from __future__ import annotations

import asyncio
import json
import re
from time import perf_counter
from typing import Any

from app.config import get_settings
from app.models.mentor import MentorIntent
from app.services.gemini_service import gemini
from app.services.knowledge_research_service import search_knowledge_sources
from app.services.market_research_service import search_market_context
from app.services.supabase_service import SupabaseService
from app.utils.ai_context import (
    DEFAULT_CONTEXT_POLICY,
    build_context_usage_trace,
    build_shared_ai_context,
)
from app.utils.content_blueprint import build_blueprint_fallback
from app.utils.helpers import (
    build_core_title,
    build_prompt_learning_context,
    get_user_context,
    normalize_text,
    normalize_topic_phrase,
    strip_accents,
)
from app.utils.mentor_logic import (
    FORBIDDEN_GENERIC_PHRASES,
    GENERIC_MARKERS,
    INTENT_RESPONSE_POLICIES,
    MAX_ANSWER_WORDS,
    MAX_FOLLOWUP_WORDS,
    MAX_STEP_WORDS,
    SKILL_CATALOG,
    TRACK_KEYWORDS,
    answer_denies_profile_access,
    build_general_guidance_followups,
    detect_mentor_intent,
    general_guidance_answer_matches_question,
    general_guidance_requirements,
    is_profile_lookup_question,
    looks_like_direct_knowledge_question,
    mentor_compare_subjects,
    mentor_focus_topic,
    mentor_question_type,
    profile_lookup_requested_fields,
    question_focus_terms,
    should_use_market_context,
    should_use_profile_context,
)
from app.utils.mentor_prompts import MENTOR_RESPONSE_PROMPT, MENTOR_RESPONSE_REWRITE_PROMPT
from app.utils.source_references import normalize_source_references, split_sources_and_related_materials


MENTOR_CAREER_PATH_TEMPLATE = {
    "role": "",
    "fit_reason": "",
    "entry_level": "",
    "required_skills": [],
    "next_step": "",
}

MENTOR_MARKET_SIGNAL_TEMPLATE = {
    "role_name": "",
    "demand_summary": "",
    "top_skills": [],
    "source_name": "",
    "source_url": "",
}

MENTOR_SKILL_GAP_TEMPLATE = {
    "skill": "",
    "gap_level": "medium",
    "why_it_matters": "",
    "suggested_action": "",
}

PROFILE_FIELD_LABELS = {
    "direction": "Định hướng hiện tại",
    "major": "Ngành học",
    "school_name": "Trường học",
    "status": "Trạng thái",
    "job_title": "Vai trò hiện tại",
    "industry": "Lĩnh vực hiện tại",
}


def _json_block(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _word_clip(text: str, max_words: int) -> str:
    words = normalize_text(text).split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(" ,;:.")


def _normalize_list_of_strings(
    raw_items: object,
    limit: int,
    *,
    clip: bool = False,
    max_words: int = MAX_STEP_WORDS,
) -> list[str]:
    if not isinstance(raw_items, list):
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        cleaned = normalize_text(str(item))
        if not cleaned:
            continue
        if clip:
            cleaned = _word_clip(cleaned, max_words)
        lowered = strip_accents(cleaned).lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(cleaned)
        if len(normalized) >= limit:
            break
    return normalized


def _normalize_items(
    raw_items: object,
    template: dict[str, Any],
    *,
    limit: int = 3,
) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list):
        return []

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue

        item: dict[str, Any] = {}
        for key, fallback in template.items():
            value = raw_item.get(key)
            if isinstance(fallback, list):
                if isinstance(value, list):
                    item[key] = _normalize_list_of_strings(value, 5, clip=False)
                elif isinstance(value, str):
                    item[key] = _normalize_list_of_strings([value], 5, clip=False)
                else:
                    item[key] = []
            elif key == "gap_level":
                cleaned = normalize_text(str(value or fallback)).lower()
                item[key] = cleaned if cleaned in {"high", "medium", "low"} else "medium"
            else:
                item[key] = normalize_text(str(value or fallback))

        anchor = normalize_text(str(item.get("role") or item.get("skill") or item.get("role_name") or ""))
        if not anchor:
            continue
        lowered = strip_accents(anchor).lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(item)
        if len(normalized) >= limit:
            break
    return normalized


def _normalize_decision_summary(summary: object) -> dict[str, str]:
    raw = summary if isinstance(summary, dict) else {}
    return {
        "headline": normalize_text(str(raw.get("headline") or "")),
        "priority_label": normalize_text(str(raw.get("priority_label") or "")),
        "priority_value": normalize_text(str(raw.get("priority_value") or "")),
        "reason": normalize_text(str(raw.get("reason") or "")),
        "next_action": normalize_text(str(raw.get("next_action") or "")),
        "confidence_note": normalize_text(str(raw.get("confidence_note") or "")),
    }


def _normalize_memory_updates(raw_items: object) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list):
        return []

    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        memory_type = normalize_text(str(item.get("memory_type") or "")).lower()
        memory_key = normalize_text(str(item.get("memory_key") or "")).lower()
        if not memory_type or not memory_key:
            continue
        signature = (memory_type, memory_key)
        if signature in seen:
            continue
        seen.add(signature)
        try:
            confidence = float(item.get("confidence", 0.8))
        except (TypeError, ValueError):
            confidence = 0.8
        normalized.append(
            {
                "memory_type": memory_type,
                "memory_key": memory_key,
                "memory_value": item.get("memory_value"),
                "confidence": max(0.0, min(1.0, confidence)),
            }
        )
        if len(normalized) >= 4:
            break
    return normalized


def _track_from_text(*values: object) -> str:
    haystack = strip_accents(" ".join(normalize_text(str(value)) for value in values if value)).lower()
    scores: dict[str, int] = {}
    for keyword, track in TRACK_KEYWORDS.items():
        if strip_accents(keyword).lower() in haystack:
            scores[track] = scores.get(track, 0) + 1
    if not scores:
        return "general"
    return max(scores.items(), key=lambda item: item[1])[0]


def _target_role(onboarding: dict[str, Any] | None, profile: dict[str, Any] | None = None) -> str:
    return normalize_text(
        str(
            (onboarding or {}).get("target_role")
            or (onboarding or {}).get("job_title")
            or (profile or {}).get("target_role")
            or (profile or {}).get("job_title")
            or ""
        )
    )


def _skill_catalog_for_context(
    onboarding: dict[str, Any] | None,
    profile: dict[str, Any] | None,
    message: str = "",
) -> list[str]:
    track = _track_from_text(
        message,
        _target_role(onboarding, profile),
        (onboarding or {}).get("current_focus"),
        (onboarding or {}).get("major"),
        (onboarding or {}).get("industry"),
    )
    return list(SKILL_CATALOG.get(track, SKILL_CATALOG["general"]))


def _extract_top_skills(
    *texts: object,
    track: str = "general",
    limit: int = 4,
) -> list[str]:
    haystack = strip_accents(" ".join(normalize_text(str(text)) for text in texts if text)).lower()
    ordered_catalog = list(SKILL_CATALOG.get(track, [])) + list(SKILL_CATALOG["general"])
    result: list[str] = []
    for skill in ordered_catalog:
        lowered = strip_accents(skill).lower()
        if lowered in haystack and skill not in result:
            result.append(skill)
        if len(result) >= limit:
            return result
    for skill in ordered_catalog:
        if skill not in result:
            result.append(skill)
        if len(result) >= limit:
            return result
    return result[:limit]


def _profile_value_from_onboarding(
    onboarding: dict[str, Any] | None,
    profile: dict[str, Any] | None,
    field: str,
) -> str:
    for source in (onboarding or {}, profile or {}):
        value = source.get(field)
        if isinstance(value, list):
            cleaned = ", ".join(normalize_text(str(item)) for item in value if normalize_text(str(item)))
        else:
            cleaned = normalize_text(str(value or ""))
        if cleaned:
            return cleaned
    return ""


def _career_path_from_target_role(
    target_role: str,
    onboarding: dict[str, Any] | None,
    profile: dict[str, Any] | None,
    message: str,
) -> dict[str, Any]:
    role = target_role or normalize_topic_phrase(message) or "Vai trò mục tiêu"
    track = _track_from_text(role, (onboarding or {}).get("current_focus"), message)
    status = strip_accents(normalize_text(str((onboarding or {}).get("status") or ""))).lower()
    entry_level = "Junior"
    if any(marker in status for marker in ("sinh vien", "student", "intern", "thuc tap")):
        entry_level = "Intern / Junior"
    return {
        "role": role,
        "fit_reason": normalize_text(
            f"Hướng này hợp nhất khi mục tiêu hiện tại xoay quanh {role} và cần đầu ra học tập có thể kiểm chứng sớm."
        ),
        "entry_level": entry_level,
        "required_skills": _extract_top_skills(role, (onboarding or {}).get("current_focus"), track=track),
        "next_step": normalize_text(
            f"Chốt 1 đầu ra nhỏ bám {role}, rồi làm xong trong 7 ngày thay vì học dàn trải."
        ),
    }


def _normalize_market_signals_from_research(
    web_research: list[dict[str, Any]] | None,
    onboarding: dict[str, Any] | None,
    profile: dict[str, Any] | None,
    message: str,
) -> list[dict[str, Any]]:
    track = _track_from_text(_target_role(onboarding, profile), message, (onboarding or {}).get("current_focus"))
    target_role = _target_role(onboarding, profile) or normalize_topic_phrase(message) or "Vai trò mục tiêu"
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in web_research or []:
        if not isinstance(item, dict):
            continue
        url = normalize_text(str(item.get("url") or item.get("source_url") or ""))
        if not url or url in seen:
            continue
        seen.add(url)
        title = normalize_text(str(item.get("title") or item.get("label") or target_role))
        snippet = normalize_text(str(item.get("snippet") or item.get("demand_summary") or ""))
        source_name = normalize_text(str(item.get("source_name") or item.get("label") or "Nguồn tham khảo"))
        normalized.append(
            {
                "role_name": target_role,
                "demand_summary": snippet or title,
                "top_skills": _extract_top_skills(title, snippet, track=track, limit=4),
                "source_name": source_name,
                "source_url": url,
            }
        )
        if len(normalized) >= 3:
            break
    return normalized


def _build_skill_gaps(
    onboarding: dict[str, Any] | None,
    profile: dict[str, Any] | None,
    message: str,
    market_signals: list[dict[str, Any]] | None = None,
    *,
    limit: int = 3,
) -> list[dict[str, Any]]:
    target_role = _target_role(onboarding, profile) or normalize_topic_phrase(message) or "mục tiêu hiện tại"
    current_focus = strip_accents(normalize_text(str((onboarding or {}).get("current_focus") or ""))).lower()
    ordered_skills: list[str] = []
    for signal in market_signals or []:
        for skill in signal.get("top_skills") or []:
            cleaned = normalize_text(str(skill))
            if cleaned and cleaned not in ordered_skills:
                ordered_skills.append(cleaned)
    for skill in _skill_catalog_for_context(onboarding, profile, message):
        if skill not in ordered_skills:
            ordered_skills.append(skill)

    gaps: list[dict[str, Any]] = []
    for index, skill in enumerate(ordered_skills):
        lowered = strip_accents(skill).lower()
        if lowered and lowered in current_focus:
            continue
        gaps.append(
            {
                "skill": skill,
                "gap_level": "high" if index < 2 else "medium",
                "why_it_matters": normalize_text(
                    f"{skill} là trục kỹ năng dễ xuất hiện khi tiến gần tới {target_role}, nên thiếu nó sẽ làm đầu ra học tập rời rạc."
                ),
                "suggested_action": normalize_text(
                    f"Dành 1 phiên ngắn để học đúng 1 phần cốt lõi của {skill} rồi gắn ngay vào một bài tập nhỏ."
                ),
            }
        )
        if len(gaps) >= limit:
            break
    return gaps


def _build_thread_title(message: str) -> str:
    title = build_core_title(message, "Phiên mentor mới")
    return normalize_text(title or "Phiên mentor mới")


def build_thread_title(message: str) -> str:
    return _build_thread_title(message)


def _build_profile_lookup_answer(
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    message: str,
) -> dict[str, Any]:
    requested_fields = profile_lookup_requested_fields(message)
    if not requested_fields:
        requested_fields = ["direction", "major", "school_name"]

    available_parts: list[str] = []
    missing_parts: list[str] = []
    for field in requested_fields:
        label = PROFILE_FIELD_LABELS.get(field, field)
        value = _profile_value_from_onboarding(onboarding, profile, field)
        if value:
            available_parts.append(f"{label}: {value}.")
        else:
            missing_parts.append(f"Hồ sơ hiện tại chưa có {label.lower()}.")

    if available_parts:
        answer = "Theo hồ sơ hiện tại, " + " ".join(available_parts + missing_parts)
    else:
        answer = "Hồ sơ hiện tại chưa có đủ thông tin cho câu hỏi này. " + " ".join(missing_parts)

    return {
        "answer": normalize_text(answer),
        "career_paths": [],
        "market_signals": [],
        "skill_gaps": [],
        "recommended_learning_steps": [],
        "suggested_followups": [
            "Bạn muốn tôi nối các dữ kiện đang có trong hồ sơ thành một bức tranh học tập ngắn gọn không?",
            "Bạn muốn biết hồ sơ hiện tại đang nghiêng về hướng nghề nào nhất?",
        ],
        "sources": [],
        "memory_updates": [],
    }


def _build_knowledge_answer_from_blueprint(
    message: str,
    onboarding: dict[str, Any] | None,
) -> dict[str, Any]:
    focus_topic = mentor_focus_topic(message)
    compare_subjects = mentor_compare_subjects(message)
    question_type = mentor_question_type(message)
    blueprint = build_blueprint_fallback(
        title=focus_topic,
        question_type=question_type if question_type != "general" else "concept",
        learner_context=build_prompt_learning_context(get_user_context(onboarding)),
        comparison_targets=list(compare_subjects or ()),
    )

    if compare_subjects:
        first, second = compare_subjects
        answer = normalize_text(
            f"{first} và {second} khác nhau ở bài toán chính, đầu ra và loại bằng chứng dùng để ra quyết định. "
            f"{first} thường nghiêng về việc làm rõ requirement, phạm vi hoặc luồng xử lý; còn {second} nghiêng về việc đọc tín hiệu, dữ liệu hoặc kết quả để rút ra insight. "
            "Vì vậy không nên đồng nhất hai vai trò chỉ vì chúng cùng đứng gần một sản phẩm hay quy trình."
        )
    elif question_type == "mechanism":
        answer = normalize_text(
            f"{blueprint['core_definition']} {blueprint['mechanism']} {blueprint['conditions_and_limits']}"
        )
    else:
        answer = normalize_text(
            f"{blueprint['core_definition']} {blueprint['scope_boundary']} {blueprint['example']}"
        )

    return {
        "answer": _word_clip(answer, MAX_ANSWER_WORDS),
        "career_paths": [],
        "market_signals": [],
        "skill_gaps": [],
        "recommended_learning_steps": [],
        "suggested_followups": _normalize_list_of_strings(
            build_general_guidance_followups(message, focus_topic, compare_subjects),
            3,
            clip=True,
            max_words=MAX_FOLLOWUP_WORDS,
        ),
        "sources": [],
        "memory_updates": [],
    }


def _build_market_outlook_answer(
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    message: str,
    market_signals: list[dict[str, Any]] | None,
    web_research: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    normalized_signals = _normalize_market_signals_from_research(web_research, onboarding, profile, message)
    if market_signals:
        normalized_signals = _normalize_items(market_signals, MENTOR_MARKET_SIGNAL_TEMPLATE, limit=3) or normalized_signals

    target_role = _target_role(onboarding, profile) or normalize_topic_phrase(message) or "vai trò này"
    top_skills = _extract_top_skills(
        target_role,
        " ".join(" ".join(signal.get("top_skills") or []) for signal in normalized_signals),
        track=_track_from_text(target_role, message),
    )
    answer = normalize_text(
        f"Thị trường cho {target_role} hiện tại vẫn xoay mạnh quanh các kỹ năng xuất hiện lặp lại trong JD như {', '.join(top_skills[:3])}. "
        "Điểm cần chốt trước không phải học thật nhiều, mà là bám đúng 1 trục kỹ năng mà nhà tuyển dụng nhắc lặp lại và gắn nó vào đầu ra thực hành nhỏ."
    )
    steps = [
        normalize_text(f"Đọc 5 JD gần {target_role} và ghi lại 3 nhóm kỹ năng lặp lại nhiều nhất."),
        normalize_text(f"Chọn 1 nhóm kỹ năng trong số đó và làm 1 đầu ra nhỏ để kiểm chứng mức độ phù hợp."),
    ]
    sources = normalize_source_references(
        [
            {
                "label": signal["source_name"],
                "url": signal["source_url"],
                "snippet": signal["demand_summary"],
            }
            for signal in normalized_signals
        ]
    )
    return {
        "answer": answer,
        "career_paths": [],
        "market_signals": normalized_signals,
        "skill_gaps": [],
        "recommended_learning_steps": steps,
        "suggested_followups": [
            f"JD cho {target_role} đang nhắc kỹ năng nào nhiều nhất?",
            f"Nếu chỉ học 1 thứ trước để bám thị trường {target_role}, nên chọn gì?",
            f"Làm sao đọc JD của {target_role} mà không bị học lan man?",
        ],
        "sources": sources,
        "memory_updates": [],
    }


def _build_learning_roadmap_answer(
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    message: str,
    market_signals: list[dict[str, Any]] | None,
    web_research: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    target_role = _target_role(onboarding, profile) or normalize_topic_phrase(message) or "mục tiêu hiện tại"
    normalized_signals = _normalize_market_signals_from_research(web_research, onboarding, profile, message)
    top_skills = _extract_top_skills(
        target_role,
        " ".join(" ".join(signal.get("top_skills") or []) for signal in normalized_signals),
        track=_track_from_text(target_role, message),
        limit=5,
    )
    steps = [
        normalize_text(f"Bước 1: chốt nền tảng {top_skills[0]} và {top_skills[1]} bằng bài tập ngắn có đầu ra rõ."),
        normalize_text(f"Bước 2: gắn {top_skills[2]} vào một bài toán gần {target_role} để hiểu cách dùng trong ngữ cảnh thật."),
        normalize_text(f"Bước 3: hoàn thành 1 mini project nhỏ rồi tự giải thích vì sao đầu ra đó chứng minh bạn đang tiến gần {target_role}."),
    ]
    answer = normalize_text(
        f"Roadmap hợp lý nhất là đi theo thứ tự từ nền tảng sang đầu ra thực hành gần {target_role}. "
        f"{steps[0]} {steps[1]} {steps[2]}"
    )
    sources = normalize_source_references(
        [
            {
                "label": signal["source_name"],
                "url": signal["source_url"],
                "snippet": signal["demand_summary"],
            }
            for signal in normalized_signals
        ]
    )
    return {
        "answer": answer,
        "career_paths": [_career_path_from_target_role(target_role, onboarding, profile, message)],
        "market_signals": normalized_signals,
        "skill_gaps": _build_skill_gaps(onboarding, profile, message, normalized_signals),
        "recommended_learning_steps": steps,
        "suggested_followups": [
            f"Nếu chỉ có ít thời gian, trong roadmap {target_role} nên cắt phần nào trước?",
            f"Sau bước 1 của roadmap {target_role}, đầu ra nào đủ để tự kiểm chứng?",
            f"Làm sao tránh học dàn trải khi theo roadmap {target_role}?",
        ],
        "sources": sources,
        "memory_updates": [],
    }


def _build_career_fit_result(
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    message: str,
    market_signals: list[dict[str, Any]] | None,
    web_research: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    target_role = _target_role(onboarding, profile) or "Vai trò hiện tại"
    normalized_signals = _normalize_market_signals_from_research(web_research, onboarding, profile, message)
    career_path = _career_path_from_target_role(target_role, onboarding, profile, message)
    skill_gaps = _build_skill_gaps(onboarding, profile, message, normalized_signals)
    answer = normalize_text(
        f"Có, {target_role} đang là hướng phù hợp nhất nếu bạn muốn một trục học tập rõ và có thể kiểm chứng bằng đầu ra sớm. "
        f"Lý do chính là hướng này bám trực tiếp vào mục tiêu hiện tại thay vì mở ra quá nhiều lựa chọn ngang nhau; việc cần làm ngay là {career_path['next_step'].lower()}"
    )
    return {
        "answer": answer,
        "career_paths": [career_path],
        "market_signals": normalized_signals[:2],
        "skill_gaps": skill_gaps,
        "recommended_learning_steps": _normalize_list_of_strings(
            [gap["suggested_action"] for gap in skill_gaps],
            3,
            clip=True,
            max_words=MAX_STEP_WORDS,
        ),
        "suggested_followups": [
            f"Để kiểm chứng mình hợp {target_role}, nên làm thử đầu ra nào trước?",
            f"Trong hồ sơ hiện tại, điểm nào đang hỗ trợ hướng {target_role} nhiều nhất?",
            f"Nếu chưa đủ mạnh cho {target_role}, nên bù kỹ năng nào trước?",
        ],
        "sources": normalize_source_references(
            [
                {
                    "label": signal["source_name"],
                    "url": signal["source_url"],
                    "snippet": signal["demand_summary"],
                }
                for signal in normalized_signals
            ]
        ),
        "memory_updates": [],
    }


def _build_skill_gap_result(
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    message: str,
    market_signals: list[dict[str, Any]] | None,
    web_research: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    normalized_signals = _normalize_market_signals_from_research(web_research, onboarding, profile, message)
    skill_gaps = _build_skill_gaps(onboarding, profile, message, normalized_signals)
    target_role = _target_role(onboarding, profile) or normalize_topic_phrase(message) or "mục tiêu hiện tại"
    answer = normalize_text(
        f"Ba khoảng trống kỹ năng cần ưu tiên trước cho {target_role} là {', '.join(gap['skill'] for gap in skill_gaps[:3])}. "
        "Nên bù theo thứ tự từ nền tảng trực tiếp ảnh hưởng đến đầu ra gần nhất, rồi mới mở rộng sang kỹ năng hỗ trợ."
    )
    return {
        "answer": answer,
        "career_paths": [_career_path_from_target_role(target_role, onboarding, profile, message)],
        "market_signals": normalized_signals[:2],
        "skill_gaps": skill_gaps,
        "recommended_learning_steps": _normalize_list_of_strings(
            [gap["suggested_action"] for gap in skill_gaps],
            3,
            clip=True,
            max_words=MAX_STEP_WORDS,
        ),
        "suggested_followups": [
            f"Với {target_role}, kỹ năng nào nên học trước để có đầu ra nhanh nhất?",
            "Làm sao tự biết một skill gap đã được bù đủ mức tối thiểu?",
            "Nên dùng mini project nào để kiểm chứng 3 skill gap này?",
        ],
        "sources": normalize_source_references(
            [
                {
                    "label": signal["source_name"],
                    "url": signal["source_url"],
                    "snippet": signal["demand_summary"],
                }
                for signal in normalized_signals
            ]
        ),
        "memory_updates": [],
    }


def _build_career_roles_result(
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    message: str,
) -> dict[str, Any]:
    target_role = _target_role(onboarding, profile)
    track = _track_from_text(target_role, (onboarding or {}).get("current_focus"), message)
    catalog = {
        "business": ["Business Analyst", "Business Systems Analyst", "Product Analyst"],
        "data": ["Data Analyst", "BI Analyst", "Product Analyst"],
        "dev": ["Backend Developer", "Frontend Developer", "Fullstack Developer"],
        "marketing": ["Performance Marketing", "Content Marketing", "SEO Specialist"],
        "product": ["Product Analyst", "Product Owner", "Product Manager"],
        "general": [target_role or "Vai trò mục tiêu", "Chuyên viên phân tích", "Chuyên viên vận hành"],
    }
    roles = catalog.get(track, catalog["general"])
    career_paths = [
        _career_path_from_target_role(role, onboarding, profile, message)
        for role in roles[:3]
    ]
    answer = normalize_text(
        f"Nếu bám đúng tín hiệu hiện tại, ba vai trò gần nhất để cân nhắc là {', '.join(path['role'] for path in career_paths)}. "
        f"Hướng nên ưu tiên trước là {career_paths[0]['role']} vì nó là điểm giao tự nhiên nhất giữa mục tiêu hiện tại và đầu ra bạn có thể làm sớm."
    )
    return {
        "answer": answer,
        "career_paths": career_paths,
        "market_signals": [],
        "skill_gaps": _build_skill_gaps(onboarding, profile, message),
        "recommended_learning_steps": [
            career_paths[0]["next_step"],
            "Đọc JD của 2 vai trò còn lại chỉ để so ranh giới, không mở thêm roadmap mới.",
        ],
        "suggested_followups": [
            f"Sự khác nhau cốt lõi giữa {career_paths[0]['role']} và {career_paths[1]['role']} là gì?",
            f"Nếu chọn {career_paths[0]['role']}, 30 ngày đầu nên chứng minh điều gì?",
            "Đọc JD thế nào để phân biệt vai trò gần nhau mà không bị nhầm tên gọi?",
        ],
        "sources": [],
        "memory_updates": [],
    }


def _build_result_by_intent(
    *,
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    intent: MentorIntent,
    message: str,
    market_signals: list[dict[str, Any]] | None,
    web_research: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    if is_profile_lookup_question(message):
        return _build_profile_lookup_answer(profile, onboarding, message)
    if intent == "market_outlook":
        return _build_market_outlook_answer(profile, onboarding, message, market_signals, web_research)
    if intent == "learning_roadmap":
        return _build_learning_roadmap_answer(profile, onboarding, message, market_signals, web_research)
    if intent == "career_fit":
        return _build_career_fit_result(profile, onboarding, message, market_signals, web_research)
    if intent == "skill_gap":
        return _build_skill_gap_result(profile, onboarding, message, market_signals, web_research)
    if intent == "career_roles":
        return _build_career_roles_result(profile, onboarding, message)
    return _build_knowledge_answer_from_blueprint(message, onboarding)


def _build_decision_summary(
    result: dict[str, Any],
    onboarding: dict[str, Any] | None,
    *,
    intent: MentorIntent = "general_guidance",
) -> dict[str, str]:
    existing = _normalize_decision_summary(result.get("decision_summary"))
    target_role = _target_role(onboarding, None) or "mục tiêu hiện tại"
    steps = _normalize_list_of_strings(result.get("recommended_learning_steps"), 3, clip=False)
    career_paths = _normalize_items(result.get("career_paths"), MENTOR_CAREER_PATH_TEMPLATE, limit=3)
    skill_gaps = _normalize_items(result.get("skill_gaps"), MENTOR_SKILL_GAP_TEMPLATE, limit=3)
    market_signals = _normalize_items(result.get("market_signals"), MENTOR_MARKET_SIGNAL_TEMPLATE, limit=3)

    headline = existing["headline"]
    priority_label = existing["priority_label"]
    priority_value = existing["priority_value"]
    reason = existing["reason"]
    next_action = existing["next_action"]
    confidence_note = existing["confidence_note"]

    if intent == "learning_roadmap":
        headline = headline or f"Roadmap hợp lý nhất là đi theo thứ tự từ nền tảng đến đầu ra gần {target_role}."
        priority_label = priority_label or "Ưu tiên hiện tại"
        priority_value = priority_value or "Roadmap 3 bước"
        reason = reason or f"Loại câu hỏi này cần thứ tự học rõ thay vì danh sách kỹ năng rời rạc cho {target_role}."
        next_action = next_action or (steps[0] if steps else "Chốt bước 1 và hoàn thành trong 7 ngày.")
    elif intent == "market_outlook":
        top_skill = market_signals[0]["top_skills"][0] if market_signals and market_signals[0].get("top_skills") else target_role
        headline = headline or f"Thị trường hiện tại đang ưu tiên tín hiệu tuyển dụng lặp lại quanh {target_role}."
        priority_label = priority_label or "Tín hiệu mạnh nhất"
        priority_value = priority_value or top_skill
        reason = reason or "Câu hỏi này cần kết luận thị trường trước, rồi mới kéo sang hành động học nếu thật sự cần."
        next_action = next_action or (steps[0] if steps else "Đọc JD gần nhất và chốt nhóm kỹ năng lặp lại.")
    elif intent in {"career_fit", "career_roles"}:
        lead_role = career_paths[0]["role"] if career_paths else target_role
        headline = headline or f"Hướng nên ưu tiên trước là {lead_role}."
        priority_label = priority_label or "Hướng ưu tiên"
        priority_value = priority_value or lead_role
        reason = reason or "Câu hỏi này cần chốt hướng trước rồi mới bàn bước tiếp theo."
        next_action = next_action or (career_paths[0]["next_step"] if career_paths else "Chốt một đầu ra thử nghiệm trong 7 ngày.")
    elif intent == "skill_gap":
        lead_gap = skill_gaps[0]["skill"] if skill_gaps else "Khoảng trống kỹ năng cốt lõi"
        headline = headline or f"Cần bù trước các khoảng trống kỹ năng đang chặn đầu ra gần nhất."
        priority_label = priority_label or "Gap ưu tiên"
        priority_value = priority_value or lead_gap
        reason = reason or f"Thiếu đúng kỹ năng nền cho {target_role} sẽ làm việc học bị dàn trải và khó tạo đầu ra."
        next_action = next_action or (steps[0] if steps else "Bù 1 gap cốt lõi bằng một bài tập nhỏ.")
    else:
        focus = priority_value or mentor_focus_topic(existing["headline"] or "")
        headline = headline or normalize_text(str(result.get("answer") or "")) or "Đây là ý chính cần giữ."
        priority_label = priority_label or "Ý chính"
        priority_value = priority_value or focus or "Khái niệm cốt lõi"
        reason = reason or "Câu hỏi này cần câu trả lời trực diện vào đúng trọng tâm đang được hỏi."
        next_action = next_action or "Đối chiếu lại một ví dụ cụ thể để kiểm tra mình đã hiểu đúng ranh giới áp dụng hay chưa."

    confidence_note = confidence_note or "Đã bám dữ kiện hiện có; nếu thiếu ngữ cảnh, câu trả lời đang dùng giả định tối thiểu."
    return {
        "headline": normalize_text(headline),
        "priority_label": normalize_text(priority_label),
        "priority_value": normalize_text(priority_value),
        "reason": normalize_text(reason),
        "next_action": normalize_text(next_action),
        "confidence_note": normalize_text(confidence_note),
    }


def _prune_result_for_intent(result: dict[str, Any], intent: MentorIntent) -> dict[str, Any]:
    pruned = dict(result)
    if intent == "general_guidance":
        pruned["career_paths"] = []
        pruned["market_signals"] = []
        pruned["skill_gaps"] = []
        pruned["recommended_learning_steps"] = []
    elif intent == "market_outlook":
        pruned["career_paths"] = []
        pruned["skill_gaps"] = []
        pruned["recommended_learning_steps"] = _normalize_list_of_strings(
            pruned.get("recommended_learning_steps"),
            2,
            clip=False,
        )
    elif intent == "career_fit":
        pruned["market_signals"] = _normalize_items(pruned.get("market_signals"), MENTOR_MARKET_SIGNAL_TEMPLATE, limit=2)
    return pruned


def _align_result_to_target_role(
    result: dict[str, Any],
    onboarding: dict[str, Any] | None,
    *,
    intent: MentorIntent,
) -> dict[str, Any]:
    if intent == "general_guidance":
        return _prune_result_for_intent(result, intent)

    aligned = dict(result)
    target_role = _target_role(onboarding, None)
    if target_role and not _normalize_items(aligned.get("career_paths"), MENTOR_CAREER_PATH_TEMPLATE, limit=3):
        aligned["career_paths"] = [_career_path_from_target_role(target_role, onboarding, None, target_role)]
    if intent in {"career_fit", "skill_gap", "learning_roadmap"} and not _normalize_items(
        aligned.get("skill_gaps"),
        MENTOR_SKILL_GAP_TEMPLATE,
        limit=3,
    ):
        aligned["skill_gaps"] = _build_skill_gaps(onboarding, None, target_role or "")
    if intent in {"career_fit", "skill_gap", "learning_roadmap"} and not _normalize_list_of_strings(
        aligned.get("recommended_learning_steps"),
        3,
        clip=False,
    ):
        aligned["recommended_learning_steps"] = _normalize_list_of_strings(
            [gap["suggested_action"] for gap in aligned.get("skill_gaps") or []],
            3,
            clip=True,
            max_words=MAX_STEP_WORDS,
        )
    return _prune_result_for_intent(aligned, intent)


def _low_signal(
    answer: str,
    message: str,
    onboarding: dict[str, Any] | None,
    result: dict[str, Any],
) -> bool:
    cleaned_answer = normalize_text(answer)
    if not cleaned_answer or len(cleaned_answer.split()) < 12:
        return True

    lowered_answer = strip_accents(cleaned_answer).lower()
    if any(marker in lowered_answer for marker in GENERIC_MARKERS + FORBIDDEN_GENERIC_PHRASES):
        return True
    if is_profile_lookup_question(message) and answer_denies_profile_access(cleaned_answer):
        return True
    if looks_like_direct_knowledge_question(message) and not general_guidance_answer_matches_question(cleaned_answer, message):
        return True
    focus_terms = question_focus_terms(message)
    if focus_terms:
        focus_hits = sum(1 for term in focus_terms[:5] if term in lowered_answer)
        if focus_hits < min(2, len(focus_terms[:4])):
            return True

    headline = normalize_text(str((result.get("decision_summary") or {}).get("headline") or ""))
    if headline and any(marker in strip_accents(headline).lower() for marker in GENERIC_MARKERS):
        return True

    detected_intent = detect_mentor_intent(message)
    career_paths = _normalize_items(result.get("career_paths"), MENTOR_CAREER_PATH_TEMPLATE, limit=3)
    market_signals = _normalize_items(result.get("market_signals"), MENTOR_MARKET_SIGNAL_TEMPLATE, limit=3)
    skill_gaps = _normalize_items(result.get("skill_gaps"), MENTOR_SKILL_GAP_TEMPLATE, limit=3)
    learning_steps = _normalize_list_of_strings(result.get("recommended_learning_steps"), 3, clip=False)
    priority_value = normalize_text(str((result.get("decision_summary") or {}).get("priority_value") or ""))

    if detected_intent == "skill_gap" and (len(skill_gaps) < 2 or len(learning_steps) < 2):
        return True
    if detected_intent == "learning_roadmap":
        if len(learning_steps) < 2:
            return True
        lowered_steps = " ".join(strip_accents(step).lower() for step in learning_steps)
        if not any(marker in lowered_steps for marker in ("buoc 1", "buoc 2", "thu tu", "truoc", "sau")):
            return True
    if detected_intent == "market_outlook" and not market_signals:
        return True
    if detected_intent in {"career_fit", "career_roles"} and not career_paths:
        return True
    if detected_intent != "general_guidance" and strip_accents(priority_value).lower() in {
        "chu de hien tai",
        "khai niem cot loi",
        "y chinh",
    }:
        return True

    target_role = _target_role(onboarding, None)
    if target_role and career_paths and detected_intent != "general_guidance":
        if target_role not in " ".join(
            normalize_text(str(item.get("role") or "")) for item in career_paths
        ):
            return True
    return False


def _build_profile_digest(
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    mentor_memory: list[dict[str, Any]] | None,
    recent_messages: list[dict[str, Any]] | None,
    recent_sessions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return build_shared_ai_context(
        profile=profile,
        onboarding=onboarding,
        mentor_memory=mentor_memory,
        recent_messages=recent_messages,
        recent_sessions=recent_sessions,
    )["profile_digest"]


def _profile_context_enabled(current_question: dict[str, Any]) -> bool:
    return bool(
        current_question.get("profile_grounding_required")
        or current_question.get("use_profile_context")
    )


def _infer_answer_mode(intent: MentorIntent, message: str) -> str:
    if intent == "general_guidance" or looks_like_direct_knowledge_question(message):
        return "knowledge_first"
    return "mentor_guidance"


def _build_current_question(
    message: str,
    intent: MentorIntent,
    answer_mode: str,
    *,
    profile: dict[str, Any] | None = None,
    onboarding: dict[str, Any] | None = None,
) -> dict[str, Any]:
    focus_topic = mentor_focus_topic(message)
    normalized_message = normalize_text(message).strip(" ?")
    target_role = _target_role(onboarding, profile)
    if intent != "general_guidance" and target_role:
        if not focus_topic or strip_accents(focus_topic).lower() == strip_accents(normalized_message).lower():
            focus_topic = target_role
    question_type = mentor_question_type(message)
    compare_subjects = mentor_compare_subjects(message)
    profile_grounding_required = is_profile_lookup_question(message)
    if intent == "general_guidance":
        primary_goal, _, must_include = general_guidance_requirements(message)
    else:
        primary_goal = INTENT_RESPONSE_POLICIES[intent]["primary_goal"]
        must_include = list(INTENT_RESPONSE_POLICIES[intent]["must_include"])

    return {
        "main_request": normalize_text(message),
        "question_type": question_type,
        "focus_topic": focus_topic,
        "must_answer": must_include,
        "primary_goal": primary_goal,
        "compare_subjects": list(compare_subjects or ()),
        "use_profile_context": should_use_profile_context(intent, message) or profile_grounding_required,
        "use_market_context": should_use_market_context(intent),
        "profile_grounding_required": profile_grounding_required,
        "answer_mode": answer_mode,
        "context_mode": answer_mode,
    }


def _build_response_contract(intent: MentorIntent, message: str) -> dict[str, Any]:
    policy = dict(INTENT_RESPONSE_POLICIES[intent])
    if intent == "general_guidance":
        primary_goal, answer_style, must_include = general_guidance_requirements(message)
        policy["primary_goal"] = primary_goal
        policy["answer_style"] = answer_style
        policy["must_include"] = must_include
    policy["max_answer_words"] = MAX_ANSWER_WORDS
    policy["max_steps"] = 3
    policy["max_followups"] = 3
    return policy


def _build_market_brief(
    *,
    message: str,
    current_question: dict[str, Any],
    market_signals: list[dict[str, Any]],
    knowledge_sources: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "focus_topic": current_question["focus_topic"],
        "research_path": {
            "market": bool(market_signals),
            "knowledge": bool(knowledge_sources),
        },
        "market_signals": market_signals,
        "knowledge_sources": knowledge_sources,
        "message_anchor": normalize_text(message),
    }


def _should_lookup_knowledge(intent: MentorIntent, message: str, current_question: dict[str, Any]) -> bool:
    lowered = strip_accents(normalize_text(message)).lower()
    if any(marker in lowered for marker in ("nguon", "bang chung", "source", "tai lieu", "theo nghien cuu")):
        return True
    if current_question["question_type"] in {"definition", "mechanism", "comparison"}:
        return True
    return intent == "general_guidance"


def _sanitize_mentor_result(
    raw_result: object,
    *,
    intent: MentorIntent,
    message: str,
    onboarding: dict[str, Any] | None,
    allowed_sources: list[dict[str, str]],
) -> dict[str, Any]:
    raw = raw_result if isinstance(raw_result, dict) else {}
    allowed_by_url = {item["url"]: item for item in allowed_sources if item.get("url")}
    requested_sources = normalize_source_references(raw.get("sources"))
    actual_sources = [allowed_by_url[item["url"]] for item in requested_sources if item["url"] in allowed_by_url]
    actual_sources, related_materials = split_sources_and_related_materials(
        allowed_sources,
        selected_urls=[item.get("url", "") for item in actual_sources],
    )

    result = {
        "answer": _word_clip(str(raw.get("answer") or ""), MAX_ANSWER_WORDS),
        "career_paths": _normalize_items(raw.get("career_paths"), MENTOR_CAREER_PATH_TEMPLATE, limit=3),
        "market_signals": _normalize_items(raw.get("market_signals"), MENTOR_MARKET_SIGNAL_TEMPLATE, limit=3),
        "skill_gaps": _normalize_items(raw.get("skill_gaps"), MENTOR_SKILL_GAP_TEMPLATE, limit=3),
        "decision_summary": _normalize_decision_summary(raw.get("decision_summary")),
        "recommended_learning_steps": _normalize_list_of_strings(raw.get("recommended_learning_steps"), 3, clip=True),
        "suggested_followups": _normalize_list_of_strings(
            raw.get("suggested_followups"),
            3,
            clip=True,
            max_words=MAX_FOLLOWUP_WORDS,
        ),
        "sources": actual_sources,
        "related_materials": related_materials,
        "memory_updates": _normalize_memory_updates(raw.get("memory_updates")),
    }
    result = _align_result_to_target_role(result, onboarding, intent=intent)
    result["decision_summary"] = _build_decision_summary(result, onboarding, intent=intent)
    if not result["answer"]:
        fallback = _build_result_by_intent(
            profile=None,
            onboarding=onboarding,
            intent=intent,
            message=message,
            market_signals=result["market_signals"],
            web_research=result["sources"],
        )
        result["answer"] = fallback["answer"]
    if intent == "general_guidance" and not result["suggested_followups"]:
        result["suggested_followups"] = _normalize_list_of_strings(
            build_general_guidance_followups(message, mentor_focus_topic(message), mentor_compare_subjects(message)),
            3,
            clip=True,
            max_words=MAX_FOLLOWUP_WORDS,
        )
    return result


def build_personalized_fallback(
    *,
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    intent: MentorIntent,
    message: str,
    market_signals: list[dict[str, Any]] | None = None,
    web_research: list[dict[str, Any]] | None = None,
    recent_messages: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    answer_mode = _infer_answer_mode(intent, message)
    current_question = _build_current_question(
        message,
        intent,
        answer_mode,
        profile=profile,
        onboarding=onboarding,
    )
    active_profile = profile if _profile_context_enabled(current_question) else None
    active_onboarding = onboarding if _profile_context_enabled(current_question) else None
    context_bundle = build_shared_ai_context(
        profile=active_profile,
        onboarding=active_onboarding,
        mentor_memory=[],
        recent_messages=recent_messages,
        recent_sessions=[],
    )
    base = _build_result_by_intent(
        profile=active_profile,
        onboarding=active_onboarding,
        intent=intent,
        message=message,
        market_signals=market_signals,
        web_research=web_research,
    )
    evidence_sources, related_materials = split_sources_and_related_materials(base.get("sources") or [])
    base["sources"] = evidence_sources
    base["related_materials"] = related_materials
    base = _align_result_to_target_role(base, active_onboarding, intent=intent)
    base["decision_summary"] = _build_decision_summary(base, active_onboarding, intent=intent)
    base["intent"] = intent
    base["answer_mode"] = answer_mode
    context_usage = build_context_usage_trace(
        learner_context=context_bundle["learner_context"],
        rendered_texts=[
            str(base.get("answer") or ""),
            str((base.get("decision_summary") or {}).get("reason") or ""),
            " ".join(str(item) for item in base.get("recommended_learning_steps") or []),
        ],
    )
    base["request_payload"] = {
        "message": message,
        "normalized_message": normalize_text(message),
        "intent": intent,
        "answer_mode": answer_mode,
        "context_policy": DEFAULT_CONTEXT_POLICY,
        "current_question": current_question,
        "related_materials": related_materials,
    }
    base["context_snapshot"] = {
        "profile_digest": context_bundle["profile_digest"],
        "learner_context": context_bundle["learner_context"],
        "context_policy": DEFAULT_CONTEXT_POLICY,
        "current_question": current_question,
    }
    base["generation_trace"] = {
        "detected_intent": intent,
        "focus_topic": current_question["focus_topic"],
        "question_type": current_question["question_type"],
        "profile_digest_used": {
            "profile": base["context_snapshot"]["profile_digest"].get("profile"),
            "onboarding": base["context_snapshot"]["profile_digest"].get("onboarding"),
            "mentor_memory": base["context_snapshot"]["profile_digest"].get("mentor_memory"),
            "recent_sessions": base["context_snapshot"]["profile_digest"].get("recent_sessions"),
        },
        "source_lookup_plan": {
            "use_market_context": current_question["use_market_context"],
            "use_profile_context": current_question["use_profile_context"],
            "use_knowledge_lookup": _should_lookup_knowledge(intent, message, current_question),
        },
        "context_usage": context_usage,
        "context_policy": DEFAULT_CONTEXT_POLICY,
        "chosen_sources": list(base.get("sources") or []),
        "related_materials": list(base.get("related_materials") or []),
        "rewrite_used": False,
        "fallback_used": True,
        "model_name": get_settings().GEMINI_MODEL or "gemini-2.5-flash",
        "latency_ms": 0,
    }
    return base


def _build_suggested_questions_legacy_one(
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
) -> list[str]:
    _ = (profile, onboarding)
    generic_suggestions = [
        "Giải thích thẳng chủ đề tôi hỏi, không vòng sang roadmap nếu tôi không yêu cầu.",
        "Nếu tôi hỏi một khái niệm, hãy cho tôi định nghĩa, ranh giới áp dụng và ví dụ ngắn.",
        "Khi tôi hỏi so sánh hai vai trò hoặc hai khái niệm, hãy tách theo trục khác nhau rõ ràng.",
        "Nếu thiếu dữ liệu cá nhân, cứ trả lời theo hướng tổng quát trước; chỉ dùng hồ sơ khi tôi yêu cầu.",
        "TCP 3-way handshake hoạt động thế nào và vì sao cần đủ 3 bước?",
        "Business Analyst khác Product Analyst ở đâu nếu nhìn theo bài toán, đầu ra và dữ liệu?",
        "Nếu muốn chuyển sang Data Analyst, tôi nên học gì trước trong 30 ngày tới?",
        "Thị trường hiện tại đang cần gì cho Data Analyst ngoài SQL?",
        "React re-render hoạt động thế nào và khi nào mới gây chậm thực sự?",
        "Hãy phân tích hộ tôi đoạn giải thích này xem sai ở đâu và sửa lại giúp tôi.",
        "Theo hồ sơ hiện tại của tôi, mục tiêu nghề nghiệp đang nghiêng về hướng nào nhất?",
    ]
    return _normalize_list_of_strings(generic_suggestions, 6, clip=True, max_words=18)

    target_role = _target_role(onboarding, profile)
    current_focus = normalize_text(str((onboarding or {}).get("current_focus") or ""))
    desired_outcome = normalize_text(str((onboarding or {}).get("desired_outcome") or ""))

    suggestions = [
        "Giải thích thẳng chủ đề tôi hỏi, đừng vòng sang roadmap nếu không cần.",
        "Nếu tôi hỏi một khái niệm, hãy cho tôi định nghĩa, ranh giới áp dụng và ví dụ ngắn.",
        "Khi tôi hỏi so sánh hai vai trò hoặc hai khái niệm, hãy tách theo trục khác nhau rõ ràng.",
        "Nếu dữ liệu hồ sơ hiện tại còn thiếu, hãy nói rõ giả định đang dùng rồi vẫn trả lời tiếp.",
    ]
    if target_role:
        suggestions.extend(
            [
                f"Để tiến gần {target_role}, tôi nên ưu tiên học gì trước trong 30 ngày tới?",
                f"JD cho {target_role} đang lặp lại những kỹ năng nào nhiều nhất?",
            ]
        )
    if current_focus:
        suggestions.append(f"{current_focus} vận hành ra sao và dễ bị hiểu sai ở đâu?")
    if desired_outcome:
        suggestions.append(f"Với mục tiêu {desired_outcome}, tôi nên chọn đầu ra học tập nào để tự kiểm chứng nhanh nhất?")

    return _normalize_list_of_strings(suggestions, 6, clip=True, max_words=18)


async def generate_mentor_response(
    *,
    svc: SupabaseService,
    user_id: str,
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    message: str,
    recent_messages: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    start_time = perf_counter()
    settings = get_settings()
    intent = detect_mentor_intent(message)
    answer_mode = _infer_answer_mode(intent, message)
    current_question = _build_current_question(
        message,
        intent,
        answer_mode,
        profile=profile,
        onboarding=onboarding,
    )
    active_profile = profile if _profile_context_enabled(current_question) else None
    active_onboarding = onboarding if _profile_context_enabled(current_question) else None

    mentor_memory: list[dict[str, Any]] = []
    if _profile_context_enabled(current_question):
        try:
            mentor_memory = svc.get_mentor_memory(user_id, limit=12)
        except Exception:
            mentor_memory = []

    try:
        recent_sessions = svc.get_recent_learning_context(user_id, limit=5)
    except Exception:
        recent_sessions = []

    context_bundle = build_shared_ai_context(
        profile=active_profile,
        onboarding=active_onboarding,
        mentor_memory=mentor_memory,
        recent_messages=recent_messages,
        recent_sessions=recent_sessions,
    )
    profile_digest = context_bundle["profile_digest"]
    knowledge_sources: list[dict[str, str]] = []
    market_signals: list[dict[str, Any]] = []
    lookup_failures: list[str] = []

    tasks: list[tuple[str, asyncio.Task[Any]]] = []
    if current_question["use_market_context"]:
        tasks.append(("market", asyncio.create_task(search_market_context(message, active_onboarding, intent))))
    if _should_lookup_knowledge(intent, message, current_question):
        tasks.append(
            (
                "knowledge",
                asyncio.create_task(
                    search_knowledge_sources(
                        message=message,
                        focus_topic=current_question["focus_topic"],
                        evidence_targets=current_question["must_answer"],
                        limit=7,
                    )
                ),
            )
        )

    for task_name, task in tasks:
        try:
            result = await task
        except Exception as exc:
            lookup_failures.append(f"{task_name}:{exc}")
            continue
        if task_name == "market":
            market_signals = _normalize_market_signals_from_research(result, active_onboarding, active_profile, message)
        else:
            knowledge_sources = normalize_source_references(result)

    allowed_sources = normalize_source_references(
        knowledge_sources
        + [
            {
                "label": signal.get("source_name") or "Nguồn tham khảo",
                "url": signal.get("source_url") or "",
                "snippet": signal.get("demand_summary") or "",
            }
            for signal in market_signals
        ]
    )

    prompt = MENTOR_RESPONSE_PROMPT.format(
        profile_brief_json=_json_block(profile_digest),
        current_question_json=_json_block(current_question),
        market_brief_json=_json_block(
            _build_market_brief(
                message=message,
                current_question=current_question,
                market_signals=market_signals,
                knowledge_sources=knowledge_sources,
            )
        ),
        response_contract_json=_json_block(_build_response_contract(intent, message)),
    )

    fallback_result = build_personalized_fallback(
        profile=active_profile,
        onboarding=active_onboarding,
        intent=intent,
        message=message,
        market_signals=market_signals,
        web_research=allowed_sources,
        recent_messages=recent_messages,
    )

    rewrite_used = False
    fallback_used = False
    try:
        ai_result = await gemini.generate_json(prompt)
    except Exception as exc:
        print(f"[mentor] Initial generation failed: {exc}")
        ai_result = {}

    result = _sanitize_mentor_result(
        ai_result,
        intent=intent,
        message=message,
        onboarding=active_onboarding,
        allowed_sources=allowed_sources,
    )

    if _low_signal(result["answer"], message, active_onboarding, result):
        rewrite_used = True
        rewrite_prompt = MENTOR_RESPONSE_REWRITE_PROMPT.format(
            profile_brief_json=_json_block(profile_digest),
            current_question_json=_json_block(current_question),
            market_brief_json=_json_block(
                _build_market_brief(
                    message=message,
                    current_question=current_question,
                    market_signals=market_signals,
                    knowledge_sources=knowledge_sources,
                )
            ),
            response_contract_json=_json_block(_build_response_contract(intent, message)),
            draft_answer=_json_block(ai_result if isinstance(ai_result, dict) else {}),
        )
        try:
            rewritten = await gemini.generate_json(rewrite_prompt)
            result = _sanitize_mentor_result(
                rewritten,
                intent=intent,
                message=message,
                onboarding=active_onboarding,
                allowed_sources=allowed_sources,
            )
        except Exception as exc:
            print(f"[mentor] Rewrite generation failed: {exc}")

    if _low_signal(result["answer"], message, active_onboarding, result):
        fallback_used = True
        result = fallback_result

    result = _align_result_to_target_role(result, active_onboarding, intent=intent)
    result["decision_summary"] = _build_decision_summary(result, active_onboarding, intent=intent)
    result["intent"] = intent
    result["answer_mode"] = answer_mode
    context_usage = build_context_usage_trace(
        learner_context=context_bundle["learner_context"],
        rendered_texts=[
            str(result.get("answer") or ""),
            str((result.get("decision_summary") or {}).get("reason") or ""),
            " ".join(str(item) for item in result.get("recommended_learning_steps") or []),
            " ".join(str(item.get("fit_reason") or "") for item in result.get("career_paths") or []),
        ],
    )
    result["request_payload"] = {
        "message": message,
        "normalized_message": normalize_text(message),
        "intent": intent,
        "answer_mode": answer_mode,
        "context_policy": DEFAULT_CONTEXT_POLICY,
        "current_question": current_question,
        "related_materials": list(result.get("related_materials") or []),
    }
    result["context_snapshot"] = {
        "profile_digest": profile_digest,
        "learner_context": context_bundle["learner_context"],
        "context_policy": DEFAULT_CONTEXT_POLICY,
        "current_question": current_question,
    }
    result["generation_trace"] = {
        "detected_intent": intent,
        "focus_topic": current_question["focus_topic"],
        "question_type": current_question["question_type"],
        "profile_digest_used": {
            "profile": profile_digest.get("profile"),
            "onboarding": profile_digest.get("onboarding"),
            "mentor_memory": profile_digest.get("mentor_memory"),
            "recent_sessions": profile_digest.get("recent_sessions"),
        },
        "source_lookup_plan": {
            "use_market_context": current_question["use_market_context"],
            "use_profile_context": current_question["use_profile_context"],
            "use_knowledge_lookup": _should_lookup_knowledge(intent, message, current_question),
        },
        "context_usage": context_usage,
        "context_policy": DEFAULT_CONTEXT_POLICY,
        "chosen_sources": list(result.get("sources") or []),
        "related_materials": list(result.get("related_materials") or []),
        "lookup_failures": lookup_failures,
        "rewrite_used": rewrite_used,
        "fallback_used": fallback_used,
        "model_name": settings.GEMINI_MODEL or "gemini-2.5-flash",
        "latency_ms": int((perf_counter() - start_time) * 1000),
    }
    return result


def _build_suggested_questions_legacy_two(
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
) -> list[str]:
    target_role = _target_role(onboarding, profile)
    current_focus = normalize_text(str((onboarding or {}).get("current_focus") or ""))
    desired_outcome = normalize_text(str((onboarding or {}).get("desired_outcome") or ""))

    suggestions = [
        "Giải thích thẳng chủ đề tôi hỏi, đừng vòng sang roadmap nếu không cần.",
        "Nếu tôi hỏi một khái niệm, hãy cho tôi định nghĩa, ranh giới áp dụng và ví dụ ngắn.",
        "Khi tôi hỏi so sánh hai vai trò hoặc hai khái niệm, hãy tách theo trục khác nhau rõ ràng.",
        "Nếu dữ liệu hồ sơ hiện tại còn thiếu, hãy nói rõ giả định đang dùng rồi vẫn trả lời tiếp.",
        "TCP 3-way handshake hoạt động thế nào và vì sao cần đủ 3 bước?",
        "Business Analyst khác Product Analyst ở đâu nếu nhìn theo bài toán, đầu ra và dữ liệu?",
    ]
    if target_role:
        suggestions.extend(
            [
                f"Để tiến gần {target_role}, tôi nên ưu tiên học gì trước trong 30 ngày tới?",
                f"JD cho {target_role} đang lặp lại những kỹ năng nào nhiều nhất?",
            ]
        )
    if current_focus:
        suggestions.append(f"{current_focus} vận hành ra sao và dễ bị hiểu sai ở đâu?")
    if desired_outcome:
        suggestions.append(
            f"Với mục tiêu {desired_outcome}, tôi nên chọn đầu ra học tập nào để tự kiểm chứng nhanh nhất?"
        )
    return _normalize_list_of_strings(suggestions, 6, clip=True, max_words=18)


def build_suggested_questions(
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
) -> list[str]:
    target_role = _target_role(onboarding, profile)
    current_focus = normalize_text(str((onboarding or {}).get("current_focus") or ""))
    desired_outcome = normalize_text(str((onboarding or {}).get("desired_outcome") or ""))

    suggestions = [
        "Giải thích thẳng chủ đề tôi hỏi, đừng vòng sang roadmap nếu không cần.",
        "Nếu tôi hỏi một khái niệm, hãy cho tôi định nghĩa, ranh giới áp dụng và ví dụ ngắn.",
        "Khi tôi hỏi so sánh hai vai trò hoặc hai khái niệm, hãy tách theo trục khác nhau rõ ràng.",
        "Nếu dữ liệu hồ sơ hiện tại còn thiếu, hãy nói rõ giả định đang dùng rồi vẫn trả lời tiếp.",
        "TCP 3-way handshake hoạt động thế nào và vì sao cần đủ 3 bước?",
        "Business Analyst khác Product Analyst ở đâu nếu nhìn theo bài toán, đầu ra và dữ liệu?",
    ]
    if target_role:
        suggestions.extend(
            [
                f"Để tiến gần {target_role}, tôi nên ưu tiên học gì trước trong 30 ngày tới?",
                f"JD cho {target_role} đang lặp lại những kỹ năng nào nhiều nhất?",
            ]
        )
    if current_focus:
        suggestions.append(f"{current_focus} vận hành ra sao và dễ bị hiểu sai ở đâu?")
    if desired_outcome:
        suggestions.append(
            f"Với mục tiêu {desired_outcome}, tôi nên chọn đầu ra học tập nào để tự kiểm chứng nhanh nhất?"
        )
    return _normalize_list_of_strings(suggestions, 6, clip=True, max_words=18)


__all__ = [
    "_align_result_to_target_role",
    "_build_decision_summary",
    "_low_signal",
    "_normalize_items",
    "_normalize_list_of_strings",
    "_prune_result_for_intent",
    "build_personalized_fallback",
    "build_suggested_questions",
    "build_thread_title",
    "detect_mentor_intent",
    "generate_mentor_response",
]

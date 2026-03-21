import asyncio
import re
from time import perf_counter
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.models.analysis import AnalyzeRequest, AnalyzeResult, Correction
from app.services.file_parser_service import extract_text_from_upload
from app.services.gemini_service import gemini
from app.services.knowledge_research_service import search_knowledge_sources
from app.services.supabase_service import SupabaseService
from app.utils.content_blueprint import (
    build_blueprint_fallback,
    build_key_points_from_briefs,
    build_section_briefs,
    build_section_content_from_blueprint,
    build_summary_from_briefs,
    is_generic_knowledge_text,
    normalize_blueprint,
    normalize_detailed_sections,
    semantic_overlap_ratio,
)
from app.utils.core_ai_prompts import (
    build_analyze_blueprint_prompt,
    build_analyze_core_prompt,
    build_analyze_query_plan_prompt,
    build_analyze_repair_prompt,
)
from app.utils.fallbacks import build_basic_mindmap
from app.utils.helpers import (
    build_core_title,
    build_input_preview,
    build_prompt_learning_context,
    build_stored_user_input,
    get_user_context,
    normalize_text,
    normalize_topic_phrase,
    normalize_topic_tags,
    strip_accents,
    truncate_content,
)
from app.utils.source_references import resolve_source_lookup


router = APIRouter()

ANALYZE_GENERIC_PHRASES = (
    "đây là một chủ đề",
    "đây là một khái niệm",
    "ở góc nhìn",
    "điều quan trọng là",
    "người học nên",
    "hãy thử",
    "phần này sẽ",
)

ANALYZE_TOPIC_STOPWORDS = {
    "la",
    "gi",
    "nhu",
    "the",
    "nao",
    "va",
    "voi",
    "cho",
    "mot",
    "nhung",
    "cua",
    "can",
    "hieu",
    "tim",
    "phan",
    "tich",
    "giai",
    "thich",
    "topic",
}

ANALYZE_GOAL_PREFIXES = (
    "cau hoi can phan tich",
    "cau hoi can kiem tra",
    "toi muon hieu",
    "toi muon kiem tra",
    "dieu toi muon hieu",
    "dieu can phan tich",
    "focus",
    "topic",
    "chu de",
)

ANALYZE_CONTENT_PREFIXES = (
    "noi dung",
    "noi dung cua toi",
    "ghi chu",
    "doan giai thich",
)

STRUCTURE_ANALYSIS_MARKERS = (
    "gom gi",
    "gom nhung gi",
    "bao gom gi",
    "bao gom nhung gi",
    "nhung phan nao",
    "phan nao",
    "thanh phan nao",
    "thanh phan chinh",
    "cau truc",
)

ANALYZE_EXPLANATORY_MARKERS = (
    " la ",
    " khong phai ",
    " khac voi ",
    " dung de ",
    " dung khi ",
    " bao gom ",
    " gom ",
    " thanh phan ",
    " vai tro ",
    " quan he ",
    " dau vao ",
    " xu ly ",
    " dau ra ",
    " vi ",
    " do ",
    " neu ",
    " khi ",
    " gioi han ",
    " nham lan ",
)

ANALYZE_MECHANISM_MARKERS = (
    " co che ",
    " logic ",
    " dau vao ",
    " xu ly ",
    " dau ra ",
    " dan den ",
    " tao ra ",
    " van hanh ",
    " vi ",
    " do ",
    " neu ",
    " khi ",
)

ANALYZE_BOUNDARY_MARKERS = (
    " khong phai ",
    " khac voi ",
    " gioi han ",
    " chi dung khi ",
    " chi co gia tri khi ",
    " khong dong nghia ",
)

SECTION_DISPLAY_TITLES = {
    "core_concept": "Khái niệm cốt lõi",
    "mechanism": "Bản chất / cơ chế hoạt động",
    "components_and_relationships": "Các thành phần chính và quan hệ giữa chúng",
    "persona_based_example": "Ví dụ trực quan",
    "real_world_applications": "Ứng dụng thực tế",
    "common_misconceptions": "Nhầm lẫn phổ biến",
    "next_step_self_study": "Điểm cần nắm tiếp",
}

SECTION_ORDER = [
    "core_concept",
    "mechanism",
    "components_and_relationships",
    "persona_based_example",
    "real_world_applications",
    "common_misconceptions",
    "next_step_self_study",
]


def _summary_bullet_count(summary: str) -> int:
    return len([line for line in summary.splitlines() if normalize_text(line.lstrip("-*• "))])


def _normalize_corrections(items: object) -> list[Correction]:
    if not isinstance(items, list):
        return []

    normalized: list[Correction] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        original = normalize_text(str(item.get("original") or ""))
        correction = normalize_text(str(item.get("correction") or ""))
        explanation = normalize_text(str(item.get("explanation") or ""))
        if not original and not correction:
            continue
        normalized.append(
            Correction(
                original=original,
                correction=correction,
                explanation=explanation,
            )
        )
    return normalized


def _extract_prefixed_value(line: str, prefixes: tuple[str, ...]) -> str | None:
    normalized_line = normalize_text(line)
    normalized_ascii = strip_accents(normalized_line).lower()
    for prefix in prefixes:
        if normalized_ascii.startswith(prefix) and ":" in normalized_line:
            return normalize_text(normalized_line.split(":", 1)[1])
    return None


def _strip_known_question_prefixes(text: str) -> str:
    cleaned = normalize_text(text)
    prefixed = _extract_prefixed_value(cleaned, ANALYZE_GOAL_PREFIXES + ANALYZE_CONTENT_PREFIXES)
    return prefixed or cleaned


def _clean_analysis_sentences(content: str) -> list[str]:
    cleaned_content = normalize_text(content)
    return [
        normalize_text(part)
        for part in re.split(r"(?<=[.!?])\s+|\n+", cleaned_content)
        if normalize_text(part)
    ]


def _normalize_multiline_text(text: object) -> str:
    if not isinstance(text, str):
        return ""
    lines = [normalize_text(line) for line in text.splitlines() if normalize_text(line)]
    return "\n".join(lines).strip()


def _extract_sentences(text: str, limit: int = 2) -> list[str]:
    return _clean_analysis_sentences(text)[:limit]


def _select_focus_sentences(content: str, focus_topic: str, limit: int = 3) -> list[str]:
    sentences = _clean_analysis_sentences(content)
    if not sentences:
        return []

    scored: list[tuple[float, str]] = []
    for sentence in sentences:
        score = _focus_overlap_ratio(sentence, focus_topic)
        if normalize_text(sentence):
            scored.append((score, sentence))

    scored.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
    selected: list[str] = []
    for score, sentence in scored:
        if score <= 0 and selected:
            continue
        if sentence not in selected:
            selected.append(sentence)
        if len(selected) >= limit:
            break

    if not selected:
        return sentences[:limit]
    return selected[:limit]


def _strip_analysis_metadata(content: str) -> str:
    cleaned_lines: list[str] = []
    for raw_line in content.splitlines():
        line = normalize_text(raw_line)
        if not line:
            continue
        stripped = _extract_prefixed_value(line, ANALYZE_GOAL_PREFIXES + ANALYZE_CONTENT_PREFIXES)
        cleaned_lines.append(stripped if stripped is not None else line)
    cleaned = "\n".join(line for line in cleaned_lines if line)
    return cleaned or normalize_text(content)


def _normalize_analysis_goal_override(analysis_goal: str | None) -> str | None:
    cleaned = normalize_text(str(analysis_goal or ""))
    return cleaned or None


def _extract_analysis_goal(content: str, analysis_goal_override: str | None = None) -> str:
    explicit_goal = _normalize_analysis_goal_override(analysis_goal_override)
    if explicit_goal:
        return explicit_goal

    lines = [normalize_text(line) for line in content.splitlines() if normalize_text(line)]
    for line in lines[:8]:
        extracted = _extract_prefixed_value(line, ANALYZE_GOAL_PREFIXES)
        if extracted:
            return extracted

    if lines:
        first_line = lines[0]
        if first_line.endswith("?") and len(first_line.split()) >= 4:
            return first_line
    return normalize_text(content)


def _legacy_extract_analysis_focus(content: str, analysis_goal: str) -> str:
    lines = [normalize_text(line) for line in content.splitlines() if normalize_text(line)]
    for line in lines[:8]:
        extracted = _extract_prefixed_value(
            line,
            ANALYZE_GOAL_PREFIXES + ("chu de can tu kiem tra", "chu de can kiem tra", "focus topic"),
        )
        if extracted:
            return normalize_topic_phrase(extracted)

    if _detect_analysis_kind(analysis_goal) in {"definition", "mechanism", "structure"}:
        compact = build_core_title(analysis_goal, "")
        if compact and not _analysis_title_needs_cleanup(compact):
            return compact
        if lines:
            first_line_title = build_core_title(lines[0], "")
            if first_line_title and not _analysis_title_needs_cleanup(first_line_title):
                return first_line_title

    focus = normalize_topic_phrase(analysis_goal)
    if focus:
        return focus

    stripped = normalize_topic_phrase(_strip_analysis_metadata(content))
    return stripped or "chủ đề chính trong nội dung"


def _validate_analysis_input(content: str, analysis_goal: str | None = None) -> str:
    normalized = normalize_text(content)
    has_explicit_goal = bool(_normalize_analysis_goal_override(analysis_goal))
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nội dung phân tích đang trống. Hãy dán câu hỏi hoặc ghi chú của bạn.",
        )
    if len(normalized) < (12 if has_explicit_goal else 20):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Nội dung quá ngắn để phân tích. Hãy ghi ít nhất 1 câu hỏi hoặc 2-3 dòng ghi chú "
                "mà bạn muốn AI kiểm tra."
            ),
        )
    if len(normalized.split()) < (3 if has_explicit_goal else 4):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nội dung chưa đủ rõ. Hãy nêu rõ mục tiêu phân tích hoặc dán đoạn ghi chú cụ thể hơn.",
        )
    return normalized


def _focus_keywords(text: str) -> list[str]:
    normalized = strip_accents(normalize_text(normalize_topic_phrase(text) or text)).lower()
    tokens = re.findall(r"[0-9a-z]+", normalized)
    result: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if len(token) < 3 or token in ANALYZE_TOPIC_STOPWORDS or token.isdigit():
            continue
        if token in seen:
            continue
        seen.add(token)
        result.append(token)
        if len(result) >= 6:
            break
    return result


def _focus_overlap_ratio(text: str, focus_topic: str) -> float:
    keywords = _focus_keywords(focus_topic)
    if not keywords:
        return 1.0
    haystack = strip_accents(normalize_text(text)).lower()
    matches = sum(1 for keyword in keywords if keyword in haystack)
    return matches / len(keywords)


def _looks_generic_analysis_text(text: str) -> bool:
    return is_generic_knowledge_text(text)


def _clip_words(text: str, max_words: int) -> str:
    words = normalize_text(text).split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(" ,;:.") + "..."


def _split_analysis_bullets(text: object) -> list[str]:
    if not isinstance(text, str):
        return []
    return [
        normalize_text(line.lstrip("-*• ").strip())
        for line in text.splitlines()
        if normalize_text(line.lstrip("-*• ").strip())
    ]


def _contains_any_marker(text: str, markers: tuple[str, ...]) -> bool:
    lowered = f" {strip_accents(normalize_text(text)).lower()} "
    return any(marker in lowered for marker in markers)


def _is_substantive_analysis_line(
    text: str,
    focus_topic: str,
    *,
    expect_role: str | None = None,
) -> bool:
    cleaned = normalize_text(text)
    if not cleaned or _contains_trailing_ellipsis(cleaned) or _looks_generic_analysis_text(cleaned):
        return False
    if len(cleaned.split()) < 8:
        return False

    if _focus_overlap_ratio(cleaned, focus_topic) >= 0.18:
        return True

    if expect_role == "mechanism":
        return _contains_any_marker(cleaned, ANALYZE_MECHANISM_MARKERS)
    if expect_role == "structure":
        return _contains_any_marker(cleaned, STRUCTURE_ANALYSIS_MARKERS + (" thanh phan ", " vai tro ", " quan he "))
    if expect_role == "boundary":
        return _contains_any_marker(cleaned, ANALYZE_BOUNDARY_MARKERS)

    return _contains_any_marker(cleaned, ANALYZE_EXPLANATORY_MARKERS)


def _analysis_summary_needs_fallback(summary: str, focus_topic: str) -> bool:
    bullets = _split_analysis_bullets(summary)
    if len(bullets) < 4:
        return True

    useful = sum(1 for bullet in bullets if _is_substantive_analysis_line(bullet, focus_topic))
    short = sum(1 for bullet in bullets if len(bullet.split()) < 8)
    overlaps = 0
    for index in range(len(bullets) - 1):
        if semantic_overlap_ratio(bullets[index], bullets[index + 1]) > 0.82:
            overlaps += 1

    return useful < 3 or short >= 2 or overlaps >= 2


def _parse_compare_subjects(goal: str) -> tuple[str, str] | None:
    normalized = _strip_known_question_prefixes(goal)
    patterns = [
        r"(.+?)\s+(?:khác|khac)\s+(.+?)\s+(?:ở|o)\s+(?:điểm|diem)\s+nào\??$",
        r"so sánh\s+(.+?)\s+và\s+(.+?)$",
        r"phan biet\s+(.+?)\s+va\s+(.+?)$",
        r"phân biệt\s+(.+?)\s+và\s+(.+?)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if not match:
            continue
        first = normalize_topic_phrase(match.group(1))
        second = normalize_topic_phrase(match.group(2))
        if first and second:
            return first, second
    return None


def _is_structure_analysis_request(goal: str) -> bool:
    lowered = strip_accents(normalize_text(goal)).lower()
    return any(marker in lowered for marker in STRUCTURE_ANALYSIS_MARKERS)


def _detect_analysis_kind(goal: str) -> str:
    lowered = strip_accents(normalize_text(goal)).lower()
    if _parse_compare_subjects(goal):
        return "comparison"
    if _is_structure_analysis_request(goal):
        return "structure"
    if "la gi" in lowered:
        return "definition"
    if "hoat dong nhu the nao" in lowered or "van hanh nhu the nao" in lowered:
        return "mechanism"
    return "review"


def _build_analysis_brief(analysis_goal: str, focus_topic: str, analysis_content: str) -> dict[str, Any]:
    compare_subjects = _parse_compare_subjects(analysis_goal)
    return {
        "analysis_kind": _detect_analysis_kind(analysis_goal),
        "focus_topic": normalize_topic_phrase(focus_topic or analysis_goal),
        "focus_keywords": _focus_keywords(focus_topic or analysis_goal),
        "compare_subjects": list(compare_subjects) if compare_subjects else [],
        "direct_question": normalize_text(_strip_known_question_prefixes(analysis_goal)),
        "focus_evidence": _select_focus_sentences(analysis_content, focus_topic, limit=3),
        "response_blocks": [
            "summary_judgment",
            "key_points_corrected_knowledge",
            "corrections_if_needed",
            "knowledge_detail_data_teaching_note",
            "references_rendered_separately",
        ],
    }


def _heuristic_analysis_plan(analysis_goal: str, focus_topic: str, analysis_content: str) -> dict[str, Any]:
    normalized_goal = normalize_text(_strip_known_question_prefixes(analysis_goal))
    normalized_focus = normalize_topic_phrase(focus_topic or analysis_goal)
    compare_subjects = _parse_compare_subjects(analysis_goal)
    evidence_targets = _select_focus_sentences(analysis_content, focus_topic, limit=3)
    must_include = [normalized_focus] if normalized_focus else []
    if compare_subjects:
        must_include.extend(compare_subjects)
    for sentence in evidence_targets:
        short_sentence = _clip_words(sentence, 12)
        if short_sentence and short_sentence not in must_include:
            must_include.append(short_sentence)

    return {
        "analysis_kind": _detect_analysis_kind(analysis_goal),
        "main_question": normalized_goal,
        "focus_topic": normalized_focus or normalized_goal,
        "comparison_targets": list(compare_subjects) if compare_subjects else [],
        "evidence_targets": evidence_targets[:4],
        "must_include": must_include[:5],
        "must_avoid": ["lang man sang chu de lien quan", "lap lai cau hoi nguoi dung"],
        "answer_strategy": "Tra loi truc dien vao cau hoi, chi dung noi dung da nop lam bang chung, sau do moi chi ra diem dung sai.",
    }


def _normalize_analysis_plan(
    raw_plan: object,
    analysis_goal: str,
    focus_topic: str,
    analysis_content: str,
) -> dict[str, Any]:
    fallback = _heuristic_analysis_plan(analysis_goal, focus_topic, analysis_content)
    if not isinstance(raw_plan, dict):
        return fallback

    analysis_kind = normalize_text(str(raw_plan.get("analysis_kind") or fallback["analysis_kind"])).lower()
    if analysis_kind not in {"definition", "comparison", "mechanism", "structure", "review"}:
        analysis_kind = fallback["analysis_kind"]

    main_question = normalize_text(str(raw_plan.get("main_question") or fallback["main_question"]))
    plan_focus_topic = normalize_topic_phrase(str(raw_plan.get("focus_topic") or fallback["focus_topic"]))

    comparison_targets_raw = raw_plan.get("comparison_targets")
    comparison_targets: list[str] = []
    if isinstance(comparison_targets_raw, list):
        for item in comparison_targets_raw[:2]:
            cleaned = normalize_topic_phrase(str(item))
            if cleaned:
                comparison_targets.append(cleaned)
    if analysis_kind == "comparison" and len(comparison_targets) < 2:
        comparison_targets = list(fallback["comparison_targets"])

    evidence_targets_raw = raw_plan.get("evidence_targets")
    evidence_targets: list[str] = []
    if isinstance(evidence_targets_raw, list):
        for item in evidence_targets_raw[:4]:
            cleaned = normalize_text(str(item))
            if cleaned:
                evidence_targets.append(cleaned)
    if not evidence_targets:
        evidence_targets = list(fallback["evidence_targets"])

    must_include_raw = raw_plan.get("must_include")
    must_include: list[str] = []
    if isinstance(must_include_raw, list):
        for item in must_include_raw[:5]:
            cleaned = normalize_topic_phrase(str(item)) or normalize_text(str(item))
            if cleaned and cleaned not in must_include:
                must_include.append(cleaned)
    for item in comparison_targets + [plan_focus_topic]:
        if item and item not in must_include:
            must_include.append(item)

    must_avoid_raw = raw_plan.get("must_avoid")
    must_avoid: list[str] = []
    if isinstance(must_avoid_raw, list):
        for item in must_avoid_raw[:4]:
            cleaned = normalize_text(str(item))
            if cleaned:
                must_avoid.append(cleaned)
    if not must_avoid:
        must_avoid = fallback["must_avoid"]

    answer_strategy = normalize_text(str(raw_plan.get("answer_strategy") or fallback["answer_strategy"]))

    return {
        "analysis_kind": analysis_kind,
        "main_question": main_question or fallback["main_question"],
        "focus_topic": plan_focus_topic or fallback["focus_topic"],
        "comparison_targets": comparison_targets,
        "evidence_targets": evidence_targets[:4],
        "must_include": must_include[:5],
        "must_avoid": must_avoid[:4],
        "answer_strategy": answer_strategy or fallback["answer_strategy"],
    }


def _should_use_llm_analysis_plan(analysis_goal: str, analysis_content: str) -> bool:
    analysis_kind = _detect_analysis_kind(analysis_goal)
    question_length = len(normalize_text(analysis_goal).split())
    content_length = len(normalize_text(analysis_content).split())
    if analysis_kind in {"definition", "comparison", "mechanism", "structure"} and question_length <= 22 and content_length <= 220:
        return False
    return True


async def _build_analysis_plan(
    analysis_goal: str,
    focus_topic: str,
    analysis_content: str,
) -> dict[str, Any]:
    fallback = _heuristic_analysis_plan(analysis_goal, focus_topic, analysis_content)
    if not _should_use_llm_analysis_plan(analysis_goal, analysis_content):
        return fallback
    try:
        raw_plan = await gemini.generate_json(
            build_analyze_query_plan_prompt(
                analysis_goal=analysis_goal,
                focus_topic=focus_topic,
                content=analysis_content,
            )
        )
    except Exception as exc:
        print(f"[analyze] Query plan generation failed, using heuristic plan: {exc}")
        return fallback
    return _normalize_analysis_plan(raw_plan, analysis_goal, focus_topic, analysis_content)


def _should_generate_analysis_blueprint(analysis_plan: dict[str, Any], analysis_content: str) -> bool:
    analysis_kind = normalize_text(str(analysis_plan.get("analysis_kind") or "")).lower()
    content_length = len(normalize_text(analysis_content).split())
    if analysis_kind in {"definition", "comparison", "mechanism", "structure"} and content_length <= 220:
        return False
    return True


def _should_lookup_analysis_sources(
    analysis_plan: dict[str, Any],
    analysis_goal: str,
    analysis_content: str,
) -> bool:
    return bool(normalize_text(analysis_goal) and normalize_text(analysis_content))


def _build_analysis_title(analysis_goal: str, focus_topic: str) -> str:
    cleaned_goal = _strip_known_question_prefixes(analysis_goal)
    cleaned_focus = _strip_known_question_prefixes(focus_topic)
    compare_subjects = _parse_compare_subjects(cleaned_goal)
    if compare_subjects:
        return f"Phân biệt {compare_subjects[0]} và {compare_subjects[1]}"
    if cleaned_focus:
        return normalize_topic_phrase(cleaned_focus).strip(" .")
    return normalize_topic_phrase(cleaned_goal).strip(" .") or "Phân tích nội dung"


def _legacy_build_compact_analysis_title(analysis_goal: str, focus_topic: str) -> str:
    cleaned_goal = _strip_known_question_prefixes(analysis_goal)
    cleaned_focus = _strip_known_question_prefixes(focus_topic)
    compare_subjects = _parse_compare_subjects(cleaned_goal)
    if compare_subjects:
        return build_core_title(f"{compare_subjects[0]} và {compare_subjects[1]}", "Phan tich noi dung")
    if cleaned_focus:
        return build_core_title(cleaned_focus, "Phan tich noi dung")
    return build_core_title(cleaned_goal, "Phan tich noi dung")

def _analysis_title_needs_cleanup(title: str) -> bool:
    normalized = normalize_text(title)
    if not normalized:
        return True

    folded = strip_accents(normalized).lower()
    if folded.startswith(("khai niem cua ", "dinh nghia cua ", "khai niem ve ", "dinh nghia ve ")):
        return True

    words = normalized.split()
    if len(words) > 8:
        return True
    if words and strip_accents(words[-1]).lower() in {
        "la",
        "cac",
        "nhung",
        "mot",
        "duoc",
        "dung",
        "de",
        "voi",
        "cua",
        "va",
        "hay",
        "hoac",
    }:
        return True
    return False


def _prefer_compact_analysis_title(current_title: str, analysis_content: str) -> str:
    normalized = normalize_text(current_title)
    if normalized and not _analysis_title_needs_cleanup(normalized):
        return normalized

    candidates = [normalized]
    sentences = _clean_analysis_sentences(analysis_content)
    topic = _prefer_compact_analysis_title(topic, analysis_content) or topic
    if sentences:
        candidates.append(sentences[0])
    candidates.append(analysis_content)

    for candidate in candidates:
        compact = build_core_title(candidate, "")
        if compact and not _analysis_title_needs_cleanup(compact):
            return compact

    return normalized or build_core_title(analysis_content, "Phan tich noi dung")


def _contains_trailing_ellipsis(text: str) -> bool:
    normalized = normalize_text(text)
    return normalized.endswith("...") or normalized.endswith("…")


def _build_example_context(learner_context: dict[str, str]) -> str:
    target_role = learner_context.get("target_role")
    current_focus = learner_context.get("current_focus")
    if target_role and current_focus:
        return (
            f"Vi du nen gan voi boi canh nguoi hoc dang huong toi {target_role} "
            f"va hien tap trung vao {current_focus}."
        )
    if target_role:
        return f"Vi du nen gan voi boi canh nguoi hoc dang huong toi {target_role}."
    return "Vi du nen ngan, doi thuong va chi dung de lam ro dung y chinh."


def _build_comparison_knowledge_sections(
    analysis_goal: str,
    focus_topic: str,
    learner_context: dict[str, str],
) -> dict[str, dict[str, str]]:
    first, second = _parse_compare_subjects(analysis_goal) or (
        normalize_topic_phrase(focus_topic) or "khai niem A",
        "khai niem B",
    )
    example_context = _build_example_context(learner_context)
    return {
        "core_concept": {
            "title": SECTION_DISPLAY_TITLES["core_concept"],
            "content": (
                f"{first} va {second} khac nhau chu yeu o muc tieu cong viec, dau ra chinh va cach ra quyet dinh. "
                f"{first} thuong dung de lam ro bai toan, yeu cau hoac quy trinh can xu ly. "
                f"{second} thuong dung de doc tin hieu, du lieu hoac ket qua quan sat de rut ra ket luan va de xuat hanh dong. "
                "Muon phan biet dung, can so tren cung mot khung thay vi chi so dinh nghia ngan."
            ),
        },
        "mechanism": {
            "title": SECTION_DISPLAY_TITLES["mechanism"],
            "content": (
                f"Co che cua {first} thuong di tu nhu cau, van de hoac stakeholder den requirement, quy trinh va dau ra can chot. "
                f"Co che cua {second} thuong di tu du lieu, hanh vi, chi so hoac ket qua quan sat den insight va de xuat quyet dinh. "
                "Khac biet nam o diem xuat phat, cach xu ly thong tin va loai ket qua cuoi cung."
            ),
        },
        "components_and_relationships": {
            "title": SECTION_DISPLAY_TITLES["components_and_relationships"],
            "content": (
                f"Khi dat {first} canh {second}, nen so tren 3 truc: muc tieu chinh, dau ra chinh va nguon thong tin thuong dung. "
                f"{first} thuong gan voi requirement, quy trinh, stakeholder va bai toan can lam ro. "
                f"{second} thuong gan voi metric, du lieu, hanh vi va ket luan rut ra tu bang chung. "
                "Khung nay giup tach ro diem giong va diem khac ma khong bi lan sang chu de ben canh."
            ),
        },
        "persona_based_example": {
            "title": SECTION_DISPLAY_TITLES["persona_based_example"],
            "content": (
                f"{example_context} Neu mot nguoi dang lam ro requirement, ve luong xu ly va thong nhat tieu chi ban giao, do nghieng ve {first}. "
                f"Neu nguoi do dang doc so lieu, tim nguyen nhan bien dong va de xuat thay doi dua tren du lieu, do nghieng ve {second}. "
                "Vi du nhu vay giup nhin ra su khac nhau bang cong viec that."
            ),
        },
        "real_world_applications": {
            "title": SECTION_DISPLAY_TITLES["real_world_applications"],
            "content": (
                f"{first} huu ich khi to chuc can lam ro bai toan, requirement, quy trinh va cach cac ben phoi hop. "
                f"{second} huu ich khi to chuc can do luong, danh gia va toi uu san pham hoac van hanh dua tren tin hieu thuc te. "
                "Trong nhieu du an, hai ben co the phoi hop chat nhung van giu trong tam kien thuc rieng."
            ),
        },
        "common_misconceptions": {
            "title": SECTION_DISPLAY_TITLES["common_misconceptions"],
            "content": (
                f"Nham lan pho bien la cho rang {first} va {second} chi khac ten goi. "
                "Thuc te, ten chuc danh co the thay doi theo cong ty, nhung van phai soi vao bai toan ho giai quyet, dau ra ho chiu trach nhiem va nguon thong tin ho dung moi ngay. "
                "Do moi la cach phan biet chac nhat."
            ),
        },
        "next_step_self_study": {
            "title": SECTION_DISPLAY_TITLES["next_step_self_study"],
            "content": (
                f"Diem can nam tiep la cach tach ro {first} va {second} trong mot tinh huong thuc te: ai lam ro van de, ai doc tin hieu va ai chiu trach nhiem cho loai dau ra nao. "
                "Khi truc nay ro, ban se bot lan hon rat nhieu."
            ),
        },
    }


def _build_definition_knowledge_sections(
    title: str,
    learner_context: dict[str, str],
) -> dict[str, dict[str, str]]:
    example_context = _build_example_context(learner_context)
    return {
        "core_concept": {
            "title": SECTION_DISPLAY_TITLES["core_concept"],
            "content": (
                f"{title} can duoc hieu la mot khai niem, vai tro, co che hoac phuong phap co pham vi ap dung cu the. "
                f"Muon tra loi dung cau hoi ve {title}, can chot 3 diem: no dung de lam gi, xuat hien trong hoan canh nao, va khac gi voi khai niem gan no nhat. "
                "Neu ba diem nay ro, phan con lai se de dinh vi hon nhieu."
            ),
        },
        "mechanism": {
            "title": SECTION_DISPLAY_TITLES["mechanism"],
            "content": (
                f"Ban chat cua {title} nam o logic van hanh: dau vao la gi, o giua xu ly dieu gi va dau ra tao ra gia tri gi. "
                "Neu chi nho mot dinh nghia ngan ma khong hieu co che, nguoi hoc rat de lung tung khi gap vi du moi hoac ngu canh khac. "
                "Vi vay, phan co che luon quan trong hon hoc thuoc tu khoa."
            ),
        },
        "components_and_relationships": {
            "title": SECTION_DISPLAY_TITLES["components_and_relationships"],
            "content": (
                f"{title} thuong gom vai thanh phan hoac vai khia canh phai nhin cung nhau. "
                "Dieu quan trong khong chi la biet ten tung phan, ma la hieu phan nao la trung tam, phan nao ho tro va chung anh huong lan nhau ra sao. "
                "Neu tach roi tung phan, nguoi hoc se de nho roi rac va kho ap dung vao tinh huong tong hop."
            ),
        },
        "persona_based_example": {
            "title": SECTION_DISPLAY_TITLES["persona_based_example"],
            "content": (
                f"{example_context} Voi {title}, mot vi du tot nen cho thay ro dau vao, cach xu ly va dau ra thay doi nhu the nao. "
                "Khi vi du sat tinh huong that, nguoi hoc se nhin thay ban chat cua khai niem thay vi chi nho mot cau dinh nghia. "
                "Do la cach bien ly thuyet thanh thu co the hinh dung va dung lai."
            ),
        },
        "real_world_applications": {
            "title": SECTION_DISPLAY_TITLES["real_world_applications"],
            "content": (
                f"Gia tri cua {title} the hien o cho no giup giai thich, danh gia hoac cai thien mot quyet dinh trong thuc te. "
                "Khi xem ung dung, nen hoi: no xuat hien o dau trong cong viec, quy trinh, he thong hoac san pham, va no giup con nguoi lam tot dieu gi. "
                "Tra loi duoc cau hoi nay thi chu de moi that su ro."
            ),
        },
        "common_misconceptions": {
            "title": SECTION_DISPLAY_TITLES["common_misconceptions"],
            "content": (
                f"Nham lan pho bien voi {title} la danh dong no voi mot khai niem nghe gan giong, hoac nho vi du ma quen dieu kien ap dung. "
                "Cach sua la quay lai dinh nghia ngan, co che cot loi va gioi han ap dung cua chu de. "
                "Ba diem nay giup tach hieu dung khoi cach nho may moc."
            ),
        },
        "next_step_self_study": {
            "title": SECTION_DISPLAY_TITLES["next_step_self_study"],
            "content": (
                f"Diem can nam tiep la ranh gioi giua dinh nghia cua {title}, co che tao ra ket qua va boi canh nao khien no phat huy gia tri. "
                "Khi ranh gioi nay ro, viec doc them vi du hoac truong hop moi se it bi lech hon."
            ),
        },
    }


def _legacy_build_analysis_knowledge_fallback(
    analysis_goal: str,
    focus_topic: str,
    learner_context: dict[str, str],
) -> dict[str, Any]:
    title = _build_compact_analysis_title(analysis_goal, focus_topic)
    kind = _detect_analysis_kind(analysis_goal)

    if kind == "comparison":
        sections = _build_comparison_knowledge_sections(analysis_goal, focus_topic, learner_context)
        first, second = _parse_compare_subjects(analysis_goal) or (title, "khai niem lien quan")
        summary_lines = [
            f"- {first} va {second} can duoc tach bang muc tieu cong viec, dau ra va nguon thong tin chinh.",
            f"- Co che cua {first} thuong di tu bai toan can lam ro, con {second} thuong di tu tin hieu hoac du lieu can phan tich.",
            f"- Vi du dung phai cho thay moi ben xuat hien trong mot nhiem vu thuc te nhu the nao.",
            "- Nham lan thuong den tu viec so ten goi ma bo qua bai toan va dau ra thuc su.",
        ]
    else:
        sections = _build_definition_knowledge_sections(title, learner_context)
        summary_lines = [
            f"- {title} can duoc hieu qua dinh nghia, pham vi ap dung va diem khac voi khai niem gan no.",
            f"- Co che cua {title} phai duoc nhin theo logic dau vao, xu ly va dau ra thay vi hoc thuoc tu khoa.",
            f"- Vi du dung chi co gia tri khi no lam ro ban chat va dieu kien ap dung cua {title}.",
            "- Nham lan pho bien thuong xay ra khi nho ket qua ma bo qua nguyen ly tao ra ket qua do.",
        ]

    return {
        "title": title,
        "summary": "\n".join(summary_lines),
        "detailed_sections": sections,
        "teaching_adaptation": {
            "focus_priority": f"Bám sát câu hỏi gốc về {title}",
            "tone": "Rõ ràng, trực diện, ưu tiên bản chất trước",
            "depth_control": "Di tu khai niem den co che, vi du va gioi han ap dung",
            "example_strategy": _build_example_context(learner_context),
        },
    }


def _build_compare_fallback(
    analysis_content: str,
    analysis_goal: str,
    focus_topic: str,
    learner_context: dict[str, str],
) -> dict[str, Any]:
    subject_a, subject_b = _parse_compare_subjects(analysis_goal) or (focus_topic, "khái niệm còn lại")
    sentences = _clean_analysis_sentences(analysis_content)
    evidence_line = normalize_text(sentences[0]) if sentences else ""
    extra_line = normalize_text(sentences[1]) if len(sentences) > 1 else ""

    summary_bullets = [
        f"Câu hỏi đang yêu cầu phân biệt {subject_a} và {subject_b}, nên trọng tâm phải là vai trò, đầu ra và cách làm việc của từng bên.",
        f"Ghi chú hiện tại đã chạm đúng hướng: {evidence_line}" if evidence_line else f"Ghi chú hiện tại mới cho thấy một phần khác biệt giữa {subject_a} và {subject_b}.",
        f"Phần còn thiếu là so sánh rõ theo 3 trục: mục tiêu công việc, loại đầu ra và công cụ/nguồn dữ liệu thường dùng.",
        f"Nếu muốn kiểm chứng chắc hơn, hãy bổ sung một ví dụ công việc cụ thể cho {subject_a} và một ví dụ cho {subject_b}.",
    ]
    if extra_line:
        summary_bullets[2] = f"Ghi chú bổ sung hiện có: {extra_line}. Tuy vậy vẫn cần chốt rõ 3 trục so sánh chính."

    key_points = [
        f"{subject_a} nên được mô tả bằng mục tiêu công việc và loại đầu ra chính.",
        f"{subject_b} cần được đặt cạnh {subject_a} trên cùng một khung so sánh.",
        "Ba trục tốt nhất để so sánh là mục tiêu, đầu ra và cách làm việc hằng ngày.",
        "Chỉ nên kết luận từ những gì thật sự có trong ghi chú, không suy rộng sang lĩnh vực bên cạnh.",
        "Nếu thiếu ví dụ công việc, mức độ kiểm chứng chỉ nên dừng ở unverifiable.",
    ]

    return {
        "title": f"Phân biệt {subject_a} và {subject_b}",
        "accuracy_score": None,
        "accuracy_assessment": "unverifiable",
        "accuracy_reasoning": "Nội dung hiện có cho thấy hướng hiểu nhưng chưa đủ dữ kiện để chấm độ chính xác sâu hơn.",
        "summary": "\n".join(f"- {normalize_text(item)}" for item in summary_bullets[:4]),
        "key_points": [normalize_text(item) for item in key_points],
        "corrections": [],
        "knowledge_detail_data": _build_analysis_knowledge_fallback(
            analysis_goal,
            focus_topic,
            learner_context,
        ),
        "topic_tags": normalize_topic_tags([subject_a, subject_b], focus_topic or analysis_goal),
        "enrichment": "",
    }


def _build_definition_fallback(
    analysis_content: str,
    analysis_goal: str,
    focus_topic: str,
    learner_context: dict[str, str],
) -> dict[str, Any]:
    topic = normalize_topic_phrase(focus_topic or analysis_goal) or "khái niệm chính"
    sentences = _clean_analysis_sentences(analysis_content)
    evidence_line = normalize_text(sentences[0]) if sentences else ""
    summary_bullets = [
        f"Câu hỏi đang cần một định nghĩa rõ cho {topic}, sau đó mới đến phạm vi áp dụng và ví dụ.",
        f"Ghi chú hiện tại nêu: {evidence_line}" if evidence_line else f"Ghi chú hiện tại chưa đủ để khẳng định định nghĩa của {topic}.",
        f"Để trả lời tốt hơn, nội dung nên làm rõ {topic} dùng để làm gì, khi nào áp dụng và dễ nhầm với khái niệm nào.",
        "Nếu ghi chú chưa có ví dụ hoặc ngữ cảnh sử dụng, chỉ nên xem đây là mức hiểu sơ bộ.",
    ]
    key_points = [
        f"{topic} cần được trả lời bằng định nghĩa ngắn và phạm vi áp dụng.",
        "Không nên biến câu trả lời thành bài giảng rộng về cả lĩnh vực.",
        "Muốn kiểm chứng tốt, cần có ví dụ hoặc tình huống dùng khái niệm đó.",
        "Nếu thiếu dữ kiện, nên giữ accuracy ở mức unverifiable.",
    ]
    return {
        "title": topic,
        "accuracy_score": None,
        "accuracy_assessment": "unverifiable",
        "accuracy_reasoning": "Nội dung hiện tại chưa đủ bằng chứng để xác nhận đầy đủ định nghĩa và phạm vi áp dụng.",
        "summary": "\n".join(f"- {normalize_text(item)}" for item in summary_bullets[:4]),
        "key_points": [normalize_text(item) for item in key_points[:5]],
        "corrections": [],
        "knowledge_detail_data": _build_analysis_knowledge_fallback(
            analysis_goal,
            focus_topic,
            learner_context,
        ),
        "topic_tags": normalize_topic_tags([topic], topic),
        "enrichment": "",
    }


def _build_review_fallback(
    analysis_content: str,
    analysis_goal: str,
    focus_topic: str,
    learner_context: dict[str, str],
) -> dict[str, Any]:
    sentences = _clean_analysis_sentences(analysis_content)
    bullets = sentences[:4] or [
        f"Nội dung hiện tại đang xoay quanh {focus_topic}.",
        "Cần bám đúng câu hỏi người dùng thay vì mở rộng sang chủ đề lân cận.",
    ]
    return {
        "title": _build_compact_analysis_title(analysis_goal, focus_topic),
        "accuracy_score": None,
        "accuracy_assessment": "unverifiable",
        "accuracy_reasoning": "Nội dung chưa đủ dữ kiện để chấm độ chính xác sâu hơn hoặc AI chưa tạo được bản phân tích đủ mạnh.",
        "summary": "\n".join(f"- {normalize_text(item)}" for item in bullets[:4]),
        "key_points": [normalize_text(item) for item in bullets[:5]],
        "corrections": [],
        "knowledge_detail_data": _build_analysis_knowledge_fallback(
            analysis_goal,
            focus_topic,
            learner_context,
        ),
        "topic_tags": normalize_topic_tags([], focus_topic or analysis_goal),
        "enrichment": "",
    }


def _build_analysis_fallback(
    analysis_content: str,
    focus_topic: str,
    analysis_goal: str,
    learner_context: dict[str, str],
) -> dict[str, Any]:
    kind = _detect_analysis_kind(analysis_goal)
    if kind == "comparison":
        return _build_compare_fallback(analysis_content, analysis_goal, focus_topic, learner_context)
    if kind in {"definition", "mechanism", "structure"}:
        return _build_definition_fallback(analysis_content, analysis_goal, focus_topic, learner_context)
    return _build_review_fallback(analysis_content, analysis_goal, focus_topic, learner_context)


def _legacy_analysis_result_needs_rewrite(analysis_goal: str, focus_topic: str, ai_result: dict[str, Any]) -> bool:
    title = normalize_text(str(ai_result.get("title") or ""))
    summary = normalize_text(str(ai_result.get("summary") or ""))
    raw_key_points = ai_result.get("key_points")
    knowledge_detail = ai_result.get("knowledge_detail_data") or {}
    detailed_sections = knowledge_detail.get("detailed_sections") or {}
    knowledge_summary = normalize_text(str(knowledge_detail.get("summary") or ""))
    key_points = [
        normalize_text(str(item))
        for item in (raw_key_points if isinstance(raw_key_points, list) else [])
        if normalize_text(str(item))
    ]
    combined = " ".join(
        [
            title,
            summary,
            knowledge_summary,
            *key_points,
            str((detailed_sections.get("core_concept") or {}).get("content") or ""),
            str((detailed_sections.get("mechanism") or {}).get("content") or ""),
        ]
    )

    if not title:
        return True
    if title.endswith("?"):
        return True
    if len(key_points) < 3:
        return True
    if len(summary) < 80:
        return True
    if _summary_bullet_count(summary) < 3:
        return True
    if _looks_generic_analysis_text(combined):
        return True
    if _focus_overlap_ratio(combined, focus_topic) < 0.34:
        return True

    lowered = strip_accents(combined).lower()
    if any(prefix in lowered for prefix in ("cau hoi can phan tich", "noi dung cua toi", "chu de can kiem tra")):
        return True

    compare_subjects = _parse_compare_subjects(analysis_goal)
    if compare_subjects and not all(strip_accents(subject).lower() in lowered for subject in compare_subjects):
        return True

    return False


def _legacy_violates_analysis_plan_v1(ai_result: dict[str, Any], plan: dict[str, Any]) -> bool:
    must_include = [normalize_topic_phrase(str(item)) or normalize_text(str(item)) for item in plan.get("must_include", []) if str(item).strip()]
    if not must_include:
        return False

    knowledge_detail = ai_result.get("knowledge_detail_data") or {}
    detailed_sections = knowledge_detail.get("detailed_sections") or {}
    combined = normalize_text(
        " ".join(
            [
                str(ai_result.get("title") or ""),
                str(ai_result.get("summary") or ""),
                " ".join(str(item) for item in ai_result.get("key_points") or []),
                str(knowledge_detail.get("summary") or ""),
                str((detailed_sections.get("core_concept") or {}).get("content") or ""),
                str((detailed_sections.get("mechanism") or {}).get("content") or ""),
                str((detailed_sections.get("components_and_relationships") or {}).get("content") or ""),
                " ".join(
                    " ".join(
                        [
                            str(item.get("original") or ""),
                            str(item.get("correction") or ""),
                            str(item.get("explanation") or ""),
                        ]
                    )
                    for item in ai_result.get("corrections") or []
                    if isinstance(item, dict)
                ),
            ]
        )
    )
    haystack = strip_accents(combined).lower()

    if plan.get("analysis_kind") == "comparison":
        targets = [strip_accents(item).lower() for item in plan.get("comparison_targets", []) if item]
        if targets and not all(target in haystack for target in targets):
            return True

    covered = sum(1 for item in must_include if strip_accents(item).lower() in haystack)
    if covered < min(2, len(must_include)):
        return True

    evidence_targets = [normalize_text(str(item)) for item in plan.get("evidence_targets", []) if str(item).strip()]
    if evidence_targets:
        evidence_covered = sum(1 for item in evidence_targets if strip_accents(item).lower() in haystack)
        if evidence_covered == 0:
            return True

    return False


def _legacy_normalize_analysis_summary(summary: object, key_points: object, fallback_summary: str) -> str:
    bullets: list[str] = []
    if isinstance(summary, str):
        lowered_summary = strip_accents(normalize_text(summary)).lower()
        if any(prefix in lowered_summary for prefix in ANALYZE_GOAL_PREFIXES + ANALYZE_CONTENT_PREFIXES):
            return fallback_summary
        for line in summary.splitlines():
            cleaned = normalize_text(line.lstrip("-*• ").strip())
            if cleaned and cleaned not in bullets:
                bullets.append(cleaned)

    if len(bullets) < 3 and isinstance(key_points, list):
        for item in key_points:
            cleaned = normalize_text(str(item))
            if cleaned and cleaned not in bullets:
                bullets.append(cleaned)
            if len(bullets) >= 4:
                break

    if not bullets:
        return fallback_summary
    return "\n".join(f"- {normalize_text(item)}" for item in bullets[:4])


def _normalize_analysis_key_points(
    raw_points: object,
    fallback_points: list[str],
    *,
    analysis_goal: str,
    focus_topic: str,
) -> list[str]:
    points: list[str] = []
    if isinstance(raw_points, list):
        for item in raw_points:
            cleaned = normalize_text(str(item))
            if not cleaned or _looks_generic_analysis_text(cleaned):
                continue
            lowered = strip_accents(cleaned).lower()
            if any(prefix in lowered for prefix in ANALYZE_GOAL_PREFIXES + ANALYZE_CONTENT_PREFIXES):
                return fallback_points[:5]
            if cleaned not in points:
                points.append(cleaned)
            if len(points) >= 5:
                break

    if len(points) >= 4 and not _analysis_key_points_need_fallback(analysis_goal, focus_topic, points):
        return points[:5]
    return fallback_points[:5]


def _legacy_extract_analysis_knowledge_detail_data_v1(
    ai_result: dict[str, Any],
    fallback_result: dict[str, Any],
) -> dict[str, Any]:
    fallback_payload = fallback_result.get("knowledge_detail_data") or {}
    raw_payload = ai_result.get("knowledge_detail_data")
    if not isinstance(raw_payload, dict):
        return fallback_payload

    raw_sections = raw_payload.get("detailed_sections")
    fallback_sections = fallback_payload.get("detailed_sections") or {}
    if not isinstance(raw_sections, dict):
        return fallback_payload

    normalized_sections: dict[str, dict[str, str]] = {}
    for key in SECTION_ORDER:
        raw_section = raw_sections.get(key)
        raw_title = ""
        content = ""
        if isinstance(raw_section, dict):
            raw_title = normalize_text(str(raw_section.get("title") or ""))
            content = _normalize_multiline_text(raw_section.get("content"))
        fallback_section = fallback_sections.get(key) or {}
        fallback_title = normalize_text(str(fallback_section.get("title") or SECTION_DISPLAY_TITLES[key]))
        fallback_content = normalize_text(str(fallback_section.get("content") or ""))

        if len(content) < 70 or _looks_generic_analysis_text(content):
            content = fallback_content

        normalized_sections[key] = {
            "title": raw_title or fallback_title,
            "content": content or fallback_content,
        }

    raw_summary = _normalize_multiline_text(raw_payload.get("summary"))
    summary = raw_summary or normalize_text(str(fallback_payload.get("summary") or ""))
    if _summary_bullet_count(summary) < 3 or _looks_generic_analysis_text(summary):
        summary = normalize_text(str(fallback_payload.get("summary") or ""))

    adaptation = raw_payload.get("teaching_adaptation")
    fallback_adaptation = fallback_payload.get("teaching_adaptation") or {}
    if not isinstance(adaptation, dict):
        adaptation = {}

    return {
        "title": normalize_text(str(raw_payload.get("title") or fallback_payload.get("title") or "")),
        "summary": summary,
        "detailed_sections": normalized_sections,
        "teaching_adaptation": {
            "focus_priority": normalize_text(
                str(adaptation.get("focus_priority") or fallback_adaptation.get("focus_priority") or "")
            ),
            "tone": normalize_text(str(adaptation.get("tone") or fallback_adaptation.get("tone") or "")),
            "depth_control": normalize_text(
                str(adaptation.get("depth_control") or fallback_adaptation.get("depth_control") or "")
            ),
            "example_strategy": normalize_text(
                str(adaptation.get("example_strategy") or fallback_adaptation.get("example_strategy") or "")
            ),
        },
    }


def _build_analysis_key_points_from_sections(knowledge_detail_data: dict[str, Any]) -> list[str]:
    points: list[str] = []
    sections = knowledge_detail_data.get("detailed_sections") or {}
    for key in (
        "core_concept",
        "mechanism",
        "components_and_relationships",
        "common_misconceptions",
        "real_world_applications",
    ):
        content = normalize_text(str((sections.get(key) or {}).get("content") or ""))
        sentences = _extract_sentences(content, 1)
        if not sentences:
            continue
        point = normalize_text(sentences[0])
        if point and point not in points:
            points.append(point)
        if len(points) >= 5:
            break
    return points[:5]


def _build_analysis_source_brief(
    analysis_goal: str,
    focus_topic: str,
    analysis_plan: dict[str, Any],
    sources: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "analysis_goal": analysis_goal,
        "focus_topic": focus_topic,
        "evidence_targets": analysis_plan.get("evidence_targets") or [],
        "source_count": len(sources),
        "reference_policy": {
            "rendered_separately_in_ui": True,
            "model_must_not_output_urls": True,
            "model_must_not_invent_citations": True,
        },
        "sources": sources,
    }


# Legacy definition kept temporarily because the file contained mojibake content.
# The clean implementation below is the active one.
def _build_analysis_session_input_legacy(
    content: str,
    source_label: str | None = None,
    analysis_goal: str | None = None,
) -> str:
    normalized_goal = _normalize_analysis_goal_override(analysis_goal)
    stored_content = content
    if normalized_goal:
        stored_content = (
            f"CÃ¢u há»i cáº§n phÃ¢n tÃ­ch: {normalized_goal}\n"
            f"Ná»™i dung: {content}"
        )
    return build_stored_user_input(stored_content, source_label)


def _build_analysis_session_input(
    content: str,
    source_label: str | None = None,
    analysis_goal: str | None = None,
) -> str:
    normalized_goal = _normalize_analysis_goal_override(analysis_goal)
    stored_content = content
    if normalized_goal:
        stored_content = (
            f"Cau hoi can phan tich: {normalized_goal}\n"
            f"Noi dung: {content}"
        )
    return build_stored_user_input(stored_content, source_label)


def _apply_source_confidence(
    accuracy_assessment: str,
    accuracy_score: int | None,
    sources: list[dict[str, str]],
) -> tuple[str, int | None]:
    if not sources:
        return "unverifiable", None
    if accuracy_assessment == "unverifiable":
        return accuracy_assessment, None
    if len(sources) == 1 and accuracy_assessment == "high":
        return "medium", min(accuracy_score or 78, 78)
    return accuracy_assessment, accuracy_score


def _build_analysis_verdict(
    accuracy_assessment: str,
    corrections: list[Correction],
    sources: list[dict[str, str]],
) -> str:
    if sources and accuracy_assessment == "high" and not corrections:
        return "correct"
    return "incorrect"


def _build_analysis_mindmap_context(
    title: str,
    summary: str,
    key_points: list[str],
    corrections: list[Correction],
) -> dict[str, str]:
    detail_lines = [f"- Ý chính: {point}" for point in key_points[:4]]
    for correction in corrections[:3]:
        if correction.correction:
            detail_lines.append(f"- Đính chính: {correction.correction}")
    return {
        "topic": title,
        "summary": summary,
        "key_points": "\n".join(f"- {point}" for point in key_points[:4]),
        "detail_outline": "\n".join(detail_lines),
    }


def _build_analysis_mindmap_points(
    knowledge_detail_data: dict[str, Any],
    key_points: list[str],
    corrections: list[Correction],
) -> list[str]:
    points = list(_build_analysis_key_points_from_sections(knowledge_detail_data) or key_points)
    for correction in corrections[:2]:
        if correction.correction:
            points.append(f"Dinh chinh: {correction.correction}")
    return points[:5]


async def _legacy_run_analysis(
    *,
    content: str,
    language: str,
    current_user: dict[str, str | None],
    supabase: Client,
    source_label: str | None = None,
    analysis_goal: str | None = None,
) -> AnalyzeResult:
    svc = SupabaseService(supabase)
    start_time = perf_counter()
    svc.ensure_profile(
        current_user["id"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        avatar_url=current_user.get("avatar_url"),
    )

    try:
        onboarding = svc.get_onboarding(current_user["id"])
    except Exception:
        onboarding = None
    learner_context = build_prompt_learning_context(get_user_context(onboarding))

    normalized_analysis_goal = _normalize_analysis_goal_override(analysis_goal)
    truncated_content = truncate_content(content)
    _validate_analysis_input(truncated_content, normalized_analysis_goal)

    analysis_goal = _extract_analysis_goal(truncated_content, normalized_analysis_goal)
    focus_topic = _extract_analysis_focus(truncated_content, analysis_goal)
    analysis_content = _strip_analysis_metadata(truncated_content)
    analysis_plan = await _build_analysis_plan(analysis_goal, focus_topic, analysis_content)
    analysis_goal = normalize_text(str(analysis_plan.get("main_question") or analysis_goal))
    focus_topic = normalize_topic_phrase(str(analysis_plan.get("focus_topic") or focus_topic)) or focus_topic
    normalized_title = _prefer_compact_analysis_title(
        _build_compact_analysis_title(analysis_goal, focus_topic),
        analysis_content,
    )
    analysis_brief = _build_analysis_brief(analysis_goal, focus_topic, analysis_content)
    analysis_brief["plan"] = analysis_plan
    source_task = asyncio.create_task(
        search_knowledge_sources(
            message=analysis_goal,
            focus_topic=focus_topic,
            evidence_targets=[str(item) for item in analysis_plan.get("evidence_targets", []) if str(item).strip()],
        )
    )
    verified_sources = await resolve_source_lookup(source_task, flow_label="analyze")
    source_brief = _build_analysis_source_brief(
        analysis_goal,
        focus_topic,
        analysis_plan,
        verified_sources,
    )
    fallback_result = _build_analysis_fallback(analysis_content, focus_topic, analysis_goal, learner_context)
    if _should_generate_analysis_blueprint(analysis_plan, analysis_content):
        try:
            raw_blueprint = await gemini.generate_json(
                build_analyze_blueprint_prompt(
                    content=analysis_content,
                    language=language,
                    analysis_goal=analysis_goal,
                    focus_topic=focus_topic,
                    analysis_brief=analysis_brief,
                    source_brief=source_brief,
                )
            )
        except Exception as exc:
            print(f"[analyze] Blueprint generation failed, using fallback blueprint: {exc}")
            raw_blueprint = (fallback_result.get("knowledge_detail_data") or {}).get("content_blueprint") or {}
    else:
        raw_blueprint = (fallback_result.get("knowledge_detail_data") or {}).get("content_blueprint") or {}

    fallback_blueprint = (
        (fallback_result.get("knowledge_detail_data") or {}).get("content_blueprint")
        or build_blueprint_fallback(
            title=focus_topic or analysis_goal,
            question_type=str(analysis_plan.get("analysis_kind") or "review"),
            learner_context=learner_context,
            comparison_targets=analysis_plan.get("comparison_targets") or [],
            analysis_content=analysis_content,
        )
    )
    content_blueprint = normalize_blueprint(
        raw_blueprint,
        fallback_blueprint=fallback_blueprint,
    )

    try:
        ai_result = await gemini.generate_json(
            build_analyze_core_prompt(
                content=analysis_content,
                language=language,
                analysis_goal=analysis_goal,
                focus_topic=focus_topic,
                learner_context=learner_context,
                analysis_brief=analysis_brief,
                source_brief=source_brief,
                content_blueprint=content_blueprint,
            )
        )
    except Exception as exc:
        print(f"[analyze] Main analysis failed, using fallback: {exc}")
        ai_result = fallback_result

    if _analysis_result_needs_rewrite(analysis_goal, focus_topic, ai_result) or _violates_analysis_plan(ai_result, analysis_plan):
        ai_result = fallback_result
    title = _prefer_compact_analysis_title(
        normalized_title or normalize_topic_phrase(str(ai_result.get("title") or "")) or fallback_result["title"],
        analysis_content,
    )

    accuracy_assessment = str(ai_result.get("accuracy_assessment") or fallback_result["accuracy_assessment"]).strip()
    raw_accuracy_score = ai_result.get("accuracy_score")
    if isinstance(raw_accuracy_score, bool):
        accuracy_score: int | None = int(raw_accuracy_score)
    elif isinstance(raw_accuracy_score, (int, float)):
        accuracy_score = max(0, min(100, int(raw_accuracy_score)))
    else:
        accuracy_score = None

    if accuracy_assessment == "unverifiable":
        accuracy_score = None
    accuracy_assessment, accuracy_score = _apply_source_confidence(
        accuracy_assessment,
        accuracy_score,
        verified_sources,
    )

    fallback_summary = str(fallback_result["summary"])
    fallback_points = [str(point) for point in fallback_result["key_points"]]
    summary = _normalize_analysis_summary(
        ai_result.get("summary"),
        ai_result.get("key_points"),
        fallback_summary,
        focus_topic=focus_topic,
    )
    knowledge_detail_data = _extract_analysis_knowledge_detail_data(ai_result, fallback_result)
    key_points = _normalize_analysis_key_points(
        ai_result.get("key_points"),
        _build_analysis_key_points_from_sections(knowledge_detail_data) or fallback_points,
        analysis_goal=analysis_goal,
        focus_topic=focus_topic,
    )
    corrections = _normalize_corrections(ai_result.get("corrections"))
    topic_tags = normalize_topic_tags(ai_result.get("topic_tags"), title or focus_topic or content)
    verdict = _build_analysis_verdict(accuracy_assessment, corrections, verified_sources)
    effective_source_label = source_label or "Nội dung nhập tay"

    mindmap_points = list(_build_analysis_key_points_from_sections(knowledge_detail_data) or key_points)
    for correction in corrections[:2]:
        if correction.correction:
            mindmap_points.append(f"ÄÃ­nh chÃ­nh: {correction.correction}")
    mindmap_points = [point.replace("Ã„ÂÃƒÂ­nh chÃƒÂ­nh:", "Dinh chinh:") for point in mindmap_points]
    clean_mindmap_points = list(_build_analysis_key_points_from_sections(knowledge_detail_data) or key_points)
    for correction in corrections[:2]:
        if correction.correction:
            clean_mindmap_points.append(f"Dinh chinh: {correction.correction}")
    mindmap_points = clean_mindmap_points
    mindmap_points = _build_analysis_mindmap_points(
        knowledge_detail_data,
        key_points,
        corrections,
    )
    mindmap_data = build_basic_mindmap(title, mindmap_points)

    session = svc.create_session(
        current_user["id"],
        {
            "session_type": "analyze",
            "title": title,
            "user_input": _build_analysis_session_input(content, source_label, analysis_goal),
            "topic_tags": topic_tags,
            "accuracy_score": accuracy_score,
            "accuracy_assessment": accuracy_assessment,
            "summary": summary,
            "key_points": key_points,
            "corrections": [item.model_dump() for item in corrections],
            "infographic_data": knowledge_detail_data,
            "mindmap_data": mindmap_data,
            "sources": verified_sources,
            "language": language,
            "duration_ms": int((perf_counter() - start_time) * 1000),
        },
    )
    if not session or not session.get("id"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lưu phiên phân tích.",
        )

    return AnalyzeResult(
        session_id=session["id"],
        title=title,
        verdict=verdict,
        accuracy_score=accuracy_score,
        accuracy_assessment=accuracy_assessment,
        summary=summary,
        key_points=key_points,
        corrections=corrections,
        knowledge_detail_data=knowledge_detail_data,
        topic_tags=topic_tags,
        mindmap_data=mindmap_data,
        sources=verified_sources,
        source_label=effective_source_label,
        input_preview=build_input_preview(content),
    )


def _build_blueprint_sections(
    title: str,
    content_blueprint: dict[str, str],
) -> dict[str, dict[str, str]]:
    return {
        key: {
            "title": SECTION_DISPLAY_TITLES[key],
            "content": build_section_content_from_blueprint(
                key,
                title=title,
                blueprint=content_blueprint,
            ),
        }
        for key in SECTION_ORDER
    }


def _build_analysis_knowledge_fallback(
    analysis_goal: str,
    focus_topic: str,
    learner_context: dict[str, str],
) -> dict[str, Any]:
    title = _build_compact_analysis_title(analysis_goal, focus_topic)
    kind = _detect_analysis_kind(analysis_goal)
    content_blueprint = build_blueprint_fallback(
        title=title,
        question_type=kind,
        learner_context=learner_context,
        comparison_targets=_parse_compare_subjects(analysis_goal) or [],
    )
    section_briefs = build_section_briefs(
        content_blueprint,
        title=title,
        question_type=kind,
        mode="analyze",
        main_question=analysis_goal,
        focus_topic=focus_topic,
        comparison_targets=_parse_compare_subjects(analysis_goal) or [],
    )
    if kind == "structure":
        section_briefs = _apply_structure_analysis_briefs(section_briefs, content_blueprint)
    return {
        "title": title,
        "summary": build_summary_from_briefs(section_briefs, key="detail_focus"),
        "content_blueprint": content_blueprint,
        "section_briefs": section_briefs,
        "active_section_keys": list(SECTION_ORDER),
        "detailed_sections": _build_blueprint_sections(title, content_blueprint),
        "teaching_adaptation": {
            "focus_priority": f"Bám sát câu hỏi gốc về {title}",
            "tone": "Rõ ràng, trực diện, ưu tiên bản chất trước",
            "depth_control": "Đi từ khái niệm đến cơ chế, giới hạn và ví dụ",
            "example_strategy": _build_example_context(learner_context),
        },
    }


def _legacy_extract_analysis_knowledge_detail_data_v2(
    ai_result: dict[str, Any],
    fallback_result: dict[str, Any],
    *,
    content_blueprint: dict[str, str],
    section_briefs: dict[str, list[str]],
    title: str,
) -> dict[str, Any]:
    fallback_payload = fallback_result.get("knowledge_detail_data") or {}
    normalized_sections, active_section_keys = normalize_detailed_sections(
        ai_result.get("detailed_sections"),
        fallback_sections=fallback_payload.get("detailed_sections") or {},
        blueprint=content_blueprint,
        title=title,
    )

    adaptation = ai_result.get("teaching_adaptation")
    fallback_adaptation = fallback_payload.get("teaching_adaptation") or {}
    if not isinstance(adaptation, dict):
        adaptation = {}

    detail_summary = build_summary_from_briefs(
        section_briefs,
        key="detail_focus",
        fallback_text=fallback_payload.get("summary") or "",
    )
    section_bullets = _build_analysis_key_points_from_sections(
        {
            "detailed_sections": normalized_sections,
        }
    )
    if section_bullets:
        detail_summary = "\n".join(f"- {item}" for item in section_bullets[:4])

    return {
        "title": title,
        "summary": detail_summary,
        "content_blueprint": content_blueprint,
        "section_briefs": section_briefs,
        "active_section_keys": active_section_keys,
        "detailed_sections": normalized_sections,
        "teaching_adaptation": {
            "focus_priority": normalize_text(
                str(adaptation.get("focus_priority") or fallback_adaptation.get("focus_priority") or "")
            ),
            "tone": normalize_text(str(adaptation.get("tone") or fallback_adaptation.get("tone") or "")),
            "depth_control": normalize_text(
                str(adaptation.get("depth_control") or fallback_adaptation.get("depth_control") or "")
            ),
            "example_strategy": normalize_text(
                str(adaptation.get("example_strategy") or fallback_adaptation.get("example_strategy") or "")
            ),
        },
    }


def _legacy_violates_analysis_plan_v2(ai_result: dict[str, Any], plan: dict[str, Any]) -> bool:
    must_include = [
        normalize_topic_phrase(str(item)) or normalize_text(str(item))
        for item in plan.get("must_include", [])
        if str(item).strip()
    ]
    if not must_include:
        return False

    detailed_sections = ai_result.get("detailed_sections") or {}
    if not isinstance(detailed_sections, dict):
        knowledge_detail = ai_result.get("knowledge_detail_data") or {}
        detailed_sections = knowledge_detail.get("detailed_sections") or {}

    combined = normalize_text(
        " ".join(
            [
                str(ai_result.get("title") or ""),
                str(ai_result.get("summary") or ""),
                " ".join(str(item) for item in ai_result.get("key_points") or []),
                str((detailed_sections.get("core_concept") or {}).get("content") or ""),
                str((detailed_sections.get("mechanism") or {}).get("content") or ""),
                str((detailed_sections.get("components_and_relationships") or {}).get("content") or ""),
                " ".join(
                    " ".join(
                        [
                            str(item.get("original") or ""),
                            str(item.get("correction") or ""),
                            str(item.get("explanation") or ""),
                        ]
                    )
                    for item in ai_result.get("corrections") or []
                    if isinstance(item, dict)
                ),
            ]
        )
    )
    haystack = strip_accents(combined).lower()

    if plan.get("analysis_kind") == "comparison":
        targets = [strip_accents(item).lower() for item in plan.get("comparison_targets", []) if item]
        if targets and not all(target in haystack for target in targets):
            return True

    covered = sum(1 for item in must_include if strip_accents(item).lower() in haystack)
    return covered == 0


def _legacy_analysis_result_needs_rewrite_v2(analysis_goal: str, focus_topic: str, ai_result: dict[str, Any]) -> bool:
    title = normalize_text(str(ai_result.get("title") or ""))
    summary = _normalize_multiline_text(ai_result.get("summary"))
    sections = ai_result.get("detailed_sections")
    if not title or title.endswith("?"):
        return True
    if len(summary) < 80 or _summary_bullet_count(summary) < 3 or _looks_generic_analysis_text(summary):
        return True
    if not isinstance(sections, dict):
        return True

    core_content = _normalize_multiline_text((sections.get("core_concept") or {}).get("content"))
    mechanism_content = _normalize_multiline_text((sections.get("mechanism") or {}).get("content"))
    relationship_content = _normalize_multiline_text(
        (sections.get("components_and_relationships") or {}).get("content")
    )
    if len(core_content) < 70 or len(mechanism_content) < 70 or len(relationship_content) < 70:
        return True
    if _looks_generic_analysis_text(core_content) or _looks_generic_analysis_text(mechanism_content):
        return True
    if semantic_overlap_ratio(core_content, mechanism_content) > 0.62:
        return True
    if semantic_overlap_ratio(mechanism_content, relationship_content) > 0.62:
        return True

    compare_subjects = _parse_compare_subjects(analysis_goal)
    if compare_subjects:
        lowered = strip_accents(" ".join([title, core_content, mechanism_content, relationship_content])).lower()
        if not all(strip_accents(subject).lower() in lowered for subject in compare_subjects):
            return True
    if _focus_overlap_ratio(" ".join([summary, core_content, mechanism_content]), focus_topic) < 0.34:
        return True
    return False


def _extract_analysis_focus(content: str, analysis_goal: str) -> str:
    lines = [normalize_text(line) for line in content.splitlines() if normalize_text(line)]
    for line in lines[:8]:
        extracted = _extract_prefixed_value(
            line,
            ANALYZE_GOAL_PREFIXES + ("chu de can tu kiem tra", "chu de can kiem tra", "focus topic"),
        )
        if extracted:
            compact = build_core_title(extracted, "")
            if compact and not _analysis_title_needs_cleanup(compact):
                return compact
            return normalize_topic_phrase(extracted)

    if _detect_analysis_kind(analysis_goal) in {"definition", "mechanism", "structure"}:
        compact = build_core_title(analysis_goal, "")
        if compact and not _analysis_title_needs_cleanup(compact):
            return compact
        if lines:
            first_line_title = build_core_title(lines[0], "")
            if first_line_title and not _analysis_title_needs_cleanup(first_line_title):
                return first_line_title

    focus = normalize_topic_phrase(analysis_goal)
    if focus:
        return focus

    stripped = normalize_topic_phrase(_strip_analysis_metadata(content))
    return stripped or "chu de chinh trong noi dung"


def _build_compact_analysis_title(analysis_goal: str, focus_topic: str) -> str:
    cleaned_goal = _strip_known_question_prefixes(analysis_goal)
    cleaned_focus = _strip_known_question_prefixes(focus_topic)
    compare_subjects = _parse_compare_subjects(cleaned_goal)
    if compare_subjects:
        return build_core_title(f"{compare_subjects[0]} va {compare_subjects[1]}", "Phan tich noi dung")

    preferred = cleaned_focus or cleaned_goal
    compact = build_core_title(preferred, "")
    if compact and not _analysis_title_needs_cleanup(compact):
        return compact
    return compact or build_core_title(preferred, "Phan tich noi dung")


def _is_direct_analysis_answer(analysis_goal: str, focus_topic: str, text: str) -> bool:
    lead = strip_accents(normalize_text(str(text or ""))).lower()
    if not lead:
        return False

    compare_subjects = _parse_compare_subjects(analysis_goal)
    if compare_subjects:
        return (
            all(strip_accents(subject).lower() in lead for subject in compare_subjects)
            and any(marker in lead for marker in (" khac ", " phan biet ", " so sanh "))
        )

    analysis_kind = _detect_analysis_kind(analysis_goal)
    if analysis_kind == "definition":
        return _focus_overlap_ratio(lead, focus_topic) >= 0.34 and any(
            marker in f" {lead} "
            for marker in (" la ", " la mot ", " duoc dung de ", " chi ")
        )
    if analysis_kind == "structure":
        return _focus_overlap_ratio(lead, focus_topic) >= 0.34 and any(
            marker in f" {lead} "
            for marker in (" gom ", " bao gom ", " thanh phan ", " cau truc ")
        )
    if analysis_kind == "mechanism":
        return _focus_overlap_ratio(lead, focus_topic) >= 0.34 and any(
            marker in f" {lead} "
            for marker in (" hoat dong ", " van hanh ", " dien ra ", " bat dau ")
        )
    return _focus_overlap_ratio(lead, focus_topic) >= 0.24


def _apply_structure_analysis_briefs(
    section_briefs: dict[str, list[str]],
    content_blueprint: dict[str, str],
) -> dict[str, list[str]]:
    section_briefs["overview"] = [
        item
        for item in [
            normalize_text(content_blueprint.get("components", "")),
            normalize_text(content_blueprint.get("core_definition", "")),
            normalize_text(content_blueprint.get("mechanism", "")),
            normalize_text(content_blueprint.get("conditions_and_limits", "")),
        ]
        if item
    ][:4]
    section_briefs["core_takeaways"] = [
        item
        for item in [
            normalize_text(content_blueprint.get("components", "")),
            normalize_text(content_blueprint.get("core_definition", "")),
            normalize_text(content_blueprint.get("mechanism", "")),
            normalize_text(content_blueprint.get("misconceptions", "")),
            normalize_text(content_blueprint.get("conditions_and_limits", "")),
        ]
        if item
    ][:5]
    return section_briefs


def _analysis_key_points_need_fallback(
    analysis_goal: str,
    focus_topic: str,
    key_points: list[str],
) -> bool:
    if len(key_points) < 4:
        return True

    analysis_kind = _detect_analysis_kind(analysis_goal)
    compare_subjects = _parse_compare_subjects(analysis_goal)
    useful_points = 0
    generic_points = 0
    compare_points = 0
    structure_points = 0
    mechanism_points = 0
    boundary_points = 0
    repeated_pairs = 0

    for index, point in enumerate(key_points):
        cleaned = normalize_text(point)
        if not cleaned:
            continue
        if _looks_generic_analysis_text(cleaned):
            generic_points += 1
            continue

        lowered = strip_accents(cleaned).lower()
        if compare_subjects and all(strip_accents(subject).lower() in lowered for subject in compare_subjects):
            compare_points += 1
        if analysis_kind == "structure" and any(
            marker in f" {lowered} " for marker in (" gom ", " bao gom ", " thanh phan ", " cau truc ")
        ):
            structure_points += 1
        if _contains_any_marker(cleaned, ANALYZE_MECHANISM_MARKERS):
            mechanism_points += 1
        if _contains_any_marker(cleaned, ANALYZE_BOUNDARY_MARKERS):
            boundary_points += 1
        if index < len(key_points) - 1 and semantic_overlap_ratio(cleaned, key_points[index + 1]) > 0.82:
            repeated_pairs += 1

        if _is_substantive_analysis_line(cleaned, focus_topic):
            useful_points += 1
            continue

        if compare_subjects and any(strip_accents(subject).lower() in lowered for subject in compare_subjects):
            useful_points += 1

    if generic_points >= 2:
        return True
    if useful_points < 3:
        return True
    if repeated_pairs >= 2:
        return True
    if compare_subjects and compare_points == 0:
        return True
    if analysis_kind == "structure" and structure_points == 0:
        return True
    if analysis_kind in {"definition", "mechanism"} and mechanism_points == 0:
        return True
    if analysis_kind == "definition" and boundary_points == 0:
        return True
    return False


def _normalize_analysis_summary(
    summary: object,
    key_points: object,
    fallback_summary: str,
    *,
    focus_topic: str,
) -> str:
    bullets: list[str] = []
    if isinstance(summary, str):
        lowered_summary = strip_accents(normalize_text(summary)).lower()
        if any(prefix in lowered_summary for prefix in ANALYZE_GOAL_PREFIXES + ANALYZE_CONTENT_PREFIXES):
            return fallback_summary
        for line in summary.splitlines():
            cleaned = normalize_text(line.lstrip("-*• ").strip())
            if _contains_trailing_ellipsis(cleaned):
                continue
            if cleaned and cleaned not in bullets:
                bullets.append(cleaned)

    if len(bullets) < 3 and isinstance(key_points, list):
        for item in key_points:
            cleaned = normalize_text(str(item))
            if _contains_trailing_ellipsis(cleaned):
                continue
            if cleaned and cleaned not in bullets:
                bullets.append(cleaned)
            if len(bullets) >= 4:
                break

    if not bullets:
        return fallback_summary
    normalized_summary = "\n".join(f"- {normalize_text(item)}" for item in bullets[:4])
    if _analysis_summary_needs_fallback(normalized_summary, focus_topic):
        return fallback_summary
    return normalized_summary


def _merge_analysis_result(
    ai_result: object,
    fallback_result: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(fallback_result)
    raw = ai_result if isinstance(ai_result, dict) else {}

    title = normalize_text(str(raw.get("title") or ""))
    if title and not title.endswith("?"):
        merged["title"] = title

    summary = _normalize_multiline_text(raw.get("summary"))
    if summary:
        merged["summary"] = summary

    key_points = _normalize_analysis_key_points(
        raw.get("key_points"),
        merged.get("key_points") or [],
        analysis_goal=str(merged.get("analysis_goal") or merged.get("title") or ""),
        focus_topic=str(merged.get("focus_topic") or merged.get("title") or ""),
    )
    if key_points:
        merged["key_points"] = key_points

    accuracy_assessment = normalize_text(str(raw.get("accuracy_assessment") or ""))
    if accuracy_assessment in {"high", "medium", "low", "unverifiable"}:
        merged["accuracy_assessment"] = accuracy_assessment

    accuracy_reasoning = normalize_text(str(raw.get("accuracy_reasoning") or ""))
    if accuracy_reasoning:
        merged["accuracy_reasoning"] = accuracy_reasoning

    raw_accuracy_score = raw.get("accuracy_score")
    if isinstance(raw_accuracy_score, bool):
        merged["accuracy_score"] = int(raw_accuracy_score)
    elif isinstance(raw_accuracy_score, (int, float)):
        merged["accuracy_score"] = max(0, min(100, int(raw_accuracy_score)))

    corrections = _normalize_corrections(raw.get("corrections"))
    if corrections:
        merged["corrections"] = [item.model_dump() for item in corrections]

    topic_tags = normalize_topic_tags(raw.get("topic_tags"), merged.get("title") or "")
    if topic_tags:
        merged["topic_tags"] = topic_tags

    fallback_knowledge = fallback_result.get("knowledge_detail_data") or {}
    fallback_sections = fallback_knowledge.get("detailed_sections") or {}
    raw_sections = raw.get("detailed_sections")
    merged_sections = {key: dict(value) for key, value in fallback_sections.items()}
    if isinstance(raw_sections, dict):
        for key in SECTION_ORDER:
            raw_section = raw_sections.get(key)
            if not isinstance(raw_section, dict):
                continue
            fallback_section = merged_sections.get(key) or {
                "title": SECTION_DISPLAY_TITLES[key],
                "content": "",
            }
            merged_sections[key] = {
                "title": normalize_text(
                    str(raw_section.get("title") or fallback_section.get("title") or SECTION_DISPLAY_TITLES[key])
                )
                or fallback_section.get("title")
                or SECTION_DISPLAY_TITLES[key],
                "content": _normalize_multiline_text(raw_section.get("content"))
                or normalize_text(str(fallback_section.get("content") or "")),
            }

    adaptation = raw.get("teaching_adaptation")
    fallback_adaptation = fallback_knowledge.get("teaching_adaptation") or {}
    merged["detailed_sections"] = merged_sections
    merged["teaching_adaptation"] = {
        "focus_priority": normalize_text(
            str((adaptation or {}).get("focus_priority") or fallback_adaptation.get("focus_priority") or "")
        ),
        "tone": normalize_text(str((adaptation or {}).get("tone") or fallback_adaptation.get("tone") or "")),
        "depth_control": normalize_text(
            str((adaptation or {}).get("depth_control") or fallback_adaptation.get("depth_control") or "")
        ),
        "example_strategy": normalize_text(
            str((adaptation or {}).get("example_strategy") or fallback_adaptation.get("example_strategy") or "")
        ),
    }
    return merged


async def _rewrite_analysis_result(
    *,
    content: str,
    language: str,
    analysis_goal: str,
    focus_topic: str,
    learner_context: dict[str, str],
    analysis_brief: dict[str, Any],
    source_brief: dict[str, Any],
    content_blueprint: dict[str, str],
    ai_result: dict[str, Any],
) -> dict[str, Any] | None:
    try:
        repaired = await gemini.generate_json(
            build_analyze_repair_prompt(
                content=content,
                language=language,
                analysis_goal=analysis_goal,
                focus_topic=focus_topic,
                learner_context=learner_context,
                analysis_brief=analysis_brief,
                source_brief=source_brief,
                content_blueprint=content_blueprint,
                weak_draft=ai_result,
            )
        )
    except Exception as exc:
        print(f"[analyze] Analysis repair failed, keeping salvage path: {exc}")
        return None
    return repaired if isinstance(repaired, dict) else None


async def _run_analysis(
    *,
    content: str,
    language: str,
    current_user: dict[str, str | None],
    supabase: Client,
    source_label: str | None = None,
    analysis_goal: str | None = None,
) -> AnalyzeResult:
    svc = SupabaseService(supabase)
    start_time = perf_counter()
    svc.ensure_profile(
        current_user["id"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        avatar_url=current_user.get("avatar_url"),
    )

    try:
        onboarding = svc.get_onboarding(current_user["id"])
    except Exception:
        onboarding = None
    learner_context = build_prompt_learning_context(get_user_context(onboarding))

    normalized_analysis_goal = _normalize_analysis_goal_override(analysis_goal)
    truncated_content = truncate_content(content)
    _validate_analysis_input(truncated_content, normalized_analysis_goal)

    analysis_goal = _extract_analysis_goal(truncated_content, normalized_analysis_goal)
    focus_topic = _extract_analysis_focus(truncated_content, analysis_goal)
    analysis_content = _strip_analysis_metadata(truncated_content)
    analysis_plan = await _build_analysis_plan(analysis_goal, focus_topic, analysis_content)
    analysis_goal = normalize_text(str(analysis_plan.get("main_question") or analysis_goal))
    focus_topic = normalize_topic_phrase(str(analysis_plan.get("focus_topic") or focus_topic)) or focus_topic
    normalized_title = _prefer_compact_analysis_title(
        _build_compact_analysis_title(analysis_goal, focus_topic),
        analysis_content,
    )
    analysis_brief = _build_analysis_brief(analysis_goal, focus_topic, analysis_content)
    analysis_brief["plan"] = analysis_plan

    verified_sources: list[dict[str, str]] = []
    if _should_lookup_analysis_sources(analysis_plan, analysis_goal, analysis_content):
        source_task = asyncio.create_task(
            search_knowledge_sources(
                message=analysis_goal,
                focus_topic=focus_topic,
                evidence_targets=[
                    str(item)
                    for item in analysis_plan.get("evidence_targets", [])
                    if str(item).strip()
                ],
            )
        )
        verified_sources = await resolve_source_lookup(source_task, flow_label="analyze")
    source_brief = _build_analysis_source_brief(
        analysis_goal,
        focus_topic,
        analysis_plan,
        verified_sources,
    )
    fallback_result = _build_analysis_fallback(
        analysis_content,
        focus_topic,
        analysis_goal,
        learner_context,
    )
    fallback_knowledge_detail = _build_analysis_knowledge_fallback(
        analysis_goal,
        focus_topic,
        learner_context,
    )
    fallback_result["title"] = normalized_title or fallback_knowledge_detail["title"] or fallback_result["title"]
    fallback_result["summary"] = build_summary_from_briefs(
        fallback_knowledge_detail.get("section_briefs") or {},
        key="overview",
        fallback_text=str(fallback_result.get("summary") or ""),
    )
    fallback_result["key_points"] = build_key_points_from_briefs(
        fallback_knowledge_detail.get("section_briefs") or {},
        fallback_result.get("key_points") or [],
    )
    fallback_result["knowledge_detail_data"] = fallback_knowledge_detail

    if _should_generate_analysis_blueprint(analysis_plan, analysis_content):
        try:
            raw_blueprint = await gemini.generate_json(
                build_analyze_blueprint_prompt(
                    content=analysis_content,
                    language=language,
                    analysis_goal=analysis_goal,
                    focus_topic=focus_topic,
                    analysis_brief=analysis_brief,
                    source_brief=source_brief,
                )
            )
        except Exception as exc:
            print(f"[analyze] Blueprint generation failed, using fallback blueprint: {exc}")
            raw_blueprint = (fallback_result.get("knowledge_detail_data") or {}).get("content_blueprint") or {}
    else:
        raw_blueprint = (fallback_result.get("knowledge_detail_data") or {}).get("content_blueprint") or {}

    fallback_blueprint = (
        (fallback_result.get("knowledge_detail_data") or {}).get("content_blueprint")
        or build_blueprint_fallback(
            title=focus_topic or analysis_goal,
            question_type=str(analysis_plan.get("analysis_kind") or "review"),
            learner_context=learner_context,
            comparison_targets=analysis_plan.get("comparison_targets") or [],
            analysis_content=analysis_content,
        )
    )
    content_blueprint = normalize_blueprint(
        raw_blueprint,
        fallback_blueprint=fallback_blueprint,
    )

    try:
        ai_result = await gemini.generate_json(
            build_analyze_core_prompt(
                content=analysis_content,
                language=language,
                analysis_goal=analysis_goal,
                focus_topic=focus_topic,
                learner_context=learner_context,
                analysis_brief=analysis_brief,
                source_brief=source_brief,
                content_blueprint=content_blueprint,
            )
        )
    except Exception as exc:
        print(f"[analyze] Main analysis failed, switching to salvage path: {exc}")
        ai_result = {}

    needs_rewrite = _analysis_result_needs_rewrite(
        analysis_goal,
        focus_topic,
        ai_result if isinstance(ai_result, dict) else {},
    ) or _violates_analysis_plan(
        ai_result if isinstance(ai_result, dict) else {},
        analysis_plan,
    )
    if needs_rewrite and isinstance(ai_result, dict) and ai_result:
        repaired_result = await _rewrite_analysis_result(
            content=analysis_content,
            language=language,
            analysis_goal=analysis_goal,
            focus_topic=focus_topic,
            learner_context=learner_context,
            analysis_brief=analysis_brief,
            source_brief=source_brief,
            content_blueprint=content_blueprint,
            ai_result=ai_result,
        )
        if repaired_result:
            ai_result = repaired_result

    if _analysis_result_needs_rewrite(
        analysis_goal,
        focus_topic,
        ai_result if isinstance(ai_result, dict) else {},
    ) or _violates_analysis_plan(
        ai_result if isinstance(ai_result, dict) else {},
        analysis_plan,
    ):
        ai_result = _merge_analysis_result(ai_result, fallback_result)

    title = _prefer_compact_analysis_title(
        normalized_title or normalize_topic_phrase(str(ai_result.get("title") or "")) or fallback_result["title"],
        analysis_content,
    )
    accuracy_assessment = str(ai_result.get("accuracy_assessment") or fallback_result["accuracy_assessment"]).strip()
    raw_accuracy_score = ai_result.get("accuracy_score")
    if isinstance(raw_accuracy_score, bool):
        accuracy_score: int | None = int(raw_accuracy_score)
    elif isinstance(raw_accuracy_score, (int, float)):
        accuracy_score = max(0, min(100, int(raw_accuracy_score)))
    else:
        accuracy_score = None

    if accuracy_assessment == "unverifiable":
        accuracy_score = None
    accuracy_assessment, accuracy_score = _apply_source_confidence(
        accuracy_assessment,
        accuracy_score,
        verified_sources,
    )

    fallback_summary = str(fallback_result["summary"])
    fallback_points = [str(point) for point in fallback_result["key_points"]]
    section_briefs = build_section_briefs(
        content_blueprint,
        title=title,
        question_type=str(analysis_plan.get("analysis_kind") or "review"),
        mode="analyze",
        main_question=analysis_goal,
        focus_topic=focus_topic,
        comparison_targets=analysis_plan.get("comparison_targets") or [],
        evidence_targets=analysis_plan.get("evidence_targets") or [],
    )
    if str(analysis_plan.get("analysis_kind") or "review") == "structure":
        section_briefs = _apply_structure_analysis_briefs(section_briefs, content_blueprint)
    summary = _normalize_analysis_summary(
        ai_result.get("summary"),
        ai_result.get("key_points"),
        fallback_summary,
        focus_topic=focus_topic,
    )
    if _contains_trailing_ellipsis(summary):
        summary = fallback_summary
    knowledge_detail_data = _extract_analysis_knowledge_detail_data(
        ai_result,
        fallback_result,
        content_blueprint=content_blueprint,
        section_briefs=section_briefs,
        title=title,
    )
    key_points = _normalize_analysis_key_points(
        ai_result.get("key_points"),
        build_key_points_from_briefs(
            section_briefs,
            fallback_points,
        ),
        analysis_goal=analysis_goal,
        focus_topic=focus_topic,
    )
    corrections = _normalize_corrections(ai_result.get("corrections"))
    topic_tags = normalize_topic_tags(ai_result.get("topic_tags"), title or focus_topic or content)
    effective_source_label = source_label or "Nội dung nhập tay"

    verdict = _build_analysis_verdict(accuracy_assessment, corrections, verified_sources)
    mindmap_data = build_basic_mindmap(
        title,
        _build_analysis_mindmap_points(
            knowledge_detail_data,
            key_points,
            corrections,
        ),
    )

    session = svc.create_session(
        current_user["id"],
        {
            "session_type": "analyze",
            "title": title,
            "user_input": _build_analysis_session_input(content, source_label, analysis_goal),
            "topic_tags": topic_tags,
            "accuracy_score": accuracy_score,
            "accuracy_assessment": accuracy_assessment,
            "summary": summary,
            "key_points": key_points,
            "corrections": [item.model_dump() for item in corrections],
            "infographic_data": knowledge_detail_data,
            "mindmap_data": mindmap_data,
            "sources": verified_sources,
            "language": language,
            "duration_ms": int((perf_counter() - start_time) * 1000),
        },
    )
    if not session or not session.get("id"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="KhÃ´ng thá»ƒ lÆ°u phiÃªn phÃ¢n tÃ­ch.",
        )

    return AnalyzeResult(
        session_id=session["id"],
        title=title,
        verdict=verdict,
        accuracy_score=accuracy_score,
        accuracy_assessment=accuracy_assessment,
        summary=summary,
        key_points=key_points,
        corrections=corrections,
        knowledge_detail_data=knowledge_detail_data,
        topic_tags=topic_tags,
        mindmap_data=mindmap_data,
        sources=verified_sources,
        source_label=effective_source_label,
        input_preview=build_input_preview(content),
    )


@router.post("/", response_model=AnalyzeResult)
async def analyze_content(
    request: AnalyzeRequest,
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> AnalyzeResult:
    return await _run_analysis(
        content=request.content,
        language=request.language,
        current_user=current_user,
        supabase=supabase,
        analysis_goal=request.analysis_goal,
    )


@router.post("/upload", response_model=AnalyzeResult)
async def analyze_uploaded_file(
    file: UploadFile = File(...),
    language: str = Form("vi"),
    analysis_goal: str | None = Form(None),
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> AnalyzeResult:
    content, filename = await extract_text_from_upload(file)

    return await _run_analysis(
        content=content,
        language=language,
        current_user=current_user,
        supabase=supabase,
        source_label=filename,
        analysis_goal=analysis_goal,
    )


def _repair_analysis_sections(
    raw_sections: object,
    *,
    fallback_sections: dict[str, dict[str, str]],
    content_blueprint: dict[str, str],
    title: str,
) -> tuple[dict[str, dict[str, str]], list[str]]:
    normalized_sections, active_section_keys = normalize_detailed_sections(
        raw_sections,
        fallback_sections=fallback_sections,
        blueprint=content_blueprint,
        title=title,
    )

    critical_keys = {"core_concept", "mechanism", "components_and_relationships"}
    for key in SECTION_ORDER:
        current_section = normalized_sections.get(key) or {}
        current_content = _normalize_multiline_text(current_section.get("content"))
        minimum_length = 70 if key in critical_keys else 48
        role_is_weak = False
        if key == "core_concept":
            role_is_weak = not (
                _contains_any_marker(current_content, ANALYZE_BOUNDARY_MARKERS)
                or _contains_any_marker(current_content, ANALYZE_EXPLANATORY_MARKERS)
            )
        elif key == "mechanism":
            role_is_weak = not _contains_any_marker(current_content, ANALYZE_MECHANISM_MARKERS)
        elif key == "components_and_relationships":
            role_is_weak = not _contains_any_marker(
                current_content,
                STRUCTURE_ANALYSIS_MARKERS + (" thanh phan ", " vai tro ", " quan he "),
            )
        if (
            len(current_content) < minimum_length
            or (key in critical_keys and _looks_generic_analysis_text(current_content))
            or (key in critical_keys and len(current_content.split()) < 22 and role_is_weak)
            or _contains_trailing_ellipsis(current_content)
        ):
            normalized_sections[key] = dict(
                fallback_sections.get(key)
                or {
                    "title": SECTION_DISPLAY_TITLES[key],
                    "content": build_section_content_from_blueprint(
                        key,
                        title=title,
                        blueprint=content_blueprint,
                    ),
                }
            )

    overlap_pairs = (
        ("core_concept", "mechanism", 0.68),
        ("mechanism", "components_and_relationships", 0.68),
        ("components_and_relationships", "common_misconceptions", 0.72),
    )
    for left_key, right_key, threshold in overlap_pairs:
        left_content = _normalize_multiline_text((normalized_sections.get(left_key) or {}).get("content"))
        right_content = _normalize_multiline_text((normalized_sections.get(right_key) or {}).get("content"))
        if left_content and right_content and semantic_overlap_ratio(left_content, right_content) > threshold:
            normalized_sections[right_key] = {
                "title": SECTION_DISPLAY_TITLES[right_key],
                "content": build_section_content_from_blueprint(
                    right_key,
                    title=title,
                    blueprint=content_blueprint,
                ),
            }

    return normalized_sections, active_section_keys


def _extract_analysis_knowledge_detail_data(
    ai_result: dict[str, Any],
    fallback_result: dict[str, Any],
    *,
    content_blueprint: dict[str, str],
    section_briefs: dict[str, list[str]],
    title: str,
) -> dict[str, Any]:
    fallback_payload = fallback_result.get("knowledge_detail_data") or {}
    normalized_sections, active_section_keys = _repair_analysis_sections(
        ai_result.get("detailed_sections"),
        fallback_sections=fallback_payload.get("detailed_sections") or {},
        content_blueprint=content_blueprint,
        title=title,
    )

    adaptation = ai_result.get("teaching_adaptation")
    fallback_adaptation = fallback_payload.get("teaching_adaptation") or {}
    if not isinstance(adaptation, dict):
        adaptation = {}

    detail_summary = build_summary_from_briefs(
        section_briefs,
        key="detail_focus",
        fallback_text=fallback_payload.get("summary") or "",
    )
    section_bullets = _build_analysis_key_points_from_sections(
        {
            "detailed_sections": normalized_sections,
        }
    )
    if section_bullets and not _analysis_key_points_need_fallback(title, title, section_bullets[:4]):
        detail_summary = "\n".join(f"- {item}" for item in section_bullets[:4])

    return {
        "title": title,
        "summary": detail_summary,
        "content_blueprint": content_blueprint,
        "section_briefs": section_briefs,
        "active_section_keys": active_section_keys,
        "detailed_sections": normalized_sections,
        "teaching_adaptation": {
            "focus_priority": normalize_text(
                str(adaptation.get("focus_priority") or fallback_adaptation.get("focus_priority") or "")
            ),
            "tone": normalize_text(str(adaptation.get("tone") or fallback_adaptation.get("tone") or "")),
            "depth_control": normalize_text(
                str(adaptation.get("depth_control") or fallback_adaptation.get("depth_control") or "")
            ),
            "example_strategy": normalize_text(
                str(adaptation.get("example_strategy") or fallback_adaptation.get("example_strategy") or "")
            ),
        },
    }


def _violates_analysis_plan(ai_result: dict[str, Any], plan: dict[str, Any]) -> bool:
    must_include = [
        normalize_topic_phrase(str(item)) or normalize_text(str(item))
        for item in plan.get("must_include", [])
        if str(item).strip()
    ]
    if not must_include:
        return False

    detailed_sections = ai_result.get("detailed_sections") or {}
    if not isinstance(detailed_sections, dict):
        knowledge_detail = ai_result.get("knowledge_detail_data") or {}
        detailed_sections = knowledge_detail.get("detailed_sections") or {}

    combined = normalize_text(
        " ".join(
            [
                str(ai_result.get("title") or ""),
                str(ai_result.get("summary") or ""),
                " ".join(str(item) for item in ai_result.get("key_points") or []),
                str((detailed_sections.get("core_concept") or {}).get("content") or ""),
                str((detailed_sections.get("mechanism") or {}).get("content") or ""),
                str((detailed_sections.get("components_and_relationships") or {}).get("content") or ""),
            ]
        )
    )
    haystack = strip_accents(combined).lower()

    if plan.get("analysis_kind") == "comparison":
        targets = [strip_accents(item).lower() for item in plan.get("comparison_targets", []) if item]
        if targets and not all(target in haystack for target in targets):
            return True

    covered = sum(1 for item in must_include if strip_accents(item).lower() in haystack)
    return covered < min(2, len(must_include))


def _analysis_result_needs_rewrite(analysis_goal: str, focus_topic: str, ai_result: dict[str, Any]) -> bool:
    title = normalize_text(str(ai_result.get("title") or ""))
    summary = _normalize_multiline_text(ai_result.get("summary"))
    raw_key_points = ai_result.get("key_points")
    key_points = [
        normalize_text(str(item))
        for item in (raw_key_points if isinstance(raw_key_points, list) else [])
        if normalize_text(str(item))
    ]
    sections = ai_result.get("detailed_sections")
    if not title or title.endswith("?"):
        return True
    if not isinstance(sections, dict):
        return True

    analysis_kind = _detect_analysis_kind(analysis_goal)
    core_content = _normalize_multiline_text((sections.get("core_concept") or {}).get("content"))
    mechanism_content = _normalize_multiline_text((sections.get("mechanism") or {}).get("content"))
    relationship_content = _normalize_multiline_text(
        (sections.get("components_and_relationships") or {}).get("content")
    )

    if _analysis_summary_needs_fallback(summary, focus_topic):
        return True
    if len(core_content) < 60 or _looks_generic_analysis_text(core_content):
        return True
    if analysis_kind in {"definition", "comparison", "mechanism", "structure"} and not _is_direct_analysis_answer(
        analysis_goal,
        focus_topic,
        core_content,
    ):
        return True
    if mechanism_content and _looks_generic_analysis_text(mechanism_content):
        return True
    if mechanism_content and not _contains_any_marker(mechanism_content, ANALYZE_MECHANISM_MARKERS):
        return True
    if relationship_content and analysis_kind == "structure" and not _contains_any_marker(
        relationship_content,
        STRUCTURE_ANALYSIS_MARKERS + (" thanh phan ", " vai tro ", " quan he "),
    ):
        return True
    if key_points and _analysis_key_points_need_fallback(analysis_goal, focus_topic, key_points):
        return True

    weak_sections = sum(
        1
        for content in (core_content, mechanism_content, relationship_content)
        if len(content) < 50 or _looks_generic_analysis_text(content) or _contains_trailing_ellipsis(content)
    )
    if weak_sections >= 2:
        return True
    if core_content and mechanism_content and semantic_overlap_ratio(core_content, mechanism_content) > 0.84:
        return True

    compare_subjects = _parse_compare_subjects(analysis_goal)
    if compare_subjects:
        lowered = strip_accents(" ".join([title, core_content, mechanism_content, relationship_content])).lower()
        if not all(strip_accents(subject).lower() in lowered for subject in compare_subjects):
            return True

    if (
        analysis_kind == "structure"
        and _focus_overlap_ratio(relationship_content, focus_topic) < 0.28
    ):
        return True
    if _focus_overlap_ratio(" ".join([summary, core_content, mechanism_content, relationship_content]), focus_topic) < 0.24:
        return True
    return False

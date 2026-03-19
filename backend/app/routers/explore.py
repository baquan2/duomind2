import json
import re
from time import perf_counter
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.models.analysis import ExploreRequest, ExploreResult
from app.services.gemini_service import gemini
from app.services.supabase_service import SupabaseService
from app.utils.fallbacks import build_explore_fallback, build_explore_mindmap
from app.utils.helpers import (
    convert_mind_map_tree_to_flow,
    normalize_text,
    normalize_topic_phrase,
    normalize_topic_tags,
)
from app.utils.prompts import (
    EXPLORE_TOPIC_PROMPT,
    EXPLORE_TOPIC_REWRITE_PROMPT,
    MINDMAP_GENERATE_PROMPT,
)


router = APIRouter()

META_SECTION_OPENINGS = (
    "ở góc nhìn",
    "xét ở",
    "về mặt",
    "điều quan trọng là",
    "phần này",
    "người học nên",
    "hãy hiểu",
    "hãy nắm",
)

GENERIC_SECTION_PHRASES = (
    "là một khối kiến thức",
    "người học",
    "thiên về ứng dụng",
    "thiên về trực quan",
    "bối cảnh người học",
    "dùng một dự án nhỏ",
    "trả lời được ba ý",
    "phần này",
    "persona",
)


SECTION_DISPLAY_TITLES = {
    "core_concept": "Khái niệm cốt lõi",
    "mechanism": "Bản chất / cơ chế hoạt động",
    "components_and_relationships": "Các thành phần chính và quan hệ giữa chúng",
    "persona_based_example": "Ví dụ trực quan dễ hiểu",
    "real_world_applications": "Ứng dụng thực tế",
    "common_misconceptions": "Nhầm lẫn phổ biến",
    "next_step_self_study": "Cách tự học tiếp trong 1 buổi ngắn",
}

EXPLORE_HARD_GUARDRAILS = """
ADDITIONAL HARD RULES:
- Treat the user's input as a request for a real explanation, not a coaching exercise.
- Answer the topic directly with factual content, then organize the explanation into sections.
- Never describe the topic as "a block of knowledge", "an important concept", or "something the learner should understand".
- Never repeat the raw user question in every section.
- The example section must contain an actual example or scenario, not advice about choosing an example.
- If the user asks for a simple explanation, write in short, concrete sentences with real-world analogies.
- Each section must add new information. Do not restate the same idea with different wording.
"""


def _normalize_key_points(raw_points: object) -> list[str]:
    if not isinstance(raw_points, list):
        return []
    return [normalize_text(str(point)) for point in raw_points if normalize_text(str(point))][:5]


def _normalize_multiline_text(text: object) -> str:
    if not isinstance(text, str):
        return ""
    lines = [normalize_text(line) for line in text.splitlines() if normalize_text(line)]
    return "\n".join(lines).strip()


def _extract_sentences(text: str, limit: int = 2) -> list[str]:
    return [
        normalize_text(part)
        for part in re.split(r"(?<=[.!?])\s+|\n+", text)
        if normalize_text(part)
    ][:limit]


def _extract_summary_bullets(summary: str) -> list[str]:
    return [
        normalize_text(line.lstrip("-*• ").strip())
        for line in summary.splitlines()
        if normalize_text(line.lstrip("-*• ").strip())
    ]


def _has_vietnamese_diacritics(text: str) -> bool:
    return any(
        char in text
        for char in "ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ"
    )


def _resolve_display_title(raw_title: object, prompt: str) -> str:
    prompt_title = normalize_topic_phrase(prompt).strip(" .")
    normalized_title = normalize_topic_phrase(str(raw_title or "")).strip(" .")

    if not normalized_title:
        return prompt_title or "Khám phá chủ đề"

    if _has_vietnamese_diacritics(prompt_title) and not _has_vietnamese_diacritics(normalized_title):
        return prompt_title

    return normalized_title


def _normalize_topic_tag_list(raw_tags: object, source_text: str) -> list[str]:
    tags = normalize_topic_tags(raw_tags, source_text)
    return [normalize_topic_phrase(tag) for tag in tags if normalize_topic_phrase(tag)]


def _looks_like_meta_key_point(point: str) -> bool:
    lowered = normalize_text(point).lower()
    return any(
        phrase in lowered
        for phrase in [
            "hiểu ",
            "nắm ",
            "biết cách",
            "xác định",
            "người học",
            "hãy",
            "cần được hiểu",
        ]
    )


def _looks_like_meta_section(text: str) -> bool:
    lowered = normalize_text(text).lower()
    if not lowered:
        return True
    return any(lowered.startswith(prefix) for prefix in META_SECTION_OPENINGS)


def _looks_like_generic_section(text: str) -> bool:
    lowered = normalize_text(text).lower()
    if not lowered:
        return True
    if _looks_like_meta_section(lowered):
        return True
    generic_hits = sum(1 for phrase in GENERIC_SECTION_PHRASES if phrase in lowered)
    return generic_hits >= 2


def _raw_explore_result_needs_rewrite(prompt: str, ai_result: dict[str, Any]) -> bool:
    raw_title = normalize_text(str(ai_result.get("title") or ""))
    if not raw_title:
        return True

    normalized_title = normalize_topic_phrase(raw_title).lower()
    if any(token in normalized_title for token in ["giải thích", "ví dụ", "đơn giản", "cơ bản", "tổng quan"]):
        return True

    detailed_sections = ai_result.get("detailed_sections")
    if not isinstance(detailed_sections, dict):
        return True

    generic_sections = 0
    for section in detailed_sections.values():
        if not isinstance(section, dict):
            generic_sections += 1
            continue
        content = normalize_text(str(section.get("content") or ""))
        if (
            len(content) < 110
            or _looks_like_generic_section(content)
            or normalize_topic_phrase(prompt).lower() in content.lower()
        ):
            generic_sections += 1

    prompt_topic = normalize_topic_phrase(prompt).lower()
    if prompt_topic and prompt_topic in raw_title.lower() and "?" in str(ai_result.get("title") or ""):
        return True

    if "?" in raw_title:
        return True

    return generic_sections >= 2


def _build_direct_section_fallback(title: str, section_key: str) -> str:
    direct_sections = {
        "core_concept": (
            f"{title} là một khối kiến thức xác định rõ bản chất, phạm vi áp dụng và giá trị của chủ đề. "
            "Muốn hiểu đúng phần này, cần trả lời được ba ý: nó là gì, dùng trong trường hợp nào, và khác gì với khái niệm gần nó. "
            "Khi làm rõ ba điểm đó, người học sẽ nắm được nền tảng thay vì chỉ nhớ một định nghĩa ngắn."
        ),
        "mechanism": (
            f"Cơ chế của {title} được hiểu qua chuỗi logic từ đầu vào, cách xử lý, đến kết quả đầu ra. "
            "Điểm quan trọng không phải là nhớ từng bước rời rạc mà là thấy được vì sao bước trước dẫn tới bước sau. "
            "Khi nắm được logic vận hành, người học có thể tự suy luận ở tình huống mới thay vì phụ thuộc vào ví dụ mẫu."
        ),
        "components_and_relationships": (
            f"{title} thường gồm nhiều thành phần có vai trò riêng, nhưng ý nghĩa thật sự chỉ xuất hiện khi nhìn được mối liên hệ giữa chúng. "
            "Vì vậy, người học cần hiểu từng phần làm gì, phần nào giữ vai trò trung tâm, và sự thay đổi ở một phần sẽ ảnh hưởng ra sao tới phần còn lại. "
            "Nhìn theo cấu trúc như vậy giúp kiến thức bớt rời rạc và dễ áp dụng hơn."
        ),
        "persona_based_example": (
            f"Ví dụ về {title} nên được đặt trong bối cảnh học tập hoặc công việc gần với người học để dễ hình dung. "
            "Nếu người học thiên về ứng dụng, nên liên hệ tới một nhiệm vụ thực tế, một quy trình quen thuộc hoặc một bài toán cụ thể. "
            "Ví dụ càng sát bối cảnh cá nhân thì việc ghi nhớ và chuyển hóa thành hành động càng nhanh."
        ),
        "real_world_applications": (
            f"{title} có giá trị khi nó giúp giải thích một quyết định, cải thiện một quy trình hoặc hỗ trợ giải quyết một tình huống thực tế. "
            "Người học nên thấy rõ chủ đề này xuất hiện ở đâu trong học tập, trong công việc và trong việc đánh giá kết quả. "
            "Khi nhìn được điểm chạm thực tế, kiến thức sẽ bớt trừu tượng và dễ dùng hơn."
        ),
        "common_misconceptions": (
            f"Nhầm lẫn phổ biến với {title} thường đến từ việc nhớ ví dụ nhưng chưa hiểu bản chất hoặc đánh đồng nó với khái niệm gần giống. "
            "Cách sửa là quay lại cơ chế cốt lõi, kiểm tra điều kiện áp dụng và phân biệt rõ khi nào kết luận này còn đúng, khi nào không. "
            "Làm rõ giới hạn của chủ đề giúp người học tránh áp dụng sai trong thực tế."
        ),
        "next_step_self_study": (
            f"Để học tiếp {title} trong một buổi ngắn, hãy chia thời gian thành ba phần: đọc lại khái niệm cốt lõi, tự giải thích cơ chế bằng lời của mình, rồi làm một ví dụ nhỏ. "
            "Sau đó, ghi lại vài ý chính vừa hiểu rõ hơn và một điểm còn mơ hồ để đào sâu ở buổi sau. "
            "Cách học ngắn nhưng có cấu trúc này giúp kiến thức bền hơn nhiều so với chỉ đọc lướt."
        ),
    }
    return direct_sections.get(section_key, f"{title} cần được giải thích bằng nội dung trực tiếp, rõ ý và có thể áp dụng.")


def _build_direct_knowledge_section(title: str, section_key: str) -> str:
    direct_sections = {
        "core_concept": (
            f"{title} cần được hiểu bằng ý nghĩa thật của nó: nó là gì, dùng để mô tả điều gì và khác gì với khái niệm gần giống. "
            "Nếu không làm rõ ba điểm này, người đọc rất dễ nhớ nhầm một định nghĩa ngắn rồi áp sai trong thực tế. "
            "Vì vậy phần cốt lõi luôn phải trả lời thẳng vào bản chất của chủ đề trước khi đi sang ví dụ hay ứng dụng."
        ),
        "mechanism": (
            f"Cơ chế của {title} nên được nhìn như một chuỗi nguyên nhân và kết quả, tức là điều gì diễn ra trước, điều gì diễn ra sau và vì sao kết quả cuối cùng lại xuất hiện. "
            "Khi hiểu được logic này, người đọc sẽ không còn phụ thuộc vào một ví dụ mẫu duy nhất mà có thể tự liên hệ sang các trường hợp tương tự. "
            "Đây là phần giúp biến việc ghi nhớ thành hiểu thực sự."
        ),
        "components_and_relationships": (
            f"{title} thường gồm nhiều yếu tố liên kết với nhau chứ không đứng riêng lẻ. "
            "Muốn nắm chắc chủ đề, cần chỉ ra từng thành phần giữ vai trò gì, thành phần nào là trung tâm và sự thay đổi ở một phần sẽ kéo theo phần khác ra sao. "
            "Nhìn được mối quan hệ này sẽ làm kiến thức mạch lạc hơn rất nhiều."
        ),
        "persona_based_example": (
            f"Một ví dụ dễ hiểu về {title} nên đặt trong tình huống đời thường, nơi có thể thấy rõ ai tham gia, điều gì xảy ra và kết quả cuối cùng là gì. "
            "Ví dụ tốt không cần quá kỹ thuật; chỉ cần đủ cụ thể để người đọc hình dung được cơ chế đang vận hành ngoài đời ra sao. "
            "Nhờ vậy phần giải thích sẽ bớt trừu tượng và dễ nhớ hơn."
        ),
        "real_world_applications": (
            f"{title} có giá trị khi nó giúp giải thích, dự đoán hoặc cải thiện một việc cụ thể trong thực tế. "
            "Phần ứng dụng cần chỉ ra chủ đề này xuất hiện ở đâu trong công việc, đời sống, hệ thống vận hành hoặc quá trình ra quyết định. "
            "Khi nhìn thấy điểm chạm thực tế, người đọc sẽ hiểu vì sao kiến thức này đáng học."
        ),
        "common_misconceptions": (
            f"Hiểu nhầm về {title} thường đến từ việc nhớ ví dụ nhưng không hiểu bản chất, hoặc đánh đồng nó với một khái niệm gần giống. "
            "Cách sửa là quay lại logic cốt lõi, kiểm tra điều kiện áp dụng và chỉ ra rõ trường hợp nào kết luận đó còn đúng, trường hợp nào không còn đúng nữa. "
            "Làm rõ giới hạn của chủ đề sẽ giúp tránh áp dụng sai."
        ),
        "next_step_self_study": (
            f"Để học tiếp {title}, hãy ôn lại định nghĩa cốt lõi, tự tóm tắt cơ chế vận hành bằng lời của mình và thử áp nó vào một ví dụ nhỏ. "
            "Chỉ cần đủ ba bước đó trong một buổi ngắn là đã chuyển từ đọc hiểu sang hiểu thật. "
            "Nếu còn một điểm chưa rõ, hãy đào sâu đúng điểm đó ở buổi sau."
        ),
    }
    return direct_sections.get(
        section_key,
        f"{title} cần được giải thích bằng nội dung trực tiếp, rõ ý và có thể áp dụng.",
    )


def _build_theory_key_points_from_sections(
    knowledge_detail_data: dict[str, Any],
) -> list[str]:
    detailed_sections = knowledge_detail_data.get("detailed_sections") or {}
    ordered_keys = [
        "core_concept",
        "mechanism",
        "components_and_relationships",
        "real_world_applications",
        "common_misconceptions",
    ]

    key_points: list[str] = []
    for key in ordered_keys:
        section = detailed_sections.get(key) or {}
        content = normalize_text(str(section.get("content") or ""))
        sentences = _extract_sentences(content, 2)
        if not sentences:
            continue
        candidate = sentences[0]
        if candidate not in key_points:
            key_points.append(candidate)
        if len(key_points) >= 5:
            break

    return key_points[:5]


def _build_summary_from_sections(knowledge_detail_data: dict[str, Any]) -> str:
    detailed_sections = knowledge_detail_data.get("detailed_sections") or {}
    ordered_keys = [
        "core_concept",
        "mechanism",
        "components_and_relationships",
        "real_world_applications",
    ]

    bullets: list[str] = []
    for key in ordered_keys:
        content = normalize_text(str((detailed_sections.get(key) or {}).get("content") or ""))
        sentences = _extract_sentences(content, 1)
        if not sentences:
            continue
        bullet = sentences[0].lstrip("-*• ").strip()
        if bullet and bullet not in bullets:
            bullets.append(f"- {bullet}")
        if len(bullets) >= 4:
            break

    return "\n".join(bullets[:4])


def _looks_like_generic_summary(summary: str) -> bool:
    lowered = normalize_text(summary).lower()
    if not lowered:
        return True

    meta_hits = sum(
        1
        for phrase in [
            "người học",
            "hãy",
            "phần này",
            "khối kiến thức",
            "điều quan trọng",
            "ở góc nhìn",
        ]
        if phrase in lowered
    )
    return meta_hits >= 2


def _summary_and_keypoints_overlap(summary: str, key_points: list[str]) -> bool:
    summary_bullets = _extract_summary_bullets(summary)
    if not summary_bullets or not key_points:
        return False

    overlap_count = 0
    for key_point in key_points:
        normalized_key_point = normalize_text(key_point).lower()
        if any(normalized_key_point == normalize_text(bullet).lower() for bullet in summary_bullets):
            overlap_count += 1

    return overlap_count >= max(2, min(len(key_points), len(summary_bullets)) - 1)


def _build_fallback_knowledge_payload(title: str, ai_result: dict[str, Any]) -> dict[str, Any]:
    fallback_payload = build_explore_fallback(title)
    fallback_payload["title"] = title

    incoming_summary = _normalize_multiline_text(ai_result.get("summary"))
    if incoming_summary:
        fallback_payload["summary"] = incoming_summary

    incoming_key_points = _normalize_key_points(ai_result.get("key_points"))
    if incoming_key_points:
        fallback_payload["key_points"] = incoming_key_points

    return fallback_payload


def _extract_knowledge_detail_data(
    ai_result: dict[str, Any],
    title: str,
    summary: str,
    key_points: list[str],
) -> dict[str, Any]:
    fallback_payload = _build_fallback_knowledge_payload(title, ai_result)
    fallback_sections = fallback_payload["detailed_sections"]
    detailed_sections = ai_result.get("detailed_sections")
    teaching_adaptation = ai_result.get("teaching_adaptation")

    if not isinstance(detailed_sections, dict):
        for section_key, section_data in fallback_sections.items():
            section_data["content"] = _build_direct_knowledge_section(title, section_key)
            section_data["title"] = SECTION_DISPLAY_TITLES.get(section_key, section_data["title"])
        return {
            "title": title,
            "summary": summary or fallback_payload["summary"],
            "detailed_sections": fallback_sections,
            "teaching_adaptation": fallback_payload["teaching_adaptation"],
        }

    normalized_sections: dict[str, dict[str, str]] = {}
    for key, fallback_section in fallback_sections.items():
        raw_section = detailed_sections.get(key)
        cleaned_content = ""

        if isinstance(raw_section, dict):
            content = str(raw_section.get("content") or "")
            cleaned_content = "\n".join(_extract_sentences(content, 6))

        if (
            len(cleaned_content) < 140
            or _looks_like_meta_section(cleaned_content)
            or _looks_like_generic_section(cleaned_content)
        ):
            cleaned_content = _build_direct_knowledge_section(title, key)

        normalized_sections[key] = {
            "title": SECTION_DISPLAY_TITLES.get(
                key,
                normalize_text(str((raw_section or {}).get("title") or fallback_section["title"])),
            ),
            "content": cleaned_content,
        }

    if not isinstance(teaching_adaptation, dict):
        teaching_adaptation = fallback_payload["teaching_adaptation"]

    return {
        "title": title,
        "summary": summary or fallback_payload["summary"],
        "detailed_sections": normalized_sections,
        "teaching_adaptation": {
            "focus_priority": normalize_text(
                str(
                    teaching_adaptation.get("focus_priority")
                    or fallback_payload["teaching_adaptation"]["focus_priority"]
                )
            ),
            "tone": normalize_text(
                str(teaching_adaptation.get("tone") or fallback_payload["teaching_adaptation"]["tone"])
            ),
            "depth_control": normalize_text(
                str(
                    teaching_adaptation.get("depth_control")
                    or fallback_payload["teaching_adaptation"]["depth_control"]
                )
            ),
            "example_strategy": normalize_text(
                str(
                    teaching_adaptation.get("example_strategy")
                    or fallback_payload["teaching_adaptation"]["example_strategy"]
                )
            ),
        },
    }


def _finalize_summary_and_key_points(
    summary: str,
    key_points: list[str],
    knowledge_detail_data: dict[str, Any],
) -> tuple[str, list[str]]:
    summary_bullets = _extract_summary_bullets(summary)
    if not summary_bullets or _looks_like_generic_summary(summary):
        rebuilt_summary = _build_summary_from_sections(knowledge_detail_data)
        summary = rebuilt_summary or knowledge_detail_data.get("summary", "")

    rebuilt_key_points = _build_theory_key_points_from_sections(knowledge_detail_data)
    should_rebuild = (
        not key_points
        or _summary_and_keypoints_overlap(summary, key_points)
        or sum(1 for item in key_points if _looks_like_meta_key_point(item)) >= max(2, len(key_points) // 2)
    )

    if should_rebuild and rebuilt_key_points:
        key_points = rebuilt_key_points

    return summary, key_points[:5]


@router.post("/", response_model=ExploreResult)
async def explore_topic(
    request: ExploreRequest,
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> ExploreResult:
    svc = SupabaseService(supabase)
    start_time = perf_counter()
    svc.ensure_profile(
        current_user["id"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        avatar_url=current_user.get("avatar_url"),
    )

    try:
        ai_result = await gemini.generate_json(
            (EXPLORE_TOPIC_PROMPT + "\n\n" + EXPLORE_HARD_GUARDRAILS).format(
                prompt=request.prompt,
            )
        )
        if _raw_explore_result_needs_rewrite(request.prompt, ai_result):
            try:
                ai_result = await gemini.generate_json(
                    (EXPLORE_TOPIC_REWRITE_PROMPT + "\n\n" + EXPLORE_HARD_GUARDRAILS).format(
                        prompt=request.prompt,
                        draft_json=json.dumps(ai_result, ensure_ascii=False),
                    )
                )
            except Exception as exc:
                print(f"[explore] Topic rewrite failed, keeping original draft: {exc}")
    except Exception as exc:
        print(f"[explore] Topic exploration failed, using fallback: {exc}")
        ai_result = build_explore_fallback(request.prompt)

    title = _resolve_display_title(ai_result.get("title"), request.prompt)
    summary = _normalize_multiline_text(ai_result.get("summary"))
    key_points = _normalize_key_points(ai_result.get("key_points"))
    knowledge_detail_data = _extract_knowledge_detail_data(ai_result, title, summary, key_points)
    summary, key_points = _finalize_summary_and_key_points(summary, key_points, knowledge_detail_data)

    topic_tags = _normalize_topic_tag_list(ai_result.get("topic_tags"), request.prompt or title)
    if not topic_tags:
        topic_tags = _normalize_topic_tag_list(title, title)

    try:
        raw_mindmap_data = await gemini.generate_json(
            MINDMAP_GENERATE_PROMPT.format(
                topic=title,
            )
        )
        mindmap_data = convert_mind_map_tree_to_flow(raw_mindmap_data)
        if not mindmap_data.get("nodes"):
            raise ValueError("Mind map tree conversion returned no nodes")
    except Exception as exc:
        print(f"[explore] Mind map generation failed, using fallback: {exc}")
        mindmap_data = build_explore_mindmap(title, knowledge_detail_data)

    session = svc.create_session(
        current_user["id"],
        {
            "session_type": "explore",
            "title": title,
            "user_input": request.prompt,
            "topic_tags": topic_tags,
            "summary": summary,
            "key_points": key_points,
            "infographic_data": knowledge_detail_data,
            "mindmap_data": mindmap_data,
            "language": request.language,
            "duration_ms": int((perf_counter() - start_time) * 1000),
        },
    )
    if not session or not session.get("id"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lưu phiên khám phá.",
        )

    return ExploreResult(
        session_id=session["id"],
        title=title,
        summary=summary,
        key_points=key_points,
        knowledge_detail_data=knowledge_detail_data,
        topic_tags=topic_tags,
        mindmap_data=mindmap_data,
    )

from typing import Any, Iterable, Mapping

from app.utils.content_blueprint import (
    SECTION_ORDER,
    build_key_points_from_briefs,
    build_summary_from_briefs,
    bullet_text_to_list,
)
from app.utils.helpers import normalize_text


SECTION_DISPLAY_TITLES = {
    "core_concept": "Khái niệm cốt lõi",
    "mechanism": "Bản chất / cơ chế hoạt động",
    "components_and_relationships": "Các thành phần chính và quan hệ giữa chúng",
    "persona_based_example": "Ví dụ trực quan",
    "real_world_applications": "Ứng dụng thực tế",
    "common_misconceptions": "Nhầm lẫn phổ biến",
    "next_step_self_study": "Điểm cần nắm tiếp",
}

DEFAULT_SUMMARY_SECTION_KEYS = (
    "core_concept",
    "mechanism",
    "components_and_relationships",
    "real_world_applications",
)

DEFAULT_KEY_POINT_SECTION_KEYS = (
    "core_concept",
    "mechanism",
    "components_and_relationships",
    "common_misconceptions",
    "real_world_applications",
)


def normalize_multiline_text(text: object) -> str:
    if not isinstance(text, str):
        return ""
    lines = [normalize_text(line) for line in text.splitlines() if normalize_text(line)]
    return "\n".join(lines).strip()


def extract_sentences(text: str, limit: int = 2) -> list[str]:
    normalized = normalize_multiline_text(text)
    parts = [normalize_text(part) for part in normalized.replace("\n", ". ").split(". ") if normalize_text(part)]
    return parts[:limit]


def _fallback_bullets_from_sections(
    knowledge_detail_data: Mapping[str, Any],
    *,
    section_keys: Iterable[str],
    limit: int,
) -> list[str]:
    bullets: list[str] = []
    sections = knowledge_detail_data.get("detailed_sections") or {}
    for key in section_keys:
        content = normalize_text(str((sections.get(key) or {}).get("content") or ""))
        sentences = extract_sentences(content, 1)
        if not sentences:
            continue
        bullet = sentences[0]
        if bullet in bullets:
            continue
        bullets.append(bullet)
        if len(bullets) >= limit:
            break
    return bullets[:limit]


def build_summary_from_sections(
    knowledge_detail_data: Mapping[str, Any],
    *,
    section_keys: Iterable[str] = DEFAULT_SUMMARY_SECTION_KEYS,
    limit: int = 4,
) -> str:
    section_briefs = knowledge_detail_data.get("section_briefs") or {}
    summary = build_summary_from_briefs(
        section_briefs,
        key="overview",
        fallback_text=knowledge_detail_data.get("summary") or "",
        limit=limit,
    )
    if summary:
        return summary
    return "\n".join(
        f"- {item}" for item in _fallback_bullets_from_sections(
            knowledge_detail_data,
            section_keys=section_keys,
            limit=limit,
        )
    )


def build_key_points_from_sections(
    knowledge_detail_data: Mapping[str, Any],
    *,
    section_keys: Iterable[str] = DEFAULT_KEY_POINT_SECTION_KEYS,
    limit: int = 5,
) -> list[str]:
    section_briefs = knowledge_detail_data.get("section_briefs") or {}
    points = build_key_points_from_briefs(
        section_briefs,
        bullet_text_to_list(knowledge_detail_data.get("key_points"), limit=limit),
        limit=limit,
    )
    if points:
        return points[:limit]
    return _fallback_bullets_from_sections(
        knowledge_detail_data,
        section_keys=section_keys,
        limit=limit,
    )

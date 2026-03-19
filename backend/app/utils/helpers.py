import json
import math
import re
import unicodedata
from typing import Any


SOURCE_PREFIX = "[DUOMIND_SOURCE]"

KEYWORD_STOP_WORDS = {
    "va",
    "voi",
    "cua",
    "cho",
    "la",
    "mot",
    "nhung",
    "trong",
    "khi",
    "the",
    "hay",
    "ban",
    "nguoi",
    "duoc",
    "noi",
    "nay",
    "gi",
    "don",
    "gian",
    "giai",
    "thich",
    "co",
    "ban",
    "tong",
    "quan",
    "vi",
    "du",
}

KEYWORD_FILLER_PHRASES = [
    "la gi",
    "hoat dong nhu the nao",
    "nhu the nao",
    "ra sao",
    "giai thich don gian",
    "giai thich",
    "don gian",
    "co ban",
    "tong quan",
    "vi du",
]


def safe_parse_json(text: str) -> dict:
    """Parse JSON safely and strip markdown code fences if present."""
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse AI response as JSON: {exc}\nResponse: {text[:200]}"
        ) from exc


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def truncate_content(content: str, max_chars: int = 8000) -> str:
    """Trim long content so it stays within the model context budget."""
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "\n...[Nội dung đã được rút gọn]"


def build_stored_user_input(content: str, source_label: str | None = None) -> str:
    if not source_label:
        return content
    return f"{SOURCE_PREFIX} {source_label}\n\n{content}"


def extract_source_label(stored_input: str | None) -> str | None:
    if not stored_input:
        return None

    first_line, _, _ = stored_input.partition("\n")
    if not first_line.startswith(SOURCE_PREFIX):
        return None

    source_label = first_line.removeprefix(SOURCE_PREFIX).strip()
    return source_label or None


def strip_source_label(stored_input: str | None) -> str:
    if not stored_input:
        return ""

    if not stored_input.startswith(SOURCE_PREFIX):
        return stored_input

    _, _, content = stored_input.partition("\n\n")
    return content or ""


def build_input_preview(content: str, max_chars: int = 180) -> str:
    normalized = normalize_text(content)
    if len(normalized) <= max_chars:
        return normalized
    return normalized[:max_chars].rstrip(" ,.;:") + "..."


def clean_keyword(text: str) -> str:
    cleaned = normalize_text(text)
    cleaned = re.sub(r"[#*_`~\[\]{}()<>]+", " ", cleaned)
    cleaned = re.sub(r"\s*[:|/,-]\s*", " ", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" .,:;-")
    tokens = re.findall(r"[0-9A-Za-zÀ-ỹĐđ]+", cleaned, flags=re.UNICODE)
    parts: list[str] = []

    for token in tokens:
        lowered = strip_accents(token).lower()
        if lowered in KEYWORD_STOP_WORDS or lowered.isdigit():
            continue
        if lowered in {"la", "gi", "nhu", "the", "nao", "tong", "quan"}:
            continue
        parts.append(token.lower())
        if len(parts) >= 4:
            break

    return " ".join(parts).strip()


def extract_keywords_from_text(text: str, limit: int = 4) -> list[str]:
    normalized = normalize_text(text)
    words = re.findall(r"[0-9A-Za-zÀ-ỹĐđ]{4,}", normalized, flags=re.UNICODE)
    keywords: list[str] = []

    for word in words:
        normalized_word = strip_accents(word).lower()
        if normalized_word in KEYWORD_STOP_WORDS or normalized_word.isdigit():
            continue
        word_with_case = word.lower()
        if word_with_case not in keywords:
            keywords.append(word_with_case)
        if len(keywords) >= limit:
            break

    return keywords


QUESTION_SUFFIX_PATTERNS = [
    r"\b(là gì|la gi)\b",
    r"\b(hoạt động như thế nào|hoat dong nhu the nao)\b",
    r"\b(vận hành ra sao|van hanh ra sao)\b",
    r"\b(vận hành như thế nào|van hanh nhu the nao)\b",
    r"\b(ra sao)\b",
    r"\b(như thế nào|nhu the nao)\b",
    r"\b(thế nào|the nao)\b",
]


def normalize_topic_phrase(text: str) -> str:
    cleaned = normalize_text(text).strip(" .?!,:;-")
    cleaned = re.sub(
        r"^(giải thích|giai thich|cho tôi biết|cho toi biet|nói về|noi ve|phân tích|phan tich|tìm hiểu|tim hieu)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip(" .?!,:;-")
    for pattern in QUESTION_SUFFIX_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip(" .?!,:;-")
    cleaned = re.sub(
        r"\b(ví dụ thực tế|vi du thuc te|ví dụ|vi du|đơn giản|don gian|cơ bản|co ban|tổng quan|tong quan)\b",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip(" .?!,:;-")
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" .?!,:;-")
    return cleaned or normalize_text(text).strip(" .?!,:;-")


def sentence_case(text: str) -> str:
    normalized = normalize_text(text)
    if not normalized:
        return normalized
    return normalized[0].upper() + normalized[1:]


def shorten_phrase(text: str, max_words: int = 6, max_chars: int = 48) -> str:
    normalized = normalize_text(text)
    if len(normalized) <= max_chars:
        return normalized

    first_clause = re.split(r"[:;,.]", normalized, maxsplit=1)[0].strip()
    if 0 < len(first_clause) <= max_chars:
        normalized = first_clause

    words = normalized.split()
    shortened = " ".join(words[:max_words]).strip()
    if len(shortened) > max_chars:
        shortened = shortened[:max_chars].rstrip(" ,.;:")
    return shortened or normalized[:max_chars].rstrip(" ,.;:")


def normalize_topic_tags(
    raw_tags: object,
    source_text: str,
    limit: int = 4,
) -> list[str]:
    candidates: list[str] = []

    if isinstance(raw_tags, list):
        for item in raw_tags:
            if isinstance(item, str):
                candidates.extend(re.split(r"[,|/]", item))
    elif isinstance(raw_tags, str):
        candidates.extend(re.split(r"[,|/]", raw_tags))

    normalized: list[str] = []
    seen: set[str] = set()

    for candidate in candidates:
        keyword = clean_keyword(candidate)
        if len(keyword) < 2:
            continue

        lowered = keyword.lower()
        if lowered in seen:
            continue

        seen.add(lowered)
        normalized.append(keyword)
        if len(normalized) >= limit:
            return normalized

    if normalized:
        return normalized[:limit]

    topic_phrase = sentence_case(normalize_topic_phrase(source_text))
    fallback_tags: list[str] = []
    if topic_phrase:
        fallback_tags.append(topic_phrase)

    keyword_tags = [
        sentence_case(keyword)
        for keyword in extract_keywords_from_text(source_text, max(0, limit - len(fallback_tags)))
        if sentence_case(keyword) != topic_phrase
    ]
    fallback_tags.extend(keyword_tags)
    return fallback_tags[:limit]


def build_learner_profile(data: dict[str, Any]) -> str:
    lines = [
        f"- Age range: {data.get('age_range') or 'unknown'}",
        f"- Status: {data.get('status') or 'unknown'}",
        f"- Education level: {data.get('education_level') or 'unknown'}",
        f"- Major: {data.get('major') or 'unknown'}",
        f"- School: {data.get('school_name') or 'unknown'}",
        f"- Industry: {data.get('industry') or 'unknown'}",
        f"- Job title: {data.get('job_title') or 'unknown'}",
        f"- Years of experience: {data.get('years_experience') or 0}",
        f"- Learning goals: {', '.join(data.get('learning_goals') or []) or 'unknown'}",
        f"- Topics of interest: {', '.join(data.get('topics_of_interest') or []) or 'unknown'}",
        f"- Learning style: {data.get('learning_style') or 'mixed'}",
        f"- Daily study minutes: {data.get('daily_study_minutes') or 30}",
    ]
    return "\n".join(lines)


def _infer_difficulty_level(onboarding_data: dict[str, Any]) -> str:
    if onboarding_data.get("education_level") in {"high_school", "college"}:
        return "beginner"
    if onboarding_data.get("education_level") in {"university", "postgrad"}:
        return "intermediate"
    if (onboarding_data.get("years_experience") or 0) >= 5:
        return "advanced"
    return "intermediate"


def _build_background_context(onboarding_data: dict[str, Any]) -> str:
    parts = []
    status = onboarding_data.get("status")
    if status == "student":
        parts.append("người học thiên về bối cảnh học tập")
    elif status == "working":
        parts.append("người học thiên về bối cảnh công việc")
    elif status == "both":
        parts.append("người học vừa học vừa làm")

    if onboarding_data.get("major"):
        parts.append(f"chuyên ngành {onboarding_data['major']}")
    if onboarding_data.get("industry"):
        parts.append(f"ngành {onboarding_data['industry']}")
    if onboarding_data.get("job_title"):
        parts.append(f"vai trò {onboarding_data['job_title']}")
    if onboarding_data.get("education_level"):
        parts.append(f"trình độ {onboarding_data['education_level']}")

    return ", ".join(parts) or "người học phổ thông cần định hướng rõ ràng"


def _infer_busyness_level(daily_study_minutes: int, status: str | None) -> str:
    if daily_study_minutes <= 20:
        return "cao"
    if status == "both" and daily_study_minutes <= 45:
        return "cao"
    if daily_study_minutes <= 45:
        return "trung bình"
    return "thấp"


def _infer_example_need(
    learning_style: str,
    status: str | None,
    learning_goals: list[str],
) -> str:
    practical_goals = {"career", "skill", "application", "problem_solving"}
    if learning_style in {"visual", "practice"}:
        return "cao"
    if status in {"working", "both"}:
        return "cao"
    if any(goal in practical_goals for goal in learning_goals):
        return "cao"
    return "trung bình"


def _derive_study_pacing(daily_study_minutes: int) -> str:
    if daily_study_minutes <= 20:
        return "nhanh, ưu tiên trọng tâm trước"
    if daily_study_minutes <= 45:
        return "vừa phải, đi từ cốt lõi đến ứng dụng"
    return "thoải mái, có thể đào sâu theo từng lớp"


def _derive_content_depth(difficulty_level: str, daily_study_minutes: int) -> str:
    if difficulty_level == "advanced" and daily_study_minutes >= 45:
        return "sâu, có trade-off và liên hệ hệ thống"
    if difficulty_level == "beginner" or daily_study_minutes <= 20:
        return "gọn, ưu tiên hiểu bản chất trước"
    return "trung bình, cân bằng giữa khái niệm và ứng dụng"


def get_user_context(onboarding_data: dict | None) -> dict[str, Any]:
    """Extract rich prompt context from onboarding data without requiring schema changes."""
    if not onboarding_data:
        return {
            "user_persona": "general_learner",
            "user_persona_description": "Người học cần lời giải thích rõ ràng, thực dụng và dễ theo dõi.",
            "difficulty_level": "intermediate",
            "learning_goals": "general_knowledge",
            "learning_style": "mixed",
            "daily_study_minutes": 30,
            "background_context": "người học phổ thông cần định hướng rõ ràng",
            "busyness_level": "trung bình",
            "practical_example_need": "trung bình",
            "study_pacing": "vừa phải, đi từ cốt lõi đến ứng dụng",
            "content_depth": "trung bình, cân bằng giữa khái niệm và ứng dụng",
        }

    learning_goals = onboarding_data.get("learning_goals", []) or []
    learning_style = onboarding_data.get("learning_style") or "mixed"
    daily_study_minutes = int(onboarding_data.get("daily_study_minutes") or 30)
    difficulty_level = _infer_difficulty_level(onboarding_data)

    return {
        "user_persona": onboarding_data.get("ai_persona", "general_learner"),
        "user_persona_description": onboarding_data.get(
            "ai_persona_description",
            "Người học cần lời giải thích rõ ràng, thực dụng và dễ theo dõi.",
        ),
        "difficulty_level": difficulty_level,
        "learning_goals": ", ".join(learning_goals) or "general_knowledge",
        "learning_style": learning_style,
        "daily_study_minutes": daily_study_minutes,
        "background_context": _build_background_context(onboarding_data),
        "busyness_level": _infer_busyness_level(daily_study_minutes, onboarding_data.get("status")),
        "practical_example_need": _infer_example_need(
            learning_style, onboarding_data.get("status"), learning_goals
        ),
        "study_pacing": _derive_study_pacing(daily_study_minutes),
        "content_depth": _derive_content_depth(difficulty_level, daily_study_minutes),
    }


def _node_payload(item: dict[str, Any], fallback_label: str) -> dict[str, Any]:
    label = normalize_text(str(item.get("label") or fallback_label))[:48] or fallback_label
    full_label = normalize_text(str(item.get("full_label") or label)) or label
    description = normalize_text(str(item.get("description") or f"Nội dung về {label.lower()}"))
    details = normalize_text(str(item.get("details") or description))
    return {
        "label": label,
        "full_label": full_label,
        "description": description,
        "details": details,
    }


def convert_mind_map_tree_to_flow(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Convert nested tree JSON into React Flow nodes/edges.
    If payload already contains nodes/edges, return it as-is.
    """
    if payload.get("nodes") and payload.get("edges"):
        return payload

    root = payload.get("mind_map")
    if not isinstance(root, dict):
        return {"nodes": [], "edges": []}

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    root_data = _node_payload(root, str(payload.get("topic") or "Chủ đề"))
    nodes.append(
        {
            "id": "root",
            "type": "root",
            "data": root_data,
            "position": {"x": 0, "y": 0},
        }
    )

    main_children = [child for child in root.get("children", []) if isinstance(child, dict)][:8]
    if not main_children:
        return {"nodes": nodes, "edges": edges}

    left_count = math.ceil(len(main_children) / 2)
    right_count = max(0, len(main_children) - left_count)

    for index, child in enumerate(main_children):
        is_left = index < left_count
        lane_index = index if is_left else index - left_count
        lane_count = left_count if is_left else max(right_count, 1)
        side = -1 if is_left else 1
        main_y = int((lane_index - (lane_count - 1) / 2) * 220)
        main_x = side * 280
        main_id = f"main_{index}"
        color = ["#0f766e", "#2563eb", "#7c3aed", "#ea580c", "#0891b2", "#be185d", "#1d4ed8", "#047857"][index % 8]

        nodes.append(
            {
                "id": main_id,
                "type": "main",
                "data": {
                    **_node_payload(child, f"Nhánh {index + 1}"),
                    "color": color,
                },
                "position": {"x": main_x, "y": main_y},
            }
        )
        edges.append(
            {
                "id": f"edge_root_{main_id}",
                "source": "root",
                "target": main_id,
                "type": "smoothstep",
            }
        )

        sub_children = [grandchild for grandchild in child.get("children", []) if isinstance(grandchild, dict)][:5]
        for sub_index, grandchild in enumerate(sub_children):
            sub_id = f"sub_{index}_{sub_index}"
            sub_y = int(main_y + (sub_index - (len(sub_children) - 1) / 2) * 110)
            sub_x = side * 560

            nodes.append(
                {
                    "id": sub_id,
                    "type": "sub",
                    "data": _node_payload(grandchild, f"Ý phụ {sub_index + 1}"),
                    "position": {"x": sub_x, "y": sub_y},
                }
            )
            edges.append(
                {
                    "id": f"edge_{main_id}_{sub_id}",
                    "source": main_id,
                    "target": sub_id,
                    "type": "smoothstep",
                }
            )

    return {"nodes": nodes, "edges": edges}

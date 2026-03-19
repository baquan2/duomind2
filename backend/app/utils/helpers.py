import json
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
    return content[:max_chars] + "\n...[Noi dung da duoc rut gon]"


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

    accentless = strip_accents(cleaned.lower())
    for phrase in KEYWORD_FILLER_PHRASES:
        accentless = accentless.replace(phrase, " ")

    accentless = re.sub(r"\s{2,}", " ", accentless).strip()
    parts = [
        part
        for part in accentless.split()
        if part and part not in KEYWORD_STOP_WORDS and not part.isdigit()
    ]
    if len(parts) > 4:
        parts = parts[:4]
    return " ".join(parts).strip()


def extract_keywords_from_text(text: str, limit: int = 4) -> list[str]:
    accentless = strip_accents(normalize_text(text).lower())
    words = re.findall(r"[a-z0-9_]{4,}", accentless)
    keywords: list[str] = []

    for word in words:
        if word in KEYWORD_STOP_WORDS or word.isdigit():
            continue
        if word not in keywords:
            keywords.append(word)
        if len(keywords) >= limit:
            break

    return keywords


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

    return extract_keywords_from_text(source_text, limit)


def get_user_context(onboarding_data: dict | None) -> dict[str, Any]:
    """Extract prompt context from onboarding data."""
    if not onboarding_data:
        return {
            "user_persona": "general_learner",
            "difficulty_level": "intermediate",
            "learning_goals": "general_knowledge",
        }

    if onboarding_data.get("education_level") in {"high_school", "college"}:
        difficulty_level = "beginner"
    elif onboarding_data.get("education_level") in {"university", "postgrad"}:
        difficulty_level = "intermediate"
    elif (onboarding_data.get("years_experience") or 0) >= 5:
        difficulty_level = "advanced"
    else:
        difficulty_level = "intermediate"

    return {
        "user_persona": onboarding_data.get("ai_persona", "general_learner"),
        "difficulty_level": difficulty_level,
        "learning_goals": ", ".join(onboarding_data.get("learning_goals", []))
        or "general_knowledge",
    }

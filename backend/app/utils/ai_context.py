from __future__ import annotations

from typing import Any

from app.utils.helpers import build_prompt_learning_context, get_user_context, normalize_text, strip_accents


DEFAULT_CONTEXT_POLICY = "personalized_by_default_but_question_first"


def build_shared_ai_context(
    *,
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    mentor_memory: list[dict[str, Any]] | None = None,
    recent_messages: list[dict[str, Any]] | None = None,
    recent_sessions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    learner_context = build_prompt_learning_context(get_user_context(onboarding))
    return {
        "context_policy": DEFAULT_CONTEXT_POLICY,
        "learner_context": learner_context,
        "profile_digest": {
            "profile": {
                "email": normalize_text(str((profile or {}).get("email") or "")),
                "full_name": normalize_text(str((profile or {}).get("full_name") or "")),
            },
            "onboarding": learner_context,
            "mentor_memory": [
                {
                    "memory_type": normalize_text(str(item.get("memory_type") or "")),
                    "memory_key": normalize_text(str(item.get("memory_key") or "")),
                    "memory_value": item.get("memory_value"),
                    "confidence": item.get("confidence"),
                }
                for item in (mentor_memory or [])[:8]
                if isinstance(item, dict)
            ],
            "recent_messages": [
                {
                    "role": normalize_text(str(item.get("role") or "")),
                    "content": normalize_text(str(item.get("content") or "")),
                }
                for item in (recent_messages or [])[-6:]
                if isinstance(item, dict) and normalize_text(str(item.get("content") or ""))
            ],
            "recent_sessions": [
                {
                    "id": item.get("id"),
                    "title": normalize_text(str(item.get("title") or "")),
                    "session_type": normalize_text(str(item.get("session_type") or "")),
                    "session_subtype": normalize_text(str(item.get("session_subtype") or "")),
                    "summary": normalize_text(str(item.get("summary") or "")),
                    "topic_tags": item.get("topic_tags") or [],
                    "created_at": item.get("created_at"),
                }
                for item in (recent_sessions or [])[:5]
                if isinstance(item, dict)
            ],
        },
    }


def build_context_usage_trace(
    *,
    learner_context: dict[str, Any],
    rendered_texts: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    haystack = strip_accents(
        normalize_text(" ".join(normalize_text(str(item)) for item in rendered_texts if item))
    ).lower()
    available_fields = sorted(key for key, value in learner_context.items() if _has_value(value))
    used_fields: list[str] = []
    for key in available_fields:
        if _context_value_used(learner_context.get(key), haystack):
            used_fields.append(key)
    return {
        "available_fields": available_fields,
        "used_fields": used_fields,
        "ignored_fields": [field for field in available_fields if field not in used_fields],
    }


def _has_value(value: Any) -> bool:
    if isinstance(value, str):
        return bool(normalize_text(value))
    if isinstance(value, list):
        return any(_has_value(item) for item in value)
    return value is not None


def _context_value_used(value: Any, haystack: str) -> bool:
    if isinstance(value, list):
        return any(_context_value_used(item, haystack) for item in value)
    normalized = normalize_text(str(value or ""))
    if len(normalized) < 3:
        return False
    lowered = strip_accents(normalized).lower()
    return lowered in haystack

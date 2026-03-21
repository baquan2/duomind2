import asyncio

from app.utils.helpers import normalize_text


SOURCE_SEARCH_TIMEOUT_SECONDS = 6.0


def normalize_source_references(raw_sources: object, *, limit: int = 5) -> list[dict[str, str]]:
    if not isinstance(raw_sources, list):
        return []

    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw_sources[:limit]:
        if not isinstance(item, dict):
            continue
        label = normalize_text(str(item.get("label") or "Nguồn tham khảo"))
        url = normalize_text(str(item.get("url") or ""))
        snippet = normalize_text(str(item.get("snippet") or ""))
        if not label or not url or url in seen:
            continue
        seen.add(url)
        normalized.append(
            {
                "label": label,
                "url": url,
                "snippet": snippet,
            }
        )
    return normalized


async def resolve_source_lookup(
    source_task: asyncio.Task[list[dict[str, str]]],
    *,
    flow_label: str,
) -> list[dict[str, str]]:
    try:
        raw_sources = await asyncio.wait_for(source_task, timeout=SOURCE_SEARCH_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        source_task.cancel()
        return []
    except Exception as exc:
        print(f"[{flow_label}] Source lookup failed: {exc}")
        return []
    return normalize_source_references(raw_sources)

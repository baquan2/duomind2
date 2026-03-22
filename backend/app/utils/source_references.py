import asyncio

from app.utils.helpers import normalize_text


SOURCE_SEARCH_TIMEOUT_SECONDS = 4.0


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


def split_sources_and_related_materials(
    raw_sources: list[dict[str, str]] | None,
    *,
    selected_urls: list[str] | None = None,
    source_limit: int = 3,
    related_limit: int = 4,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    normalized = normalize_source_references(
        raw_sources or [],
        limit=max(source_limit + related_limit, 6),
    )
    selected = {normalize_text(url) for url in (selected_urls or []) if normalize_text(url)}
    evidence: list[dict[str, str]] = []
    related: list[dict[str, str]] = []

    if selected:
        for item in normalized:
            if item["url"] in selected and len(evidence) < source_limit:
                evidence.append(item)
        for item in normalized:
            if item["url"] in selected:
                continue
            related.append(item)
            if len(related) >= related_limit:
                break
        return evidence, related

    evidence = normalized[:source_limit]
    related = normalized[source_limit : source_limit + related_limit]
    return evidence, related

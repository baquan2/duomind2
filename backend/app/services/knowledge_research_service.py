from __future__ import annotations

import html
import re
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import httpx

from app.utils.helpers import extract_keywords_from_text, normalize_text, normalize_topic_phrase


DUCKDUCKGO_HTML_URL = "https://html.duckduckgo.com/html/"
MAX_RESULTS = 4
PREFERRED_DOMAINS = (
    "wikipedia.org",
    "britannica.com",
    "investopedia.com",
    "developer.mozilla.org",
    "python.org",
    "fastapi.tiangolo.com",
    "postgresql.org",
    "supabase.com",
    "openai.com",
    "who.int",
    "cdc.gov",
    "nih.gov",
    "bls.gov",
    "coursera.org",
)

RESULT_LINK_RE = re.compile(
    r'<a[^>]*class="result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
RESULT_SNIPPET_RE = re.compile(
    r'<a[^>]*class="result__snippet"[^>]*>(?P<snippet_a>.*?)</a>|<div[^>]*class="result__snippet"[^>]*>(?P<snippet_b>.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(value: str) -> str:
    text = html.unescape(TAG_RE.sub(" ", value))
    return normalize_text(text)


def _resolve_result_url(raw_url: str) -> str:
    if not raw_url:
        return ""

    resolved = html.unescape(raw_url)
    if resolved.startswith("//"):
        resolved = f"https:{resolved}"
    elif resolved.startswith("/"):
        resolved = urljoin(DUCKDUCKGO_HTML_URL, resolved)

    parsed = urlparse(resolved)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        uddg = parse_qs(parsed.query).get("uddg", [""])[0]
        if uddg:
            return unquote(uddg)
    return resolved


def _domain_rank(url: str) -> int:
    domain = urlparse(url).netloc.lower()
    for index, preferred in enumerate(PREFERRED_DOMAINS):
        if preferred in domain:
            return index
    if domain.endswith(".gov") or ".gov." in domain:
        return len(PREFERRED_DOMAINS)
    if domain.endswith(".edu") or ".edu." in domain:
        return len(PREFERRED_DOMAINS) + 1
    if domain.endswith(".org") or ".org." in domain:
        return len(PREFERRED_DOMAINS) + 2
    return len(PREFERRED_DOMAINS) + 10


def _keyword_overlap(text: str, keywords: list[str]) -> int:
    if not keywords:
        return 0
    lowered = normalize_text(text).lower()
    return sum(1 for keyword in keywords if keyword and keyword in lowered)


def _compact_query(text: str, fallback: str = "") -> str:
    normalized = normalize_text(text)
    if len(normalized) <= 120:
        return normalized

    keywords = extract_keywords_from_text(normalized, limit=8)
    if keywords:
        focus = normalize_topic_phrase(fallback) or normalize_text(fallback)
        candidate = " ".join(part for part in [focus, " ".join(keywords[:6])] if part)
        return normalize_text(candidate)[:120].strip()

    return normalized[:120].strip()


def _build_queries(
    *,
    message: str,
    focus_topic: str,
    evidence_targets: list[str] | None = None,
) -> list[str]:
    focus = normalize_topic_phrase(focus_topic) or normalize_text(focus_topic)
    primary = _compact_query(message, focus)
    queries: list[str] = [primary] if primary else []

    if focus and focus.lower() != primary.lower():
        queries.append(focus)

    evidence_keywords: list[str] = []
    for item in evidence_targets or []:
        for keyword in extract_keywords_from_text(item, limit=4):
            if keyword not in evidence_keywords:
                evidence_keywords.append(keyword)
        if len(evidence_keywords) >= 5:
            break

    if focus and evidence_keywords:
        queries.append(normalize_text(f"{focus} {' '.join(evidence_keywords[:4])}"))

    unique_queries: list[str] = []
    seen: set[str] = set()
    for query in queries:
        cleaned = normalize_text(query)
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique_queries.append(cleaned)
        if len(unique_queries) >= 2:
            break

    return unique_queries


async def search_knowledge_sources(
    *,
    message: str,
    focus_topic: str,
    evidence_targets: list[str] | None = None,
    limit: int = MAX_RESULTS,
) -> list[dict[str, str]]:
    queries = _build_queries(
        message=message,
        focus_topic=focus_topic,
        evidence_targets=evidence_targets,
    )
    if not queries:
        return []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }
    keywords = extract_keywords_from_text(f"{message} {focus_topic}", limit=8)
    collected: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    async with httpx.AsyncClient(timeout=6.0, follow_redirects=True, headers=headers) as client:
        for query in queries:
            try:
                response = await client.get(DUCKDUCKGO_HTML_URL, params={"q": query})
                response.raise_for_status()
            except Exception:
                continue

            links = RESULT_LINK_RE.findall(response.text)
            snippets = RESULT_SNIPPET_RE.findall(response.text)

            for index, match in enumerate(links):
                raw_url, raw_title = match
                url = _resolve_result_url(raw_url)
                if not url or url in seen_urls or not url.startswith("http"):
                    continue

                snippet_tuple = snippets[index] if index < len(snippets) else ("", "")
                snippet = _strip_html(snippet_tuple[0] or snippet_tuple[1])
                label = _strip_html(raw_title)
                if not label:
                    continue

                seen_urls.add(url)
                collected.append(
                    {
                        "label": label,
                        "url": url,
                        "snippet": snippet,
                    }
                )

                if len(collected) >= limit * 2:
                    break

            if len(collected) >= limit * 2:
                break

    collected.sort(
        key=lambda item: (
            _domain_rank(item["url"]),
            -_keyword_overlap(f'{item["label"]} {item.get("snippet", "")}', keywords),
            len(item["label"]),
        )
    )
    return collected[:limit]

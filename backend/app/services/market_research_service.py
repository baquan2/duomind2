from __future__ import annotations

import html
import re
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import httpx

from app.models.mentor import MentorIntent
from app.utils.helpers import normalize_text


DUCKDUCKGO_HTML_URL = "https://html.duckduckgo.com/html/"
MAX_RESULTS = 6
PREFERRED_DOMAINS = (
    "topcv.vn",
    "vietnamworks.com",
    "itviec.com",
    "glints.com",
    "jobstreet.vn",
    "careerbuilder.vn",
    "linkedin.com",
    "coursera.org",
    "indeed.com",
    "glassdoor.com",
    "bls.gov",
    "weforum.org",
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
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    for index, preferred in enumerate(PREFERRED_DOMAINS):
        if preferred in domain:
            return index
    return len(PREFERRED_DOMAINS) + 1


def _build_queries(
    message: str,
    onboarding: dict | None,
    intent: MentorIntent,
) -> list[str]:
    normalized_message = normalize_text(message)
    lowered_message = normalized_message.lower()
    industry = normalize_text(str((onboarding or {}).get("industry") or ""))
    job_title = normalize_text(str((onboarding or {}).get("job_title") or ""))
    major = normalize_text(str((onboarding or {}).get("major") or ""))
    target_role = normalize_text(str((onboarding or {}).get("target_role") or ""))
    role_hint = target_role or job_title or major or industry
    direct_skill_lookup = any(marker in lowered_message for marker in ("tuyển dụng", "tuyen dung", "jd", "job description")) and any(
        marker in lowered_message for marker in ("kỹ năng", "ky nang", "skills", "liệt kê", "liet ke", "yêu cầu", "yeu cau")
    )

    queries = [normalized_message]

    if intent in {"career_roles", "market_outlook", "skill_gap"} and role_hint:
        queries.append(
            f"{role_hint} skills demand tuyển dụng Việt Nam"
        )
    elif intent == "learning_roadmap" and role_hint:
        queries.append(
            f"{role_hint} cần học gì kỹ năng nghề nghiệp"
        )
    elif role_hint:
        queries.append(f"{role_hint} nghề nghiệp kỹ năng cơ hội phát triển")

    unique_queries: list[str] = []
    seen = set()
    for query in queries:
        cleaned = normalize_text(query)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            unique_queries.append(cleaned)
        if len(unique_queries) >= 2:
            break

    return unique_queries


async def search_market_context(
    message: str,
    onboarding: dict | None,
    intent: MentorIntent,
) -> list[dict[str, str]]:
    queries = _build_queries(message, onboarding, intent)
    if not queries:
        return []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }

    collected: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers) as client:
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
                title = _strip_html(raw_title)
                if not title:
                    continue

                seen_urls.add(url)
                collected.append(
                    {
                        "title": title,
                        "snippet": snippet,
                        "url": url,
                        "query": query,
                        "source_name": urlparse(url).netloc.replace("www.", ""),
                    }
                )

                if len(collected) >= MAX_RESULTS * 2:
                    break

            if len(collected) >= MAX_RESULTS * 2:
                break

    collected.sort(key=lambda item: (_domain_rank(item["url"]), len(item["title"])))
    return collected[:MAX_RESULTS]

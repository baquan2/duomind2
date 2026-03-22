import asyncio
import re
from time import perf_counter
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.models.analysis import ExploreRequest, ExploreResult
from app.services.gemini_service import gemini
from app.services.knowledge_research_service import search_knowledge_sources
from app.services.supabase_service import SupabaseService
from app.utils.ai_context import (
    DEFAULT_CONTEXT_POLICY,
    build_context_usage_trace,
    build_shared_ai_context,
)
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
    build_explore_blueprint_prompt,
    build_explore_core_prompt,
    build_explore_query_plan_prompt,
    build_explore_repair_prompt,
)
from app.utils.fallbacks import build_explore_mindmap
from app.utils.helpers import (
    build_core_title,
    build_prompt_learning_context,
    get_user_context,
    normalize_text,
    normalize_topic_phrase,
    normalize_topic_tags,
    strip_accents,
)
from app.utils.knowledge_detail import (
    SECTION_DISPLAY_TITLES,
    SECTION_ORDER,
    normalize_multiline_text,
)
from app.utils.source_references import resolve_source_lookup, split_sources_and_related_materials


router = APIRouter()

EXPLORE_TOPIC_STOPWORDS = {
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
    "giai",
    "thich",
    "phan",
    "tich",
    "tim",
    "hieu",
}

GENERIC_EXPLORE_PHRASES = (
    "đây là một khái niệm quan trọng",
    "đây là một chủ đề quan trọng",
    "người học nên",
    "ở góc nhìn",
    "điều quan trọng là",
    "hãy hiểu",
    "hãy nắm",
    "phần này",
    "khối kiến thức",
)


STRUCTURE_EXPLORE_MARKERS = (
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


def _validate_explore_input(prompt: str) -> str:
    normalized = normalize_text(prompt)
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chủ đề khám phá đang trống. Hãy nhập rõ câu hỏi hoặc chủ đề bạn muốn tìm hiểu.",
        )
    if len(normalized) < 6 or len(normalized.split()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Câu hỏi khám phá còn quá ngắn. Hãy nêu rõ chủ đề hoặc điều bạn muốn hiểu.",
        )
    return normalized


def _focus_keywords(text: str) -> list[str]:
    normalized = strip_accents(normalize_text(normalize_topic_phrase(text) or text)).lower()
    tokens = re.findall(r"[0-9a-z]+", normalized)
    keywords: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if len(token) < 3 or token in EXPLORE_TOPIC_STOPWORDS or token.isdigit():
            continue
        if token in seen:
            continue
        seen.add(token)
        keywords.append(token)
        if len(keywords) >= 6:
            break
    return keywords


def _focus_overlap_ratio(text: str, focus_topic: str) -> float:
    keywords = _focus_keywords(focus_topic)
    if not keywords:
        return 1.0
    haystack = strip_accents(normalize_text(text)).lower()
    matches = sum(1 for keyword in keywords if keyword in haystack)
    return matches / len(keywords)


def _summary_bullet_count(summary: str) -> int:
    return len([line for line in summary.splitlines() if normalize_text(line.lstrip("-*• "))])


def _normalize_key_points(raw_points: object) -> list[str]:
    if not isinstance(raw_points, list):
        return []
    points: list[str] = []
    for point in raw_points:
        cleaned = normalize_text(str(point))
        if not cleaned or cleaned in points:
            continue
        points.append(cleaned)
        if len(points) >= 5:
            break
    return points[:5]


def _contains_trailing_ellipsis(text: str) -> bool:
    normalized = normalize_text(text)
    return normalized.endswith("...") or normalized.endswith("…")


def _summary_lines(text: object) -> list[str]:
    if not isinstance(text, str):
        return []
    bullets: list[str] = []
    for line in text.splitlines():
        cleaned = normalize_text(line.lstrip("-*• ").strip())
        if not cleaned or _contains_trailing_ellipsis(cleaned):
            continue
        if cleaned not in bullets:
            bullets.append(cleaned)
    return bullets


def _section_point_candidates(sections: object) -> list[str]:
    if not isinstance(sections, dict):
        return []
    candidates: list[str] = []
    for key in (
        "core_concept",
        "mechanism",
        "components_and_relationships",
        "real_world_applications",
        "common_misconceptions",
    ):
        sentence = _lead_sentence((sections.get(key) or {}).get("content"))
        if not sentence or _contains_trailing_ellipsis(sentence) or _looks_generic_text(sentence):
            continue
        if sentence not in candidates:
            candidates.append(sentence)
    return candidates[:5]


def _normalize_explore_summary(
    summary: object,
    key_points: object,
    fallback_summary: str,
    *,
    prompt: str,
    focus_topic: str,
    detailed_sections: object,
) -> str:
    bullets = _summary_lines(summary)
    if bullets and not _is_direct_explore_answer(prompt, focus_topic, bullets[0]):
        core_sentence = _lead_sentence(((detailed_sections or {}).get("core_concept") or {}).get("content"))
        if core_sentence and _is_direct_explore_answer(prompt, focus_topic, core_sentence):
            bullets = [core_sentence, *[item for item in bullets if item != core_sentence]]

    for item in _normalize_key_points(key_points):
        if item not in bullets and not _looks_generic_text(item) and not _contains_trailing_ellipsis(item):
            bullets.append(item)
        if len(bullets) >= 4:
            break

    for item in _section_point_candidates(detailed_sections):
        if item not in bullets:
            bullets.append(item)
        if len(bullets) >= 4:
            break

    if len(bullets) < 3:
        for item in _summary_lines(fallback_summary):
            if item not in bullets:
                bullets.append(item)
            if len(bullets) >= 4:
                break

    if not bullets:
        return fallback_summary
    return "\n".join(f"- {item}" for item in bullets[:4])


def _normalize_explore_output_key_points(
    raw_points: object,
    fallback_points: list[str],
    *,
    prompt: str,
    focus_topic: str,
    detailed_sections: object,
) -> list[str]:
    direct_points = _normalize_key_points(raw_points)
    if direct_points and not _key_points_need_fallback(prompt, focus_topic, direct_points):
        return direct_points[:5]

    section_points = _section_point_candidates(detailed_sections)
    if len(section_points) >= 4:
        return section_points[:5]

    merged = list(direct_points)
    for item in section_points + fallback_points:
        cleaned = normalize_text(item)
        if not cleaned or cleaned in merged or _contains_trailing_ellipsis(cleaned):
            continue
        merged.append(cleaned)
        if len(merged) >= 5:
            break

    return merged[:5] if merged else fallback_points[:5]


def _build_detail_summary_from_sections(sections: object, fallback_text: str) -> str:
    if isinstance(sections, dict):
        bullets: list[str] = []
        labeled_keys = (
            ("mechanism", "Co che"),
            ("components_and_relationships", "Cau truc"),
            ("real_world_applications", "Ung dung"),
            ("common_misconceptions", "De nham o"),
        )
        for key, label in labeled_keys:
            sentence = _lead_sentence((sections.get(key) or {}).get("content"))
            if not sentence or _looks_generic_text(sentence) or _contains_trailing_ellipsis(sentence):
                continue
            candidate = f"{label}: {sentence}"
            if candidate not in bullets:
                bullets.append(candidate)
            if len(bullets) >= 4:
                break
        if bullets:
            return "\n".join(f"- {item}" for item in bullets[:4])
    return fallback_text


def _normalize_topic_tag_list(raw_tags: object, source_text: str) -> list[str]:
    tags = normalize_topic_tags(raw_tags, source_text)
    normalized: list[str] = []
    for tag in tags:
        cleaned = normalize_topic_phrase(tag)
        if cleaned and cleaned not in normalized:
            normalized.append(cleaned)
    return normalized


def _looks_generic_text(text: str) -> bool:
    return is_generic_knowledge_text(text)


def _lead_sentence(text: str) -> str:
    normalized = normalize_multiline_text(text)
    if not normalized:
        return ""
    match = re.split(r"(?<=[.!?])\s+|\n+", normalized, maxsplit=1)
    return normalize_text(match[0] if match else normalized)


def _parse_compare_subjects(prompt: str) -> tuple[str, str] | None:
    normalized = normalize_text(prompt)
    patterns = [
        r"(.+?)\s+(?:là|la)\s+gì\s+và\s+(?:khác|khac)\s+(.+?)\s+(?:ở|o)\s+(?:điểm|diem)\s+nào\??$",
        r"(.+?)\s+(?:khác|khac)\s+(.+?)\s+(?:ở|o)\s+(?:điểm|diem)\s+nào\??$",
        r"so sánh\s+(.+?)\s+và\s+(.+?)$",
        r"phân biệt\s+(.+?)\s+và\s+(.+?)$",
        r"phan biet\s+(.+?)\s+va\s+(.+?)$",
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


def _is_structure_explore_request(prompt: str) -> bool:
    lowered = strip_accents(normalize_text(prompt)).lower()
    return any(marker in lowered for marker in STRUCTURE_EXPLORE_MARKERS)


def _detect_explore_kind(prompt: str) -> str:
    lowered = strip_accents(normalize_text(prompt)).lower()
    if _parse_compare_subjects(prompt):
        return "comparison"
    if _is_structure_explore_request(prompt):
        return "structure"
    if "la gi" in lowered:
        return "definition"
    if "hoat dong nhu the nao" in lowered or "van hanh nhu the nao" in lowered:
        return "mechanism"
    return "general"


def _is_direct_explore_answer(prompt: str, focus_topic: str, text: str) -> bool:
    lead = strip_accents(_lead_sentence(text)).lower()
    if not lead:
        return False

    compare_subjects = _parse_compare_subjects(prompt)
    if compare_subjects:
        return (
            all(strip_accents(subject).lower() in lead for subject in compare_subjects)
            and any(marker in lead for marker in (" khac ", " phan biet ", " so sanh "))
        )

    question_type = _detect_explore_kind(prompt)
    if question_type == "definition":
        return _focus_overlap_ratio(lead, focus_topic) >= 0.34 and any(
            marker in f" {lead} "
            for marker in (" la ", " la mot ", " duoc dung de ", " chi ")
        )
    if question_type == "structure":
        return _focus_overlap_ratio(lead, focus_topic) >= 0.34 and any(
            marker in f" {lead} "
            for marker in (" gom ", " bao gom ", " thanh phan ", " cau truc ")
        )
    if question_type == "mechanism":
        return _focus_overlap_ratio(lead, focus_topic) >= 0.34 and any(
            marker in f" {lead} "
            for marker in (" hoat dong ", " van hanh ", " dien ra ", " bat dau ")
        )
    return _focus_overlap_ratio(lead, focus_topic) >= 0.34


def _key_points_need_fallback(prompt: str, focus_topic: str, key_points: list[str]) -> bool:
    if len(key_points) < 4:
        return True

    question_type = _detect_explore_kind(prompt)
    compare_subjects = _parse_compare_subjects(prompt)
    useful_points = 0
    generic_points = 0
    compare_points = 0
    structure_points = 0

    for point in key_points:
        normalized = normalize_text(point)
        if not normalized:
            continue
        if _looks_generic_text(normalized):
            generic_points += 1
            continue

        lowered = strip_accents(normalized).lower()
        if compare_subjects and all(strip_accents(subject).lower() in lowered for subject in compare_subjects):
            compare_points += 1
        if question_type == "structure" and any(
            marker in f" {lowered} " for marker in (" gom ", " bao gom ", " thanh phan ", " cau truc ")
        ):
            structure_points += 1

        if _focus_overlap_ratio(normalized, focus_topic) >= 0.22:
            useful_points += 1
            continue

        if compare_subjects and any(strip_accents(subject).lower() in lowered for subject in compare_subjects):
            useful_points += 1

    if generic_points >= 2:
        return True
    if useful_points < 3:
        return True
    if compare_subjects and compare_points == 0:
        return True
    if question_type == "structure" and structure_points == 0:
        return True
    return False


def _resolve_display_title(prompt: str, focus_topic: str) -> str:
    compare_subjects = _parse_compare_subjects(prompt)
    if compare_subjects:
        return f"Phân biệt {compare_subjects[0]} và {compare_subjects[1]}"
    title = normalize_topic_phrase(focus_topic or prompt).strip(" .")
    if title.endswith("?"):
        title = title[:-1].strip()
    return title or "Khám phá chủ đề"


def _build_compact_explore_title(prompt: str, focus_topic: str) -> str:
    compare_subjects = _parse_compare_subjects(prompt)
    if compare_subjects:
        return build_core_title(f"{compare_subjects[0]} và {compare_subjects[1]}", "Khám phá chủ đề")
    return build_core_title(focus_topic or prompt, "Khám phá chủ đề")


def _build_example_context(learner_context: dict[str, str]) -> str:
    target_role = learner_context.get("target_role")
    current_focus = learner_context.get("current_focus")
    if target_role and current_focus:
        return (
            f"Ví dụ nên bám vào bối cảnh người học đang hướng tới {target_role} "
            f"và hiện tập trung vào {current_focus}."
        )
    if target_role:
        return f"Ví dụ nên gần với bối cảnh người học đang hướng tới {target_role}."
    return "Ví dụ nên ngắn, gần thực tế và chỉ dùng để làm rõ đúng ý chính."


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


def _build_definition_sections(title: str, learner_context: dict[str, str]) -> dict[str, dict[str, str]]:
    example_context = _build_example_context(learner_context)
    return {
        "core_concept": {
            "title": SECTION_DISPLAY_TITLES["core_concept"],
            "content": (
                f"{title} là một khái niệm hoặc cơ chế có phạm vi áp dụng cụ thể, không phải nhãn gọi chung cho cả lĩnh vực. "
                f"Muốn hiểu đúng {title}, cần chốt ba ý: nó dùng để làm gì, xuất hiện trong hoàn cảnh nào, và khác gì với khái niệm gần nhất. "
                "Khi ba điểm này rõ, người học mới có khung lý thuyết đủ chắc để đọc tiếp ví dụ và ứng dụng mà không bị lan man."
            ),
        },
        "mechanism": {
            "title": SECTION_DISPLAY_TITLES["mechanism"],
            "content": (
                f"Bản chất của {title} nằm ở logic vận hành: đầu vào là gì, ở giữa xử lý điều gì và đầu ra tạo ra giá trị ra sao. "
                "Nếu chỉ nhớ một định nghĩa ngắn mà không hiểu cơ chế này, người học rất dễ lúng túng khi gặp tình huống mới hoặc ví dụ khác bề mặt. "
                "Vì vậy phần cơ chế phải cho thấy vì sao khái niệm đó có tác dụng và điều gì làm cho nó khác với cách hiểu gần giống."
            ),
        },
        "components_and_relationships": {
            "title": SECTION_DISPLAY_TITLES["components_and_relationships"],
            "content": (
                f"{title} thường có vài thành phần hoặc vài góc nhìn phải đặt cạnh nhau mới hiểu đúng. "
                "Điểm quan trọng không chỉ là nhớ tên từng phần, mà là biết phần nào là trung tâm, phần nào hỗ trợ, và khi một phần thay đổi thì phần còn lại bị ảnh hưởng thế nào. "
                "Khung này giúp biến lý thuyết rời rạc thành một cấu trúc có quan hệ rõ ràng."
            ),
        },
        "persona_based_example": {
            "title": SECTION_DISPLAY_TITLES["persona_based_example"],
            "content": (
                f"{example_context} Với {title}, một ví dụ tốt nên cho thấy rõ đầu vào, cách xử lý và đầu ra thay đổi thế nào. "
                "Ví dụ càng sát tình huống thật thì người học càng thấy được bản chất của khái niệm, thay vì chỉ nhớ một câu định nghĩa khô. "
                "Đó là cách nối phần tổng quan lý thuyết với trực giác sử dụng."
            ),
        },
        "real_world_applications": {
            "title": SECTION_DISPLAY_TITLES["real_world_applications"],
            "content": (
                f"Giá trị của {title} thể hiện ở chỗ nó giúp giải thích, đánh giá hoặc cải thiện một quyết định trong thực tế. "
                "Khi xem ứng dụng, nên hỏi: nó xuất hiện ở đâu trong công việc, quy trình, hệ thống hoặc sản phẩm, và nó giúp con người làm tốt điều gì. "
                "Trả lời được câu hỏi đó thì chủ đề mới thật sự chuyển từ lý thuyết sang khả năng áp dụng."
            ),
        },
        "common_misconceptions": {
            "title": SECTION_DISPLAY_TITLES["common_misconceptions"],
            "content": (
                f"Nhầm lẫn phổ biến với {title} là đánh đồng nó với một khái niệm nghe gần giống hoặc nhớ ví dụ mà quên điều kiện áp dụng. "
                "Cách sửa là luôn quay lại định nghĩa ngắn, cơ chế cốt lõi và giới hạn áp dụng của chủ đề. "
                "Ba điểm này giúp tách hiểu đúng khỏi cách nhớ máy móc."
            ),
        },
        "next_step_self_study": {
            "title": SECTION_DISPLAY_TITLES["next_step_self_study"],
            "content": (
                f"Điểm nên nắm tiếp là ranh giới giữa định nghĩa của {title}, cơ chế tạo ra kết quả và bối cảnh nào khiến nó phát huy giá trị. "
                "Khi ba phần này rõ, việc đọc thêm ví dụ hoặc trường hợp mới sẽ ít bị lệch hơn."
            ),
        },
    }


def _build_comparison_sections(prompt: str, learner_context: dict[str, str]) -> dict[str, dict[str, str]]:
    first, second = _parse_compare_subjects(prompt) or ("khái niệm A", "khái niệm B")
    example_context = _build_example_context(learner_context)
    return {
        "core_concept": {
            "title": SECTION_DISPLAY_TITLES["core_concept"],
            "content": (
                f"{first} và {second} khác nhau chủ yếu ở mục tiêu, đầu ra và loại quyết định mà mỗi bên hỗ trợ. "
                f"{first} thường nghiêng về việc làm rõ vấn đề, requirement hoặc phạm vi cần xử lý, còn {second} thường nghiêng về việc đọc tín hiệu, dữ liệu hoặc kết quả quan sát để rút ra kết luận. "
                "Muốn phân biệt đúng, cần đặt cả hai lên cùng một khung so sánh thay vì chỉ nhớ hai định nghĩa rời."
            ),
        },
        "mechanism": {
            "title": SECTION_DISPLAY_TITLES["mechanism"],
            "content": (
                f"Cơ chế của {first} thường đi từ nhu cầu hoặc bài toán cần làm rõ đến yêu cầu, quy trình và đầu ra phải chốt. "
                f"Cơ chế của {second} thường đi từ dữ liệu, hành vi, chỉ số hoặc kết quả quan sát đến insight và đề xuất hành động. "
                "Khác biệt nằm ở điểm xuất phát, cách xử lý thông tin và loại kết quả cuối cùng."
            ),
        },
        "components_and_relationships": {
            "title": SECTION_DISPLAY_TITLES["components_and_relationships"],
            "content": (
                f"Khi đặt {first} cạnh {second}, nên so trên ba trục: mục tiêu chính, đầu ra chính và nguồn thông tin thường dùng. "
                f"{first} thường gắn với stakeholder, requirement và luồng công việc; {second} thường gắn với metric, dữ liệu và bằng chứng quan sát. "
                "Khung này giúp tách điểm giống bề mặt khỏi điểm khác thực sự."
            ),
        },
        "persona_based_example": {
            "title": SECTION_DISPLAY_TITLES["persona_based_example"],
            "content": (
                f"{example_context} Nếu một người đang làm rõ requirement, vẽ luồng xử lý và chốt điều kiện bàn giao, đó nghiêng về {first}. "
                f"Nếu người đó đang đọc số liệu, tìm nguyên nhân biến động và đề xuất thay đổi dựa trên dữ liệu, đó nghiêng về {second}. "
                "Ví dụ kiểu này giúp nhìn ra sự khác nhau bằng công việc thật, không chỉ bằng tên gọi."
            ),
        },
        "real_world_applications": {
            "title": SECTION_DISPLAY_TITLES["real_world_applications"],
            "content": (
                f"{first} hữu ích khi tổ chức cần làm rõ bài toán, requirement, quy trình và cách các bên phối hợp. "
                f"{second} hữu ích khi tổ chức cần đo lường, đánh giá và tối ưu sản phẩm hoặc vận hành dựa trên tín hiệu thực tế. "
                "Trong nhiều dự án, hai bên có thể phối hợp chặt nhưng vẫn giữ trọng tâm kiến thức riêng."
            ),
        },
        "common_misconceptions": {
            "title": SECTION_DISPLAY_TITLES["common_misconceptions"],
            "content": (
                f"Nhầm lẫn phổ biến là cho rằng {first} và {second} chỉ khác tên gọi. "
                "Thực tế, tên chức danh có thể thay đổi theo công ty, nhưng vẫn phải soi vào bài toán họ giải quyết, đầu ra họ chịu trách nhiệm và nguồn thông tin họ dùng mỗi ngày. "
                "Đó mới là cách phân biệt chắc nhất."
            ),
        },
        "next_step_self_study": {
            "title": SECTION_DISPLAY_TITLES["next_step_self_study"],
            "content": (
                f"Điểm nên nắm tiếp là ranh giới giữa {first} và {second} trong một tình huống thực tế: ai làm rõ vấn đề, ai đọc tín hiệu và ai chịu trách nhiệm cho loại đầu ra nào. "
                "Khi trục này rõ, việc so sánh sẽ bớt nhầm hơn rất nhiều."
            ),
        },
    }


def _legacy_build_fallback_payload(prompt: str, learner_context: dict[str, str]) -> dict[str, Any]:
    title = _build_compact_explore_title(prompt, prompt)
    question_type = _detect_explore_kind(prompt)

    if question_type == "comparison":
        first, second = _parse_compare_subjects(prompt) or ("khái niệm A", "khái niệm B")
        sections = _build_comparison_sections(prompt, learner_context)
        summary_lines = [
            f"- {first} khác {second} chủ yếu ở mục tiêu công việc, đầu ra chính và nguồn thông tin mà mỗi bên dùng để ra quyết định.",
            f"- Điểm khác cốt lõi nằm ở cách mỗi bên tiếp cận vấn đề và loại kết quả mà họ tạo ra.",
            "- Ví dụ tốt phải cho thấy mỗi bên xuất hiện trong một nhiệm vụ thực tế như thế nào.",
            "- Nhầm lẫn thường đến từ việc so tên gọi thay vì soi bài toán và đầu ra thực sự.",
        ]
        key_points = [
            f"{first} và {second} phải được so trên cùng một khung câu hỏi.",
            "Mục tiêu công việc là trục phân biệt mạnh nhất.",
            "Đầu ra chính giúp thấy rõ vai trò thực tế của từng bên.",
            "Nguồn thông tin thường dùng cũng là dấu hiệu phân biệt.",
            "Không nên suy từ tên gọi mà bỏ qua bối cảnh công việc thật.",
        ]
    else:
        sections = _build_definition_sections(title, learner_context)
        summary_lines = [
            f"- {title} là một khái niệm hoặc cơ chế có phạm vi áp dụng cụ thể, không phải nhãn gọi chung cho cả lĩnh vực liên quan.",
            f"- Cơ chế của {title} phải được nhìn theo logic đầu vào, xử lý và đầu ra thay vì học thuộc từ khóa.",
            "- Ví dụ chỉ có giá trị khi nó làm rõ bản chất và điều kiện áp dụng của chủ đề.",
            "- Nhầm lẫn phổ biến thường đến từ việc nhớ kết quả mà bỏ qua nguyên lý tạo ra kết quả đó.",
        ]
        key_points = [
            f"{title} phải được trả lời trực diện ngay từ phần mở đầu.",
            "Định nghĩa ngắn nhưng phải đủ phạm vi áp dụng.",
            "Cơ chế quan trọng hơn việc học thuộc từ khóa.",
            "Ví dụ cần sát thực tế nhưng không được kéo lệch chủ đề.",
            "Nhầm lẫn phổ biến giúp người học biết chỗ dễ hiểu sai.",
        ]

    return {
        "title": title,
        "summary": "\n".join(summary_lines),
        "key_points": key_points,
        "topic_tags": normalize_topic_tags([], title),
        "detailed_sections": sections,
        "teaching_adaptation": {
            "focus_priority": f"Bám chặt câu hỏi gốc về {title}",
            "tone": "Rõ ràng, trực diện, ưu tiên bản chất trước",
            "depth_control": "Đi từ tổng quan lý thuyết sang cơ chế, cấu trúc, ví dụ và ứng dụng",
            "example_strategy": _build_example_context(learner_context),
        },
    }


def _heuristic_explore_plan(prompt: str, focus_topic: str) -> dict[str, Any]:
    compare_subjects = _parse_compare_subjects(prompt)
    must_include = [normalize_topic_phrase(focus_topic or prompt)]
    if compare_subjects:
        must_include.extend(list(compare_subjects))
    must_include = [item for item in must_include if item][:4]
    return {
        "question_type": _detect_explore_kind(prompt),
        "main_question": normalize_text(prompt),
        "focus_topic": normalize_topic_phrase(focus_topic or prompt),
        "comparison_targets": list(compare_subjects) if compare_subjects else [],
        "must_include": must_include,
        "must_avoid": ["lan sang chủ đề liên quan", "giảng rộng cả lĩnh vực"],
        "answer_strategy": "Trả lời trực diện câu hỏi trước, rồi mới giải thích lý thuyết, cơ chế và ví dụ.",
    }

def _normalize_explore_plan(
    raw_plan: object,
    prompt: str,
    focus_topic: str,
) -> dict[str, Any]:
    fallback = _heuristic_explore_plan(prompt, focus_topic)
    if not isinstance(raw_plan, dict):
        return fallback

    question_type = normalize_text(str(raw_plan.get("question_type") or fallback["question_type"])).lower()
    if question_type not in {"definition", "comparison", "mechanism", "structure", "general"}:
        question_type = fallback["question_type"]

    main_question = normalize_text(str(raw_plan.get("main_question") or fallback["main_question"]))
    plan_focus_topic = normalize_topic_phrase(str(raw_plan.get("focus_topic") or fallback["focus_topic"]))

    comparison_targets_raw = raw_plan.get("comparison_targets")
    comparison_targets: list[str] = []
    if isinstance(comparison_targets_raw, list):
        for item in comparison_targets_raw[:2]:
            cleaned = normalize_topic_phrase(str(item))
            if cleaned:
                comparison_targets.append(cleaned)
    if question_type == "comparison" and len(comparison_targets) < 2:
        comparison_targets = list(fallback["comparison_targets"])

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
    if not must_include:
        must_include = list(fallback["must_include"])

    must_avoid_raw = raw_plan.get("must_avoid")
    must_avoid: list[str] = []
    if isinstance(must_avoid_raw, list):
        for item in must_avoid_raw[:4]:
            cleaned = normalize_text(str(item))
            if cleaned:
                must_avoid.append(cleaned)
    if not must_avoid:
        must_avoid = list(fallback["must_avoid"])

    answer_strategy = normalize_text(str(raw_plan.get("answer_strategy") or fallback["answer_strategy"]))

    return {
        "question_type": question_type,
        "main_question": main_question or fallback["main_question"],
        "focus_topic": plan_focus_topic or fallback["focus_topic"],
        "comparison_targets": comparison_targets,
        "must_include": must_include[:5],
        "must_avoid": must_avoid[:4],
        "answer_strategy": answer_strategy or fallback["answer_strategy"],
    }


def _should_use_llm_explore_plan(prompt: str) -> bool:
    question_type = _detect_explore_kind(prompt)
    prompt_length = len(normalize_text(prompt).split())
    if question_type in {"definition", "comparison", "mechanism", "structure"} and prompt_length <= 18:
        return False
    return True


async def _build_explore_plan(prompt: str, focus_topic: str) -> dict[str, Any]:
    fallback = _heuristic_explore_plan(prompt, focus_topic)
    if not _should_use_llm_explore_plan(prompt):
        return fallback
    try:
        raw_plan = await gemini.generate_json(
            build_explore_query_plan_prompt(
                prompt=prompt,
            )
        )
    except Exception as exc:
        print(f"[explore] Query plan generation failed, using heuristic plan: {exc}")
        return fallback
    return _normalize_explore_plan(raw_plan, prompt, focus_topic)


def _build_explore_brief(prompt: str, focus_topic: str, plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "question_type": plan.get("question_type") or "general",
        "main_question": normalize_text(str(plan.get("main_question") or prompt)),
        "focus_topic": normalize_topic_phrase(str(plan.get("focus_topic") or focus_topic)),
        "focus_keywords": _focus_keywords(focus_topic or prompt),
        "comparison_targets": plan.get("comparison_targets") or [],
        "must_include": plan.get("must_include") or [],
        "must_avoid": plan.get("must_avoid") or [],
        "answer_strategy": normalize_text(str(plan.get("answer_strategy") or "")),
        "response_blocks": [
            "summary_theory_overview",
            "key_points_knowledge_takeaways",
            "detailed_sections_deep_explanation",
            "references_rendered_separately",
        ],
    }


def _should_generate_explore_blueprint(plan: dict[str, Any], prompt: str) -> bool:
    question_type = normalize_text(str(plan.get("question_type") or "")).lower()
    prompt_length = len(normalize_text(prompt).split())
    if prompt_length <= 2:
        return False
    if question_type in {"definition", "comparison", "mechanism", "structure"}:
        return True
    return prompt_length >= 4


def _should_lookup_explore_sources(plan: dict[str, Any], prompt: str) -> bool:
    question_type = normalize_text(str(plan.get("question_type") or "")).lower()
    prompt_length = len(normalize_text(prompt).split())
    if prompt_length <= 2:
        return False
    if question_type in {"definition", "comparison", "mechanism", "structure"}:
        return True
    return prompt_length >= 4


def _build_explore_source_brief(
    prompt: str,
    focus_topic: str,
    plan: dict[str, Any],
    sources: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "user_prompt": prompt,
        "focus_topic": focus_topic,
        "question_type": plan.get("question_type") or "general",
        "comparison_targets": plan.get("comparison_targets") or [],
        "source_count": len(sources),
        "reference_policy": {
            "rendered_separately_in_ui": True,
            "model_must_not_output_urls": True,
            "model_must_not_invent_citations": True,
        },
        "sources": sources,
    }


def _normalize_result_title(raw_title: object, fallback_title: str) -> str:
    title = normalize_topic_phrase(str(raw_title or "")).strip(" .")
    if not title or title.endswith("?"):
        return fallback_title
    return title


def _build_compact_result_title(raw_title: object, fallback_title: str) -> str:
    title = build_core_title(str(raw_title or ""), "")
    return title or build_core_title(fallback_title, "Khám phá chủ đề")


def _merge_explore_result(
    ai_result: object,
    fallback_payload: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(fallback_payload)
    raw = ai_result if isinstance(ai_result, dict) else {}

    title = normalize_text(str(raw.get("title") or ""))
    if title and not title.endswith("?"):
        merged["title"] = title

    summary = normalize_multiline_text(raw.get("summary"))
    if summary:
        merged["summary"] = summary

    key_points = _normalize_key_points(raw.get("key_points"))
    if key_points:
        merged["key_points"] = key_points

    topic_tags = _normalize_topic_tag_list(raw.get("topic_tags"), merged.get("title") or fallback_payload["title"])
    if topic_tags:
        merged["topic_tags"] = topic_tags

    fallback_sections = fallback_payload.get("detailed_sections") or {}
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
                "content": normalize_multiline_text(raw_section.get("content"))
                or normalize_text(str(fallback_section.get("content") or "")),
            }
    merged["detailed_sections"] = merged_sections

    adaptation = raw.get("teaching_adaptation")
    fallback_adaptation = fallback_payload.get("teaching_adaptation") or {}
    if isinstance(adaptation, dict):
        merged["teaching_adaptation"] = {
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
        }

    return merged


async def _rewrite_explore_result(
    *,
    prompt: str,
    focus_topic: str,
    learner_context: dict[str, str],
    explore_brief: dict[str, Any],
    source_brief: dict[str, Any],
    content_blueprint: dict[str, str],
    ai_result: dict[str, Any],
) -> dict[str, Any] | None:
    try:
        repaired = await gemini.generate_json(
            build_explore_repair_prompt(
                prompt=prompt,
                focus_topic=focus_topic,
                learner_context=learner_context,
                explore_brief=explore_brief,
                source_brief=source_brief,
                content_blueprint=content_blueprint,
                weak_draft=ai_result,
            )
        )
    except Exception as exc:
        print(f"[explore] Explore repair failed, keeping salvage path: {exc}")
        return None
    return repaired if isinstance(repaired, dict) else None


def _legacy_v2_extract_knowledge_detail_data(
    ai_result: dict[str, Any],
    fallback_payload: dict[str, Any],
) -> dict[str, Any]:
    detailed_sections = ai_result.get("detailed_sections")
    if not isinstance(detailed_sections, dict):
        return fallback_payload

    normalized_sections: dict[str, dict[str, str]] = {}
    for key in SECTION_ORDER:
        raw_section = detailed_sections.get(key)
        raw_title = normalize_text(str((raw_section or {}).get("title") or ""))
        content = ""
        if isinstance(raw_section, dict):
            content = normalize_multiline_text(raw_section.get("content"))
        fallback_section = fallback_payload["detailed_sections"][key]
        if len(content) < 70 or _looks_generic_text(content):
            content = fallback_section["content"]
        normalized_sections[key] = {
            "title": raw_title or fallback_section["title"],
            "content": content,
        }

    adaptation = ai_result.get("teaching_adaptation")
    fallback_adaptation = fallback_payload["teaching_adaptation"]
    if not isinstance(adaptation, dict):
        adaptation = {}

    return {
        "title": fallback_payload["title"],
        "summary": normalize_multiline_text(ai_result.get("summary")) or fallback_payload["summary"],
        "key_points": _normalize_key_points(ai_result.get("key_points")) or fallback_payload["key_points"],
        "topic_tags": _normalize_topic_tag_list(ai_result.get("topic_tags"), fallback_payload["title"]),
        "detailed_sections": normalized_sections,
        "teaching_adaptation": {
            "focus_priority": normalize_text(
                str(adaptation.get("focus_priority") or fallback_adaptation["focus_priority"])
            ),
            "tone": normalize_text(str(adaptation.get("tone") or fallback_adaptation["tone"])),
            "depth_control": normalize_text(
                str(adaptation.get("depth_control") or fallback_adaptation["depth_control"])
            ),
            "example_strategy": normalize_text(
                str(adaptation.get("example_strategy") or fallback_adaptation["example_strategy"])
            ),
        },
    }


def _legacy_v2_raw_explore_result_needs_rewrite(
    focus_topic: str,
    prompt: str,
    ai_result: dict[str, Any],
) -> bool:
    title = normalize_text(str(ai_result.get("title") or ""))
    summary = normalize_multiline_text(ai_result.get("summary"))
    key_points = _normalize_key_points(ai_result.get("key_points"))
    sections = ai_result.get("detailed_sections")
    combined = " ".join([title, summary, *key_points])

    if not title or title.endswith("?"):
        return True
    if len(key_points) < 4:
        return True
    if len(summary) < 120 or _summary_bullet_count(summary) < 4:
        return True
    first_summary_bullet = normalize_text(summary.splitlines()[0].lstrip("-*• ")) if summary.splitlines() else ""
    if first_summary_bullet and not _is_direct_explore_answer(prompt, focus_topic, first_summary_bullet):
        return True
    if _focus_overlap_ratio(combined, focus_topic) < 0.34:
        return True
    if _looks_generic_text(summary):
        return True
    if not isinstance(sections, dict):
        return True

    weak_sections = 0
    core_content = ""
    mechanism_content = ""
    relationship_content = ""
    for key in SECTION_ORDER:
        content = normalize_multiline_text((sections.get(key) or {}).get("content"))
        if key == "core_concept":
            core_content = content
        elif key == "mechanism":
            mechanism_content = content
        elif key == "components_and_relationships":
            relationship_content = content
        if len(content) < 70 or _looks_generic_text(content):
            weak_sections += 1

    if len(core_content) < 70 or len(mechanism_content) < 70:
        return True
    if not _is_direct_explore_answer(prompt, focus_topic, core_content):
        return True
    if _focus_overlap_ratio(core_content, focus_topic) < 0.34:
        return True
    if _focus_overlap_ratio(mechanism_content, focus_topic) < 0.30:
        return True
    if relationship_content and _focus_overlap_ratio(relationship_content, focus_topic) < 0.26:
        return True
    if weak_sections >= 3:
        return True

    compare_subjects = _parse_compare_subjects(prompt)
    if compare_subjects:
        lowered = strip_accents(" ".join([combined, core_content, mechanism_content, relationship_content])).lower()
        if not all(strip_accents(subject).lower() in lowered for subject in compare_subjects):
            return True

    return False


def _legacy_violates_explore_plan(ai_result: dict[str, Any], plan: dict[str, Any]) -> bool:
    must_include = [
        normalize_topic_phrase(str(item))
        for item in plan.get("must_include", [])
        if str(item).strip()
    ]
    if not must_include:
        return False

    sections = ai_result.get("detailed_sections") or {}
    combined = normalize_text(
        " ".join(
            [
                str(ai_result.get("title") or ""),
                str(ai_result.get("summary") or ""),
                " ".join(str(item) for item in ai_result.get("key_points") or []),
                str((sections.get("core_concept") or {}).get("content") or ""),
                str((sections.get("mechanism") or {}).get("content") or ""),
                str((sections.get("components_and_relationships") or {}).get("content") or ""),
            ]
        )
    )
    haystack = strip_accents(combined).lower()

    if plan.get("question_type") == "comparison":
        targets = [strip_accents(item).lower() for item in plan.get("comparison_targets", []) if item]
        if targets and not all(target in haystack for target in targets):
            return True

    covered = sum(1 for item in must_include if strip_accents(item).lower() in haystack)
    return covered < min(2, len(must_include))


def _build_fallback_payload(prompt: str, learner_context: dict[str, str]) -> dict[str, Any]:
    title = _build_compact_explore_title(prompt, prompt)
    question_type = _detect_explore_kind(prompt)
    compare_subjects = list(_parse_compare_subjects(prompt) or ())
    content_blueprint = build_blueprint_fallback(
        title=title,
        question_type=question_type,
        learner_context=learner_context,
        comparison_targets=compare_subjects,
    )
    section_briefs = build_section_briefs(
        content_blueprint,
        title=title,
        question_type=question_type,
        mode="explore",
        main_question=prompt,
        focus_topic=title,
        comparison_targets=compare_subjects,
    )
    if question_type == "structure":
        structure_summary = [
            normalize_text(content_blueprint.get("components", "")),
            normalize_text(content_blueprint.get("core_definition", "")),
            normalize_text(content_blueprint.get("mechanism", "")),
            normalize_text(content_blueprint.get("conditions_and_limits", "")),
        ]
        section_briefs["overview"] = [item for item in structure_summary if item][:4]
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
    return {
        "title": title,
        "summary": build_summary_from_briefs(section_briefs, key="overview"),
        "key_points": build_key_points_from_briefs(section_briefs),
        "topic_tags": normalize_topic_tags([], title),
        "content_blueprint": content_blueprint,
        "section_briefs": section_briefs,
        "active_section_keys": list(SECTION_ORDER),
        "detailed_sections": _build_blueprint_sections(title, content_blueprint),
        "teaching_adaptation": {
            "focus_priority": f"Bám sát câu hỏi gốc về {title}",
            "tone": "Rõ ràng, trực diện, ưu tiên bản chất trước",
            "depth_control": "Đi từ tổng quan sang cơ chế, cấu trúc, ví dụ và giới hạn áp dụng",
            "example_strategy": _build_example_context(learner_context),
        },
    }


def _legacy_extract_knowledge_detail_data(
    ai_result: dict[str, Any],
    fallback_payload: dict[str, Any],
    *,
    content_blueprint: dict[str, str],
    section_briefs: dict[str, list[str]],
    title: str,
) -> dict[str, Any]:
    normalized_sections, active_section_keys = normalize_detailed_sections(
        ai_result.get("detailed_sections"),
        fallback_sections=fallback_payload.get("detailed_sections") or {},
        blueprint=content_blueprint,
        title=title,
    )

    adaptation = ai_result.get("teaching_adaptation")
    fallback_adaptation = fallback_payload["teaching_adaptation"]
    if not isinstance(adaptation, dict):
        adaptation = {}

    return {
        "title": title,
        "summary": _build_detail_summary_from_sections(
            normalized_sections,
            build_summary_from_briefs(
                section_briefs,
                key="detail_focus",
                fallback_text=fallback_payload.get("summary") or "",
            ),
        ),
        "key_points": _normalize_explore_output_key_points(
            ai_result.get("key_points"),
            build_key_points_from_briefs(
                section_briefs,
                fallback_payload.get("key_points") or [],
            ),
            prompt=title,
            focus_topic=title,
            detailed_sections=normalized_sections,
        ),
        "topic_tags": fallback_payload.get("topic_tags") or [],
        "content_blueprint": content_blueprint,
        "section_briefs": section_briefs,
        "active_section_keys": active_section_keys,
        "detailed_sections": normalized_sections,
        "teaching_adaptation": {
            "focus_priority": normalize_text(
                str(adaptation.get("focus_priority") or fallback_adaptation["focus_priority"])
            ),
            "tone": normalize_text(str(adaptation.get("tone") or fallback_adaptation["tone"])),
            "depth_control": normalize_text(
                str(adaptation.get("depth_control") or fallback_adaptation["depth_control"])
            ),
            "example_strategy": normalize_text(
                str(adaptation.get("example_strategy") or fallback_adaptation["example_strategy"])
            ),
        },
    }


def _legacy_raw_explore_result_needs_rewrite(
    focus_topic: str,
    prompt: str,
    ai_result: dict[str, Any],
) -> bool:
    title = normalize_text(str(ai_result.get("title") or ""))
    sections = ai_result.get("detailed_sections")
    if not title or title.endswith("?"):
        return True
    if not isinstance(sections, dict):
        return True

    core_content = normalize_multiline_text((sections.get("core_concept") or {}).get("content"))
    mechanism_content = normalize_multiline_text((sections.get("mechanism") or {}).get("content"))
    relationship_content = normalize_multiline_text(
        (sections.get("components_and_relationships") or {}).get("content")
    )
    misconception_content = normalize_multiline_text(
        (sections.get("common_misconceptions") or {}).get("content")
    )

    if len(core_content) < 70 or len(mechanism_content) < 70 or len(relationship_content) < 70:
        return True
    if _looks_generic_text(core_content) or _looks_generic_text(mechanism_content):
        return True
    if not _is_direct_explore_answer(prompt, focus_topic, core_content):
        return True
    if semantic_overlap_ratio(core_content, mechanism_content) > 0.62:
        return True
    if semantic_overlap_ratio(mechanism_content, relationship_content) > 0.62:
        return True
    if misconception_content and semantic_overlap_ratio(relationship_content, misconception_content) > 0.70:
        return True

    compare_subjects = _parse_compare_subjects(prompt)
    if compare_subjects:
        lowered = strip_accents(" ".join([title, core_content, mechanism_content, relationship_content])).lower()
        if not all(strip_accents(subject).lower() in lowered for subject in compare_subjects):
            return True

    return False


@router.post("/", response_model=ExploreResult)
async def explore_topic(
    request: ExploreRequest,
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> ExploreResult:
    svc = SupabaseService(supabase)
    start_time = perf_counter()
    profile = svc.ensure_profile(
        current_user["id"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        avatar_url=current_user.get("avatar_url"),
    )
    onboarding = svc.get_onboarding(current_user["id"])
    recent_sessions = svc.get_recent_learning_context(current_user["id"], limit=5)
    context_bundle = build_shared_ai_context(
        profile=profile,
        onboarding=onboarding,
        recent_sessions=recent_sessions,
    )

    learner_context: dict[str, Any] = dict(context_bundle["learner_context"])
    validated_prompt = _validate_explore_input(request.prompt)
    initial_focus_topic = normalize_topic_phrase(validated_prompt) or normalize_text(validated_prompt)
    explore_plan = await _build_explore_plan(validated_prompt, initial_focus_topic)
    focus_topic = (
        normalize_topic_phrase(str(explore_plan.get("focus_topic") or initial_focus_topic))
        or initial_focus_topic
    )

    fallback_payload = _build_fallback_payload(validated_prompt, learner_context)
    fallback_payload["title"] = _build_compact_explore_title(validated_prompt, focus_topic)
    fallback_payload["topic_tags"] = normalize_topic_tags([], focus_topic or validated_prompt)
    fallback_payload["content_blueprint"] = build_blueprint_fallback(
        title=fallback_payload["title"],
        question_type=str(explore_plan.get("question_type") or "general"),
        learner_context=learner_context,
        comparison_targets=list(_parse_compare_subjects(validated_prompt) or ()),
    )
    fallback_payload["section_briefs"] = build_section_briefs(
        fallback_payload["content_blueprint"],
        title=fallback_payload["title"],
        question_type=str(explore_plan.get("question_type") or "general"),
        mode="explore",
        main_question=validated_prompt,
        focus_topic=focus_topic,
        comparison_targets=explore_plan.get("comparison_targets") or [],
    )
    if str(explore_plan.get("question_type") or "general") == "structure":
        fallback_payload["section_briefs"]["overview"] = [
            item
            for item in [
                normalize_text(fallback_payload["content_blueprint"].get("components", "")),
                normalize_text(fallback_payload["content_blueprint"].get("core_definition", "")),
                normalize_text(fallback_payload["content_blueprint"].get("mechanism", "")),
                normalize_text(fallback_payload["content_blueprint"].get("conditions_and_limits", "")),
            ]
            if item
        ][:4]
        fallback_payload["section_briefs"]["core_takeaways"] = [
            item
            for item in [
                normalize_text(fallback_payload["content_blueprint"].get("components", "")),
                normalize_text(fallback_payload["content_blueprint"].get("core_definition", "")),
                normalize_text(fallback_payload["content_blueprint"].get("mechanism", "")),
                normalize_text(fallback_payload["content_blueprint"].get("misconceptions", "")),
                normalize_text(fallback_payload["content_blueprint"].get("conditions_and_limits", "")),
            ]
            if item
        ][:5]
    fallback_payload["summary"] = build_summary_from_briefs(
        fallback_payload["section_briefs"],
        key="overview",
    )
    fallback_payload["key_points"] = build_key_points_from_briefs(
        fallback_payload["section_briefs"],
    )
    fallback_payload["detailed_sections"] = _build_blueprint_sections(
        fallback_payload["title"],
        fallback_payload["content_blueprint"],
    )

    explore_brief = _build_explore_brief(validated_prompt, focus_topic, explore_plan)
    verified_sources: list[dict[str, str]] = []
    if _should_lookup_explore_sources(explore_plan, validated_prompt):
        source_task = asyncio.create_task(
            search_knowledge_sources(
                message=validated_prompt,
                focus_topic=focus_topic,
                evidence_targets=[
                    str(item) for item in explore_plan.get("must_include", []) if str(item).strip()
                ],
                limit=7,
            )
        )
        verified_sources = await resolve_source_lookup(source_task, flow_label="explore")
    evidence_sources, related_materials = split_sources_and_related_materials(verified_sources)
    source_brief = _build_explore_source_brief(
        validated_prompt,
        focus_topic,
        explore_plan,
        evidence_sources,
    )
    if _should_generate_explore_blueprint(explore_plan, validated_prompt):
        try:
            raw_blueprint = await gemini.generate_json(
                build_explore_blueprint_prompt(
                    prompt=validated_prompt,
                    focus_topic=focus_topic,
                    explore_brief=explore_brief,
                    source_brief=source_brief,
                )
            )
        except Exception as exc:
            print(f"[explore] Blueprint generation failed, using fallback blueprint: {exc}")
            raw_blueprint = fallback_payload.get("content_blueprint") or {}
    else:
        raw_blueprint = fallback_payload.get("content_blueprint") or {}

    content_blueprint = normalize_blueprint(
        raw_blueprint,
        fallback_blueprint=fallback_payload["content_blueprint"],
    )

    try:
        ai_result = await gemini.generate_json(
            build_explore_core_prompt(
                prompt=validated_prompt,
                focus_topic=focus_topic,
                learner_context=learner_context,
                explore_brief=explore_brief,
                source_brief=source_brief,
                content_blueprint=content_blueprint,
            )
        )
    except Exception as exc:
        print(f"[explore] Topic exploration failed, switching to salvage path: {exc}")
        ai_result = {}

    needs_rewrite = _raw_explore_result_needs_rewrite(
        focus_topic,
        validated_prompt,
        ai_result if isinstance(ai_result, dict) else {},
    ) or _violates_explore_plan(
        ai_result if isinstance(ai_result, dict) else {},
        explore_plan,
    )
    if needs_rewrite and isinstance(ai_result, dict) and ai_result:
        repaired_result = await _rewrite_explore_result(
            prompt=validated_prompt,
            focus_topic=focus_topic,
            learner_context=learner_context,
            explore_brief=explore_brief,
            source_brief=source_brief,
            content_blueprint=content_blueprint,
            ai_result=ai_result,
        )
        if repaired_result:
            ai_result = repaired_result

    fallback_used = _raw_explore_result_needs_rewrite(
        focus_topic,
        validated_prompt,
        ai_result if isinstance(ai_result, dict) else {},
    ) or _violates_explore_plan(
        ai_result if isinstance(ai_result, dict) else {},
        explore_plan,
    )
    if fallback_used:
        ai_result = _merge_explore_result(ai_result, fallback_payload)

    title = _build_compact_result_title(ai_result.get("title"), fallback_payload["title"])
    section_briefs = build_section_briefs(
        content_blueprint,
        title=title,
        question_type=str(explore_plan.get("question_type") or "general"),
        mode="explore",
        main_question=validated_prompt,
        focus_topic=focus_topic,
        comparison_targets=explore_plan.get("comparison_targets") or [],
    )
    if str(explore_plan.get("question_type") or "general") == "structure":
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
    summary = build_summary_from_briefs(
        section_briefs,
        key="overview",
        fallback_text=fallback_payload["summary"],
    )
    summary = _normalize_explore_summary(
        ai_result.get("summary"),
        ai_result.get("key_points"),
        summary,
        prompt=validated_prompt,
        focus_topic=focus_topic,
        detailed_sections=ai_result.get("detailed_sections"),
    )
    key_points = _normalize_explore_output_key_points(
        ai_result.get("key_points"),
        build_key_points_from_briefs(
            section_briefs,
            fallback_payload["key_points"],
        ),
        prompt=validated_prompt,
        focus_topic=focus_topic,
        detailed_sections=ai_result.get("detailed_sections"),
    )
    knowledge_detail_data = _extract_knowledge_detail_data(
        ai_result,
        fallback_payload,
        content_blueprint=content_blueprint,
        section_briefs=section_briefs,
        title=title,
    )

    topic_tags = _normalize_topic_tag_list(ai_result.get("topic_tags"), focus_topic or validated_prompt or title)
    if not topic_tags:
        topic_tags = _normalize_topic_tag_list(title, title)
    knowledge_detail_data["topic_tags"] = topic_tags

    mindmap_data = build_explore_mindmap(title, knowledge_detail_data)
    context_usage = build_context_usage_trace(
        learner_context=learner_context,
        rendered_texts=[
            summary,
            " ".join(key_points),
            str(
                ((knowledge_detail_data.get("detailed_sections") or {}).get("persona_based_example") or {}).get(
                    "content"
                )
                or ""
            ),
        ],
    )
    request_payload = {
        "prompt": request.prompt,
        "normalized_prompt": validated_prompt,
        "context_policy": DEFAULT_CONTEXT_POLICY,
        "related_materials": related_materials,
    }
    context_snapshot = {
        "learner_context": learner_context,
        "profile_digest": context_bundle["profile_digest"],
        "context_policy": DEFAULT_CONTEXT_POLICY,
        "focus_topic": focus_topic,
        "explore_plan": explore_plan,
        "explore_brief": explore_brief,
    }
    generation_trace = {
        "session_subtype": "overview",
        "question_type": explore_plan.get("question_type"),
        "focus_topic": focus_topic,
        "learner_context_digest": learner_context,
        "context_usage": context_usage,
        "context_policy": DEFAULT_CONTEXT_POLICY,
        "source_lookup_plan": {
            "should_lookup": _should_lookup_explore_sources(explore_plan, validated_prompt),
            "source_count": len(verified_sources),
        },
        "chosen_sources": evidence_sources,
        "related_materials": related_materials,
        "rewrite_used": bool(needs_rewrite),
        "fallback_used": bool(fallback_used),
        "model_name": getattr(gemini, "_configured_model_name", None) or "gemini-2.5-flash",
        "latency_ms": int((perf_counter() - start_time) * 1000),
    }

    session = svc.create_session(
        current_user["id"],
        {
            "session_type": "explore",
            "session_subtype": "overview",
            "title": title,
            "user_input": request.prompt,
            "topic_tags": topic_tags,
            "summary": summary,
            "key_points": key_points,
            "infographic_data": knowledge_detail_data,
            "mindmap_data": mindmap_data,
            "sources": evidence_sources,
            "language": request.language,
            "duration_ms": int((perf_counter() - start_time) * 1000),
            "request_payload": request_payload,
            "context_snapshot": context_snapshot,
            "generation_trace": generation_trace,
        },
    )
    session_id = session.get("id") if isinstance(session, dict) else None
    save_metadata = session.get("_save_metadata") if isinstance(session, dict) else None

    return ExploreResult(
        session_id=session_id,
        title=title,
        summary=summary,
        key_points=key_points,
        knowledge_detail_data=knowledge_detail_data,
        topic_tags=topic_tags,
        mindmap_data=mindmap_data,
        sources=evidence_sources,
        related_materials=related_materials,
        save_metadata=save_metadata,
    )


def _repair_explore_sections(
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
        current_content = normalize_multiline_text(current_section.get("content"))
        minimum_length = 70 if key in critical_keys else 48
        if (
            len(current_content) < minimum_length
            or (key in critical_keys and _looks_generic_text(current_content))
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
        left_content = normalize_multiline_text((normalized_sections.get(left_key) or {}).get("content"))
        right_content = normalize_multiline_text((normalized_sections.get(right_key) or {}).get("content"))
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


def _extract_knowledge_detail_data(
    ai_result: dict[str, Any],
    fallback_payload: dict[str, Any],
    *,
    content_blueprint: dict[str, str],
    section_briefs: dict[str, list[str]],
    title: str,
) -> dict[str, Any]:
    normalized_sections, active_section_keys = _repair_explore_sections(
        ai_result.get("detailed_sections"),
        fallback_sections=fallback_payload.get("detailed_sections") or {},
        content_blueprint=content_blueprint,
        title=title,
    )

    adaptation = ai_result.get("teaching_adaptation")
    fallback_adaptation = fallback_payload["teaching_adaptation"]
    if not isinstance(adaptation, dict):
        adaptation = {}

    return {
        "title": title,
        "summary": _build_detail_summary_from_sections(
            normalized_sections,
            build_summary_from_briefs(
                section_briefs,
                key="detail_focus",
                fallback_text=fallback_payload.get("summary") or "",
            ),
        ),
        "key_points": _normalize_explore_output_key_points(
            ai_result.get("key_points"),
            build_key_points_from_briefs(
                section_briefs,
                fallback_payload.get("key_points") or [],
            ),
            prompt=title,
            focus_topic=title,
            detailed_sections=normalized_sections,
        ),
        "topic_tags": fallback_payload.get("topic_tags") or [],
        "content_blueprint": content_blueprint,
        "section_briefs": section_briefs,
        "active_section_keys": active_section_keys,
        "detailed_sections": normalized_sections,
        "teaching_adaptation": {
            "focus_priority": normalize_text(
                str(adaptation.get("focus_priority") or fallback_adaptation["focus_priority"])
            ),
            "tone": normalize_text(str(adaptation.get("tone") or fallback_adaptation["tone"])),
            "depth_control": normalize_text(
                str(adaptation.get("depth_control") or fallback_adaptation["depth_control"])
            ),
            "example_strategy": normalize_text(
                str(adaptation.get("example_strategy") or fallback_adaptation["example_strategy"])
            ),
        },
    }


def _raw_explore_result_needs_rewrite(
    focus_topic: str,
    prompt: str,
    ai_result: dict[str, Any],
) -> bool:
    title = normalize_text(str(ai_result.get("title") or ""))
    summary_lines = _summary_lines(ai_result.get("summary"))
    key_points = _normalize_key_points(ai_result.get("key_points"))
    sections = ai_result.get("detailed_sections")
    if not title or title.endswith("?"):
        return True
    if not isinstance(sections, dict):
        return True

    question_type = _detect_explore_kind(prompt)
    core_content = normalize_multiline_text((sections.get("core_concept") or {}).get("content"))
    mechanism_content = normalize_multiline_text((sections.get("mechanism") or {}).get("content"))
    relationship_content = normalize_multiline_text(
        (sections.get("components_and_relationships") or {}).get("content")
    )

    if len(core_content) < 60 or _looks_generic_text(core_content):
        return True
    if not _is_direct_explore_answer(prompt, focus_topic, core_content):
        return True
    if mechanism_content and _looks_generic_text(mechanism_content):
        return True
    if summary_lines:
        if len(summary_lines) < 3:
            return True
        if not _is_direct_explore_answer(prompt, focus_topic, summary_lines[0]):
            return True
    if key_points and _key_points_need_fallback(prompt, focus_topic, key_points):
        return True

    weak_sections = sum(
        1
        for content in (core_content, mechanism_content, relationship_content)
        if len(content) < 50 or _looks_generic_text(content) or _contains_trailing_ellipsis(content)
    )
    if weak_sections >= 2:
        return True
    if core_content and mechanism_content and semantic_overlap_ratio(core_content, mechanism_content) > 0.84:
        return True
    if (
        question_type == "structure"
        and _focus_overlap_ratio(relationship_content, focus_topic) < 0.28
    ):
        return True

    compare_subjects = _parse_compare_subjects(prompt)
    if compare_subjects:
        lowered = strip_accents(" ".join([title, core_content, mechanism_content, relationship_content])).lower()
        if not all(strip_accents(subject).lower() in lowered for subject in compare_subjects):
            return True

    return False


def _violates_explore_plan(ai_result: dict[str, Any], plan: dict[str, Any]) -> bool:
    must_include = [
        normalize_topic_phrase(str(item))
        for item in plan.get("must_include", [])
        if str(item).strip()
    ]
    if not must_include:
        return False

    sections = ai_result.get("detailed_sections") or {}
    combined = normalize_text(
        " ".join(
            [
                str(ai_result.get("title") or ""),
                str(ai_result.get("summary") or ""),
                " ".join(str(item) for item in ai_result.get("key_points") or []),
                str((sections.get("core_concept") or {}).get("content") or ""),
                str((sections.get("mechanism") or {}).get("content") or ""),
                str((sections.get("components_and_relationships") or {}).get("content") or ""),
            ]
        )
    )
    haystack = strip_accents(combined).lower()

    if plan.get("question_type") == "comparison":
        targets = [strip_accents(item).lower() for item in plan.get("comparison_targets", []) if item]
        if targets and not all(target in haystack for target in targets):
            return True

    covered = sum(1 for item in must_include if strip_accents(item).lower() in haystack)
    return covered < min(2, len(must_include))

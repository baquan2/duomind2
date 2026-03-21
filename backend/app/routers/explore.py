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
from app.utils.source_references import resolve_source_lookup


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


def _detect_explore_kind(prompt: str) -> str:
    lowered = strip_accents(normalize_text(prompt)).lower()
    if _parse_compare_subjects(prompt):
        return "comparison"
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
    if question_type == "mechanism":
        return _focus_overlap_ratio(lead, focus_topic) >= 0.34 and any(
            marker in f" {lead} "
            for marker in (" hoat dong ", " van hanh ", " dien ra ", " bat dau ")
        )
    return _focus_overlap_ratio(lead, focus_topic) >= 0.34


def _key_points_need_fallback(prompt: str, focus_topic: str, key_points: list[str]) -> bool:
    if len(key_points) < 5:
        return True

    compare_subjects = _parse_compare_subjects(prompt)
    useful_points = 0
    generic_points = 0
    compare_points = 0

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


def _build_fallback_payload(prompt: str, learner_context: dict[str, str]) -> dict[str, Any]:
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


def _build_explore_plan(prompt: str, focus_topic: str) -> dict[str, Any]:
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


def _extract_knowledge_detail_data(
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


def _raw_explore_result_needs_rewrite(
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
    )
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


def _extract_knowledge_detail_data(
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
        "summary": build_summary_from_briefs(
            section_briefs,
            key="detail_focus",
            fallback_text=fallback_payload.get("summary") or "",
        ),
        "key_points": build_key_points_from_briefs(
            section_briefs,
            fallback_payload.get("key_points") or [],
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
    svc.ensure_profile(
        current_user["id"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        avatar_url=current_user.get("avatar_url"),
    )

    try:
        onboarding = svc.get_onboarding(current_user["id"])
    except Exception:
        onboarding = None

    learner_context = build_prompt_learning_context(get_user_context(onboarding))
    validated_prompt = _validate_explore_input(request.prompt)
    initial_focus_topic = normalize_topic_phrase(validated_prompt) or normalize_text(validated_prompt)
    explore_plan = _build_explore_plan(validated_prompt, initial_focus_topic)
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
    )
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
    source_task = asyncio.create_task(
        search_knowledge_sources(
            message=validated_prompt,
            focus_topic=focus_topic,
            evidence_targets=[
                str(item) for item in explore_plan.get("must_include", []) if str(item).strip()
            ],
        )
    )
    verified_sources = await resolve_source_lookup(source_task, flow_label="explore")
    source_brief = _build_explore_source_brief(
        validated_prompt,
        focus_topic,
        explore_plan,
        verified_sources,
    )
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
        print(f"[explore] Topic exploration failed, using fallback: {exc}")
        ai_result = fallback_payload

    if _raw_explore_result_needs_rewrite(focus_topic, validated_prompt, ai_result) or _violates_explore_plan(
        ai_result,
        explore_plan,
    ):
        ai_result = fallback_payload

    title = _build_compact_result_title(ai_result.get("title"), fallback_payload["title"])
    section_briefs = build_section_briefs(
        content_blueprint,
        title=title,
        question_type=str(explore_plan.get("question_type") or "general"),
        mode="explore",
    )
    summary = build_summary_from_briefs(
        section_briefs,
        key="overview",
        fallback_text=fallback_payload["summary"],
    )
    key_points = build_key_points_from_briefs(
        section_briefs,
        fallback_payload["key_points"],
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

    session = svc.create_session(
        current_user["id"],
        {
            "session_type": "explore",
            "title": title,
            "user_input": validated_prompt,
            "topic_tags": topic_tags,
            "summary": summary,
            "key_points": key_points,
            "infographic_data": knowledge_detail_data,
            "mindmap_data": mindmap_data,
            "sources": verified_sources,
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
        sources=verified_sources,
    )

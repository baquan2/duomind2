from __future__ import annotations

import re
from typing import Any, Iterable, Mapping

from app.utils.helpers import normalize_text, normalize_topic_phrase, strip_accents


BLUEPRINT_KEYS = (
    "core_definition",
    "scope_boundary",
    "mechanism",
    "components",
    "input_process_output",
    "example",
    "application",
    "misconceptions",
    "conditions_and_limits",
    "related_concepts",
    "decision_value",
)

SECTION_BRIEF_KEYS = (
    "overview",
    "core_takeaways",
    "detail_focus",
    "exploration",
)

SECTION_ORDER = (
    "core_concept",
    "mechanism",
    "components_and_relationships",
    "persona_based_example",
    "real_world_applications",
    "common_misconceptions",
    "next_step_self_study",
)

LOW_VALUE_PHRASES = (
    "day la mot khia canh quan trong",
    "day la mot chu de quan trong",
    "day la mot khai niem quan trong",
    "giup hieu ro hon",
    "can nam ban chat",
    "co the ap dung trong nhieu linh vuc",
    "nguoi hoc nen",
    "dieu quan trong la",
    "o goc nhin",
    "giup ban co goc nhin",
    "can tim hieu them",
    "la mot phan khong the thieu",
)

TOKEN_STOPWORDS = {
    "la",
    "gi",
    "va",
    "voi",
    "mot",
    "nhung",
    "cua",
    "cho",
    "khi",
    "neu",
    "thi",
    "de",
    "duoc",
    "trong",
    "tren",
    "tu",
    "nay",
    "do",
    "can",
    "nen",
    "hay",
    "theo",
    "nhu",
    "nao",
    "giai",
    "thich",
    "phan",
    "tich",
    "tim",
    "hieu",
    "tong",
    "quan",
    "kien",
    "thuc",
    "chi",
    "tiet",
}


def clip_words(text: str, max_words: int) -> str:
    words = normalize_text(text).split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(" ,;:.") + "..."


def bullet_text_to_list(text: object, limit: int = 5) -> list[str]:
    if isinstance(text, list):
        items = [normalize_text(str(item)) for item in text]
    else:
        items = [
            normalize_text(line.lstrip("-*• ").strip())
            for line in str(text or "").splitlines()
        ]
    return [item for item in items if item][:limit]


def bullet_list_to_text(items: Iterable[str], limit: int = 4) -> str:
    bullets = [normalize_text(item) for item in items if normalize_text(item)]
    return "\n".join(f"- {item}" for item in bullets[:limit])


def extract_sentences(text: str, limit: int = 2) -> list[str]:
    return [
        normalize_text(part)
        for part in re.split(r"(?<=[.!?])\s+|\n+", normalize_text(text))
        if normalize_text(part)
    ][:limit]


def is_generic_knowledge_text(text: object) -> bool:
    normalized = normalize_text(str(text or ""))
    if not normalized:
        return True

    lowered = strip_accents(normalized).lower()
    if any(phrase in lowered for phrase in LOW_VALUE_PHRASES):
        return True

    tokens = semantic_tokens(normalized)
    if len(tokens) < 6:
        return True

    weak_markers = ("quan trong", "hieu ro", "ban chat", "tong quan", "goc nhin")
    weak_hits = sum(1 for marker in weak_markers if marker in lowered)
    return weak_hits >= 3


def semantic_tokens(text: object) -> set[str]:
    normalized = strip_accents(normalize_text(str(text or ""))).lower()
    tokens = re.findall(r"[0-9a-z]+", normalized)
    return {
        token
        for token in tokens
        if len(token) >= 3 and token not in TOKEN_STOPWORDS and not token.isdigit()
    }


def semantic_overlap_ratio(left: object, right: object) -> float:
    left_tokens = semantic_tokens(left)
    right_tokens = semantic_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens))


def dedupe_ideas(items: Iterable[str], *, limit: int, max_overlap: float = 0.45) -> list[str]:
    unique: list[str] = []
    for item in items:
        cleaned = normalize_text(item)
        if not cleaned:
            continue
        if any(semantic_overlap_ratio(cleaned, existing) > max_overlap for existing in unique):
            continue
        unique.append(cleaned)
        if len(unique) >= limit:
            break
    return unique[:limit]


def _example_context(learner_context: Mapping[str, Any] | None) -> str:
    if not isinstance(learner_context, Mapping):
        return "một tình huống học tập hoặc công việc cụ thể"
    target_role = normalize_text(str(learner_context.get("target_role") or ""))
    current_focus = normalize_text(str(learner_context.get("current_focus") or ""))
    if target_role and current_focus:
        return f"một tình huống gần với người học đang hướng tới {target_role} và tập trung vào {current_focus}"
    if target_role:
        return f"một tình huống gần với người học đang hướng tới {target_role}"
    return "một tình huống học tập hoặc công việc cụ thể"


def build_blueprint_fallback(
    *,
    title: str,
    question_type: str,
    learner_context: Mapping[str, Any] | None = None,
    comparison_targets: Iterable[str] | None = None,
    analysis_content: str | None = None,
) -> dict[str, str]:
    clean_title = normalize_topic_phrase(title) or normalize_text(title) or "chủ đề chính"
    compare_targets = [normalize_topic_phrase(item) for item in (comparison_targets or []) if normalize_text(str(item))]
    if question_type == "comparison" and len(compare_targets) >= 2:
        first, second = compare_targets[:2]
        return {
            "core_definition": (
                f"{first} và {second} khác nhau ở bài toán chính cần giải, loại đầu ra tạo ra, và cách mỗi bên dùng thông tin để ra quyết định."
            ),
            "scope_boundary": (
                f"Không nên chỉ so {first} và {second} bằng tên gọi. Cần đặt cả hai lên cùng một bộ tiêu chí: mục tiêu, đầu ra, nguồn thông tin, và bối cảnh áp dụng."
            ),
            "mechanism": (
                f"{first} thường bắt đầu từ vấn đề cần làm rõ và chuyển thành requirement, quy trình, hoặc phạm vi cần chốt. {second} thường bắt đầu từ dấu hiệu, dữ liệu, hoặc kết quả quan sát để rút insight và đề xuất hành động."
            ),
            "components": (
                f"Có thể tách {first} và {second} trên ba trục: mục tiêu công việc, đầu ra chính, và nguồn thông tin thường dùng. Nhìn trên ba trục này sẽ thấy điểm giống bề mặt và điểm khác thực sự."
            ),
            "input_process_output": (
                f"Đầu vào của {first} thường là nhu cầu, stakeholder, và requirement thô. Xử lý là làm rõ logic và quy trình. Đầu ra là đặc tả, luồng xử lý, hoặc quyết định phạm vi. Đầu vào của {second} thường là metric, hành vi, hoặc dữ liệu sản phẩm. Xử lý là phân tích và đối chiếu. Đầu ra là insight và đề xuất."
            ),
            "example": (
                f"Trong {_example_context(learner_context)}, nếu một người đang làm rõ requirement, vẽ luồng xử lý, và chốt điều kiện bàn giao thì nghiêng về {first}. Nếu người đó đang đọc metric, tìm nguyên nhân biến động, và đề xuất thay đổi dựa trên dữ liệu thì nghiêng về {second}."
            ),
            "application": (
                f"Kiến thức này giúp phân biệt đúng vai trò, giao đúng bài toán, và đọc đúng JD thay vì suy diễn theo tên gọi. Nó đặc biệt có giá trị khi cần chọn hướng học, phỏng vấn, hoặc phối hợp liên chức năng."
            ),
            "misconceptions": (
                f"Hiểu sai phổ biến là coi {first} và {second} chỉ là hai tên gọi khác nhau. Thực tế cần soi vào bài toán mà mỗi bên giải, đầu ra mà mỗi bên chịu trách nhiệm, và bằng chứng mà mỗi bên dùng hằng ngày."
            ),
            "conditions_and_limits": (
                f"Ranh giới giữa {first} và {second} có thể thay đổi theo công ty, nhưng ba trục mục tiêu, đầu ra, và bằng chứng vẫn là khung so sánh ổn định nhất. Nếu thiếu bối cảnh công việc cụ thể thì không nên kết luận quá mạnh."
            ),
            "related_concepts": (
                f"Dễ nhầm với các chức danh lai như Product Owner, Data Analyst, hoặc Business Systems Analyst. Muốn tách đúng phải quay về bài toán và đầu ra chứ không chỉ tên chức danh."
            ),
            "decision_value": (
                f"Hiểu đúng sự khác nhau giúp chọn đúng kỹ năng cần học, đặt câu hỏi đúng trong phỏng vấn, và phân bổ công việc hợp lý giữa {first} và {second}."
            ),
        }

    base_example = _example_context(learner_context)
    return {
        "core_definition": (
            f"{clean_title} là một khái niệm hoặc cơ chế có phạm vi áp dụng cụ thể. Muốn hiểu đúng cần trả lời rõ nó là gì, nó được dùng để giải bài toán nào, và nó không đồng nghĩa với khái niệm gần nó."
        ),
        "scope_boundary": (
            f"Ranh giới của {clean_title} nằm ở bối cảnh áp dụng, điều kiện để nó phát huy giá trị, và điểm khác với cách hiểu quá rộng. Không nên biến nó thành nhãn gọi chung cho cả một lĩnh vực."
        ),
        "mechanism": (
            f"Cơ chế của {clean_title} phải được nhìn theo logic vận hành: đầu vào là gì, xử lý ở giữa diễn ra như thế nào, và đầu ra tạo giá trị ra sao. Không hiểu cơ chế thì sẽ dễ nhầm giữa biểu hiện bên ngoài và nguyên lý bên trong."
        ),
        "components": (
            f"{clean_title} thường gồm các thành phần hoặc góc nhìn cần đặt cạnh nhau mới thấy được cấu trúc. Điều quan trọng không chỉ là nhớ tên từng phần mà là hiểu quan hệ giữa chúng và phần nào quyết định kết quả."
        ),
        "input_process_output": (
            f"Khi học {clean_title}, nên soi theo chuỗi đầu vào -> xử lý -> đầu ra. Chuỗi này giúp tách định nghĩa khỏi ví dụ và giúp kiểm tra xem một trường hợp mới có thật sự dùng đúng khái niệm hay không."
        ),
        "example": (
            f"Một ví dụ tốt cho {clean_title} nên dùng {_example_context(learner_context) or base_example} để cho thấy rõ dữ liệu nào được đưa vào, logic nào được dùng, và kết quả nào thay đổi sau khi áp dụng."
        ),
        "application": (
            f"Kiến thức về {clean_title} có giá trị khi cần giải thích hiện tượng, đánh giá lựa chọn, hoặc cải thiện cách ra quyết định trong học tập và công việc. Nó giúp chuyển từ học thuộc sang biết khi nào nên dùng và không nên dùng."
        ),
        "misconceptions": (
            f"Hiểu sai phổ biến với {clean_title} là nhớ ví dụ mà tưởng đã hiểu bản chất, hoặc đồng nhất kết quả quan sát được với cơ chế tạo ra kết quả đó. Cách sửa là quay về định nghĩa, cơ chế, và giới hạn áp dụng."
        ),
        "conditions_and_limits": (
            f"{clean_title} chỉ đúng khi đúng bối cảnh và điều kiện. Nếu thay đổi đầu vào, ràng buộc, hoặc mục tiêu thì cách áp dụng cũng thay đổi. Đây là lý do phải hiểu giới hạn thay vì học thuộc một công thức cố định."
        ),
        "related_concepts": (
            f"Dễ nhầm với các khái niệm nghe giống, nhưng khác ở mục tiêu, cơ chế, hoặc cấp độ sử dụng. Muốn tách đúng cần hỏi: nó được dùng để làm gì, vận hành ra sao, và quyết định nào phụ thuộc vào nó."
        ),
        "decision_value": (
            f"Hiểu đúng {clean_title} giúp đánh giá thông tin tốt hơn, giải thích vì sao một cách làm hiệu quả hoặc thất bại, và chọn đúng hướng hành động thay vì làm theo cảm tính."
        ),
    }


def normalize_blueprint(
    raw_blueprint: object,
    *,
    fallback_blueprint: Mapping[str, str],
) -> dict[str, str]:
    if not isinstance(raw_blueprint, Mapping):
        return {key: fallback_blueprint[key] for key in BLUEPRINT_KEYS}

    normalized: dict[str, str] = {}
    for key in BLUEPRINT_KEYS:
        value = normalize_text(str(raw_blueprint.get(key) or ""))
        if is_generic_knowledge_text(value):
            value = fallback_blueprint[key]
        normalized[key] = value or fallback_blueprint[key]
    return normalized


def build_section_briefs(
    blueprint: Mapping[str, str],
    *,
    title: str,
    question_type: str,
    mode: str,
) -> dict[str, list[str]]:
    _ = mode
    overview = dedupe_ideas(
        [
            normalize_text(blueprint.get("core_definition", "")),
            normalize_text(blueprint.get("scope_boundary", "")),
            normalize_text(blueprint.get("decision_value", "")),
            normalize_text(blueprint.get("application", "")),
        ],
        limit=4,
        max_overlap=0.40,
    )

    core_takeaways = dedupe_ideas(
        [
            normalize_text(blueprint.get("core_definition", "")),
            normalize_text(blueprint.get("mechanism", "")),
            normalize_text(blueprint.get("components", "")),
            normalize_text(blueprint.get("application", "")),
            normalize_text(blueprint.get("misconceptions", "")),
            normalize_text(blueprint.get("conditions_and_limits", "")),
        ],
        limit=5,
        max_overlap=0.38,
    )

    detail_focus = dedupe_ideas(
        [
            f"Cơ chế vận hành: {normalize_text(blueprint.get('mechanism', ''))}",
            f"Cấu trúc và quan hệ: {normalize_text(blueprint.get('components', ''))}",
            f"Đầu vào -> xử lý -> đầu ra: {normalize_text(blueprint.get('input_process_output', ''))}",
            f"Dùng khi / giới hạn: {normalize_text(blueprint.get('conditions_and_limits', ''))}",
        ],
        limit=4,
        max_overlap=0.42,
    )

    exploration_seed = [
        f"Nhầm lẫn phổ biến: {normalize_text(blueprint.get('misconceptions', ''))}",
        f"Dễ nhầm với: {normalize_text(blueprint.get('related_concepts', ''))}",
        f"Giá trị để ra quyết định: {normalize_text(blueprint.get('decision_value', ''))}",
        f"Câu hỏi mở rộng: So {title} với bối cảnh nào để thấy rõ ranh giới áp dụng?",
    ]
    if question_type == "comparison":
        exploration_seed[-1] = f"Câu hỏi mở rộng: Trong cùng một dự án, khi nào hai bên cần phối hợp thay vì thay thế nhau?"

    exploration = dedupe_ideas(exploration_seed, limit=4, max_overlap=0.42)

    return {
        "overview": overview,
        "core_takeaways": core_takeaways,
        "detail_focus": detail_focus,
        "exploration": exploration,
    }


def build_summary_from_briefs(
    section_briefs: Mapping[str, Any],
    *,
    key: str,
    fallback_text: str = "",
    limit: int = 4,
) -> str:
    items = bullet_text_to_list(section_briefs.get(key), limit=limit)
    if items:
        return bullet_list_to_text(items, limit=limit)
    return bullet_list_to_text(bullet_text_to_list(fallback_text, limit=limit), limit=limit)


def build_key_points_from_briefs(
    section_briefs: Mapping[str, Any],
    fallback_points: Iterable[str] | None = None,
    *,
    limit: int = 5,
) -> list[str]:
    items = bullet_text_to_list(section_briefs.get("core_takeaways"), limit=limit)
    if items:
        return items[:limit]
    return dedupe_ideas([normalize_text(str(item)) for item in (fallback_points or [])], limit=limit)


def _compose_section(parts: Iterable[str], *, max_words: int = 110) -> str:
    chosen: list[str] = []
    word_count = 0
    for part in parts:
        cleaned = normalize_text(part)
        if not cleaned:
            continue
        if any(semantic_overlap_ratio(cleaned, existing) > 0.72 for existing in chosen):
            continue
        part_word_count = len(cleaned.split())
        if chosen and word_count + part_word_count > max_words:
            break
        chosen.append(cleaned)
        word_count += part_word_count
    return normalize_text(" ".join(chosen))


def build_section_content_from_blueprint(
    section_key: str,
    *,
    title: str,
    blueprint: Mapping[str, str],
) -> str:
    if section_key == "core_concept":
        return _compose_section(
            [
                blueprint.get("core_definition", ""),
                blueprint.get("scope_boundary", ""),
                blueprint.get("decision_value", ""),
            ],
            max_words=120,
        )
    if section_key == "mechanism":
        return _compose_section(
            [
                blueprint.get("mechanism", ""),
                blueprint.get("input_process_output", ""),
                blueprint.get("conditions_and_limits", ""),
            ],
            max_words=120,
        )
    if section_key == "components_and_relationships":
        return _compose_section(
            [
                blueprint.get("components", ""),
                blueprint.get("mechanism", ""),
                blueprint.get("conditions_and_limits", ""),
            ],
            max_words=120,
        )
    if section_key == "persona_based_example":
        return _compose_section(
            [
                blueprint.get("example", ""),
                blueprint.get("application", ""),
            ],
            max_words=90,
        )
    if section_key == "real_world_applications":
        return _compose_section(
            [
                blueprint.get("application", ""),
                blueprint.get("decision_value", ""),
                blueprint.get("conditions_and_limits", ""),
            ],
            max_words=95,
        )
    if section_key == "common_misconceptions":
        return _compose_section(
            [
                blueprint.get("misconceptions", ""),
                blueprint.get("related_concepts", ""),
                blueprint.get("scope_boundary", ""),
            ],
            max_words=95,
        )
    return _compose_section(
        [
            f"Điểm cần nắm tiếp sau {title} là: {blueprint.get('conditions_and_limits', '')}",
            blueprint.get("related_concepts", ""),
            blueprint.get("decision_value", ""),
        ],
        max_words=80,
    )


def normalize_detailed_sections(
    raw_sections: object,
    *,
    fallback_sections: Mapping[str, Mapping[str, str]],
    blueprint: Mapping[str, str],
    title: str,
) -> tuple[dict[str, dict[str, str]], list[str]]:
    raw_mapping = raw_sections if isinstance(raw_sections, Mapping) else {}
    normalized: dict[str, dict[str, str]] = {}
    active_keys: list[str] = []
    kept_contents: list[str] = []

    for key in SECTION_ORDER:
        fallback_section = fallback_sections.get(key) or {}
        fallback_title = normalize_text(str(fallback_section.get("title") or key))
        fallback_content = normalize_text(
            str(fallback_section.get("content") or build_section_content_from_blueprint(key, title=title, blueprint=blueprint))
        )

        raw_section = raw_mapping.get(key) if isinstance(raw_mapping, Mapping) else None
        section_title = fallback_title
        section_content = ""
        if isinstance(raw_section, Mapping):
            section_title = normalize_text(str(raw_section.get("title") or fallback_title)) or fallback_title
            section_content = normalize_text(str(raw_section.get("content") or ""))

        if is_generic_knowledge_text(section_content) or len(section_content.split()) < 16:
            section_content = fallback_content

        if kept_contents and semantic_overlap_ratio(section_content, " ".join(kept_contents)) > 0.58:
            rebuilt = build_section_content_from_blueprint(key, title=title, blueprint=blueprint)
            if semantic_overlap_ratio(rebuilt, " ".join(kept_contents)) < semantic_overlap_ratio(section_content, " ".join(kept_contents)):
                section_content = rebuilt

        normalized[key] = {
            "title": section_title,
            "content": section_content or fallback_content,
        }

        if key == "next_step_self_study" and semantic_overlap_ratio(section_content, " ".join(kept_contents)) > 0.60:
            continue

        if key in {"persona_based_example", "real_world_applications"} and semantic_overlap_ratio(section_content, " ".join(kept_contents)) > 0.65:
            continue

        active_keys.append(key)
        kept_contents.append(section_content)

    if "core_concept" not in active_keys:
        active_keys.insert(0, "core_concept")
    if "mechanism" not in active_keys:
        active_keys.append("mechanism")
    if "components_and_relationships" not in active_keys:
        active_keys.append("components_and_relationships")

    deduped_active: list[str] = []
    for key in active_keys:
        if key in normalized and key not in deduped_active:
            deduped_active.append(key)

    return normalized, deduped_active

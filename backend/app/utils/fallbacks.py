from __future__ import annotations

import re
import unicodedata
from typing import Any


STOP_WORDS = {
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
    "that",
    "giai",
    "thich",
    "don",
    "gian",
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def split_sentences(text: str, limit: int = 5) -> list[str]:
    chunks = [
        normalize_text(part)
        for part in re.split(r"(?<=[.!?])\s+|\n+", text)
        if normalize_text(part)
    ]
    return chunks[:limit]


def sentence_case(text: str) -> str:
    normalized = normalize_text(text)
    if not normalized:
        return normalized
    return normalized[0].upper() + normalized[1:]


def infer_title(text: str, fallback: str) -> str:
    first_sentence = split_sentences(text, 1)
    if not first_sentence:
        return fallback
    title = first_sentence[0][:80].strip(" .:-")
    return sentence_case(title or fallback)


def infer_topic_from_prompt(prompt: str) -> str:
    cleaned = normalize_text(prompt).strip(" .?!")
    suffix_patterns = [
        r"\blà gì\b",
        r"\bhoạt động như thế nào\b",
        r"\bvận hành ra sao\b",
        r"\bvận hành như thế nào\b",
        r"\bra sao\b",
        r"\bnhư thế nào\b",
        r"\bthế nào\b",
    ]
    for pattern in suffix_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip(" .?!,:;-")
    if not cleaned:
        return "chủ đề mới"
    return sentence_case(cleaned)


def extract_key_points(text: str, limit: int = 5) -> list[str]:
    sentences = split_sentences(text, limit + 2)
    if sentences:
        return sentences[:limit]

    normalized = normalize_text(text)
    if not normalized:
        return ["Chưa có đủ dữ liệu để tạo ý chính."]
    return [normalized[:220]]


def extract_topic_tags(text: str, limit: int = 5) -> list[str]:
    cleaned = normalize_text(text)
    cleaned = re.sub(r"[#*_`~\[\]{}()<>?!]+", " ", cleaned)
    cleaned = re.sub(r"\s*[:|/,-]\s*", " ", cleaned)
    tokens = re.findall(r"[0-9A-Za-zÀ-ỹĐđ]+", cleaned, flags=re.UNICODE)

    seen: set[str] = set()
    result: list[str] = []
    for token in tokens:
        key = strip_accents(token).lower()
        if len(key) < 3 or key in STOP_WORDS or key.isdigit():
            continue
        if key in seen:
            continue
        seen.add(key)
        result.append(token.lower())
        if len(result) >= limit:
            break
    return result


def _build_long_paragraph(title: str, angle: str, focus: str, application: str) -> str:
    return (
        f"Ở góc nhìn {angle}, {title} không chỉ là một nhãn khái niệm mà là một phần của hệ thống tri thức có logic riêng. {focus} "
        f"Điều quan trọng là thấy được vì sao nội dung này xuất hiện, nó giải quyết vấn đề gì, và mối liên hệ của nó với các quyết định hoặc hiện tượng trong thực tế. {application}"
    )


def _build_direct_paragraph(opening: str, explanation: str, application: str) -> str:
    return f"{opening} {explanation} {application}"


def _compact_sentence(sentence: str, max_words: int = 8, max_chars: int = 54) -> str:
    normalized = normalize_text(sentence).strip(" .")
    first_clause = re.split(r"[:;,.]", normalized, maxsplit=1)[0].strip()
    if first_clause:
        normalized = first_clause
    words = normalized.split()
    shortened = " ".join(words[:max_words]).strip()
    if len(shortened) > max_chars:
        shortened = shortened[:max_chars].rstrip(" ,.;:")
    return shortened or normalized[:max_chars].rstrip(" ,.;:")


def _make_sub_point_from_sentence(
    sentence: str,
    fallback_label: str,
    fallback_description: str,
) -> dict[str, str]:
    normalized = normalize_text(sentence)
    return {
        "label": _compact_sentence(normalized, max_words=6, max_chars=34) or fallback_label,
        "full_label": normalized or fallback_description,
        "description": normalized[:110] or fallback_description,
        "details": normalized or fallback_description,
    }


def _create_mindmap_nodes_from_sections(
    title: str,
    sections: list[dict[str, str]],
) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = [
        {
            "id": "root",
            "type": "root",
            "data": {
                "label": title[:42],
                "full_label": title,
                "description": "Chủ đề trung tâm",
                "details": f"Sơ đồ này tóm lược những khía cạnh quan trọng nhất của chủ đề {title}.",
            },
            "position": {"x": 0, "y": 0},
        }
    ]
    edges: list[dict[str, Any]] = []

    palette = ["#0f766e", "#2563eb", "#7c3aed", "#ea580c", "#0891b2", "#be185d"]
    x_positions = [-520, -300, -80, 160, 400, 640]

    for index, section in enumerate(sections[:6]):
        main_id = f"main_{index}"
        x_pos = x_positions[index] if index < len(x_positions) else (index - 2) * 220

        nodes.append(
            {
                "id": main_id,
                "type": "main",
                "data": {
                    "label": section["short_label"],
                    "full_label": section["title"],
                    "description": section["description"],
                    "details": section["details"],
                    "color": palette[index % len(palette)],
                },
                "position": {"x": x_pos, "y": 210},
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

        for sub_index, detail in enumerate(section["sub_points"]):
            sub_id = f"sub_{index}_{sub_index}"
            nodes.append(
                {
                    "id": sub_id,
                    "type": "sub",
                    "data": {
                        "label": detail["label"],
                        "full_label": detail["full_label"],
                        "description": detail["description"],
                        "details": detail["details"],
                    },
                    "position": {
                        "x": x_pos + ((sub_index % 2) * 110) - 55,
                        "y": 390 + (sub_index * 115),
                    },
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


def build_basic_mindmap(title: str, key_points: list[str]) -> dict[str, Any]:
    points = key_points[:5] or [
        "Khái niệm cốt lõi và mục tiêu chính của chủ đề.",
        "Cơ chế hoặc nguyên lý hoạt động quan trọng nhất.",
        "Các thành phần cấu thành và quan hệ giữa chúng.",
        "Ví dụ minh họa, ứng dụng hoặc tình huống thực tế.",
        "Rủi ro, giới hạn và hướng tự học tiếp theo.",
    ]

    sections: list[dict[str, str]] = []
    for index, point in enumerate(points):
        short_label = f"Ý chính {index + 1}"
        sections.append(
            {
                "short_label": short_label,
                "title": point,
                "description": "Một trục nội dung quan trọng trong chủ đề.",
                "details": point,
                "sub_points": [
                    _make_sub_point_from_sentence(
                        point,
                        f"Ý {index + 1}",
                        "Tóm tắt trọng tâm của nhánh này.",
                    ),
                    _make_sub_point_from_sentence(
                        f"Ý này giúp người học liên hệ {title} với ví dụ thực tế hoặc ứng dụng gần gũi hơn.",
                        "Liên hệ thực tế",
                        "Liên hệ kiến thức với tình huống quen thuộc.",
                    ),
                ],
            }
        )

    return _create_mindmap_nodes_from_sections(title, sections)


def build_explore_fallback(prompt: str) -> dict[str, Any]:
    title = infer_topic_from_prompt(prompt)
    topic_tags = extract_topic_tags(title, limit=4)
    key_points = [
        f"Khái niệm: {title} cần được nhìn như một hệ thống kiến thức có mục tiêu, phạm vi áp dụng và giá trị riêng.",
        f"Cơ chế: muốn hiểu {title}, cần nắm logic vận hành hoặc quan hệ nhân quả phía sau thay vì học thuộc định nghĩa.",
        f"Thành phần: chủ đề này luôn gồm các yếu tố chính và mối liên hệ giữa chúng, không thể hiểu đúng nếu tách rời từng phần.",
        f"Ứng dụng: giá trị của {title} chỉ rõ khi đặt vào bối cảnh học tập, công việc hoặc quyết định thực tế.",
        f"Lưu ý: các nhầm lẫn phổ biến thường xuất hiện khi người học nhớ ví dụ nhưng chưa hiểu bản chất và giới hạn của chủ đề.",
    ]
    summary = "\n".join(
        [
            f"- {title} nên được học theo trục khái niệm, cơ chế, thành phần, ví dụ và ứng dụng thay vì đọc rời rạc từng mảnh thông tin.",
            f"- Trọng tâm của chủ đề nằm ở việc hiểu bản chất vận hành và mối liên hệ giữa các phần chính.",
            f"- Ví dụ và ứng dụng thực tế giúp người học chuyển kiến thức từ mức ghi nhớ sang mức sử dụng được.",
            f"- Những hiểu lầm phổ biến thường đến từ việc học thuộc kết quả mà bỏ qua nguyên lý tạo ra kết quả đó.",
        ]
    )

    return {
        "title": title,
        "summary": summary,
        "key_points": key_points,
        "topic_tags": topic_tags,
        "detailed_sections": {
            "core_concept": {
                "title": "Khái niệm cốt lõi",
                "content": _build_long_paragraph(
                    title,
                    "khái niệm nền tảng",
                    f"Cốt lõi của {title} nằm ở việc xác định bản chất thật sự của khái niệm, phạm vi áp dụng và giá trị mà nó tạo ra trong học tập hoặc công việc.",
                    "Người học nên trả lời được ba câu hỏi: nó là gì, dùng để làm gì, và vì sao nó quan trọng trong bức tranh lớn hơn.",
                ),
            },
            "mechanism": {
                "title": "Bản chất / cơ chế hoạt động",
                "content": _build_long_paragraph(
                    title,
                    "cơ chế vận hành",
                    f"Phần này cần chỉ ra trình tự hoặc nguyên lý bên trong: đầu vào là gì, quá trình xử lý diễn ra ra sao, và đầu ra có ý nghĩa gì.",
                    "Khi hiểu được cơ chế, người học sẽ không còn phụ thuộc vào việc học thuộc lòng mà có thể tự suy luận khi gặp ví dụ mới.",
                ),
            },
            "components_and_relationships": {
                "title": "Các thành phần chính và quan hệ giữa chúng",
                "content": _build_long_paragraph(
                    title,
                    "cấu trúc hệ thống",
                    f"Mỗi chủ đề đều có các phần tử cấu thành riêng, và điều quan trọng không chỉ là biết tên từng phần mà còn là hiểu chúng tác động qua lại như thế nào.",
                    "Nếu tách riêng từng phần mà không thấy mối liên hệ, người học sẽ dễ nhớ rời rạc và khó áp dụng vào tình huống tổng hợp.",
                ),
            },
            "persona_based_example": {
                "title": "Ví dụ trực quan theo đúng persona",
                "content": (
                    f"Để học sâu {title}, ví dụ nên bám sát bối cảnh thực tế của người học. "
                    f"Nếu người học thiên về ứng dụng, nên dùng một dự án nhỏ, quy trình công việc, hoặc trường hợp thường gặp để mô tả chủ đề. "
                    f"Nếu người học thiên về trực quan, nên diễn giải bằng phép so sánh, sơ đồ tư duy, hoặc một tình huống có trình tự rõ ràng để họ dễ hình dung."
                ),
            },
            "real_world_applications": {
                "title": "Ứng dụng thực tế",
                "content": (
                    f"{title} chỉ thực sự có giá trị khi người học thấy nó xuất hiện ở đâu trong thực tế, tại sao người ta cần nó, "
                    f"và điều gì xảy ra nếu thiếu kiến thức này. Phần ứng dụng nên chỉ ra ít nhất một bối cảnh học tập và một bối cảnh công việc "
                    f"để người học biết cách chuyển kiến thức từ lý thuyết sang hành động."
                ),
            },
            "common_misconceptions": {
                "title": "Nhầm lẫn phổ biến",
                "content": (
                    f"Khi mới tiếp cận {title}, người học thường nhầm giữa việc nhớ ví dụ với việc hiểu bản chất, hoặc nhầm giữa kết quả quan sát được và cơ chế tạo ra kết quả đó. "
                    f"Cách sửa là luôn quay lại câu hỏi: điều gì đang diễn ra bên trong, vì sao nó diễn ra như vậy, và điều kiện nào làm cho kết quả thay đổi."
                ),
            },
            "next_step_self_study": {
                "title": "Cách tự học tiếp trong 1 buổi ngắn",
                "content": (
                    f"Trong một buổi ngắn, người học nên chia việc học {title} thành ba bước: đọc lại khái niệm cốt lõi, "
                    f"tự giải thích cơ chế bằng lời của mình, rồi làm một ví dụ nhỏ hoặc tự vẽ lại mối quan hệ giữa các thành phần. "
                    f"Nếu còn thời gian, hãy ghi lại ba điều mình đã hiểu rõ hơn và một câu hỏi còn mơ hồ để đào sâu ở buổi sau."
                ),
            },
        },
        "teaching_adaptation": {
            "focus_priority": "Ưu tiên hiểu bản chất trước, rồi mới mở rộng sang ví dụ và ứng dụng.",
            "tone": "Giải thích rõ ràng, có tính sư phạm, tránh văn phong máy móc.",
            "depth_control": "Đi từ nền tảng đến cơ chế, rồi mới sang liên hệ thực tế và bước tự học tiếp.",
            "example_strategy": "Dùng ví dụ gần ngữ cảnh người học để biến kiến thức thành thứ có thể hình dung và áp dụng.",
        },
    }


def build_explore_mindmap(
    title: str,
    knowledge_detail_data: dict[str, Any],
) -> dict[str, Any]:
    detailed_sections = knowledge_detail_data.get("detailed_sections", {})

    section_specs = [
        ("core_concept", "Khái niệm cốt lõi", "Nền tảng để hiểu đúng chủ đề."),
        ("mechanism", "Cơ chế hoạt động", "Giải thích điều gì diễn ra bên trong."),
        ("components_and_relationships", "Thành phần và quan hệ", "Cho thấy cấu trúc và sự liên kết."),
        ("persona_based_example", "Ví dụ theo persona", "Giúp người học hình dung nhanh hơn."),
        ("real_world_applications", "Ứng dụng thực tế", "Biến kiến thức thành giá trị sử dụng."),
        ("common_misconceptions", "Nhầm lẫn phổ biến", "Chỉ ra các chỗ dễ hiểu sai."),
    ]

    sections: list[dict[str, Any]] = []
    for key, short_label, default_description in section_specs:
        section = detailed_sections.get(key) or {}
        content = normalize_text(str(section.get("content") or ""))
        title_text = normalize_text(str(section.get("title") or short_label))
        sentences = split_sentences(content, 3)
        if not sentences:
            sentences = [default_description]
        full_section_label = (
            f"{title_text}: {sentences[0]}" if sentences[0] not in title_text else title_text
        )

        sections.append(
            {
                "short_label": short_label,
                "title": full_section_label[:180],
                "description": sentences[0][:120],
                "details": content[:220] or default_description,
                "sub_points": [
                    _make_sub_point_from_sentence(
                        sentences[0],
                        "Ý chính",
                        default_description,
                    ),
                    _make_sub_point_from_sentence(
                        sentences[1] if len(sentences) > 1 else default_description,
                        "Mở rộng",
                        default_description,
                    ),
                ],
            }
        )

    return _create_mindmap_nodes_from_sections(title, sections)


def build_analyze_fallback(content: str) -> dict[str, Any]:
    summary_sentences = split_sentences(content, 4)
    summary = (
        "\n".join(f"- {sentence}" for sentence in summary_sentences)
        or normalize_text(content)[:260]
    )
    key_points = extract_key_points(content)
    return {
        "title": infer_title(content, "Phân tích nội dung"),
        "accuracy_score": None,
        "accuracy_assessment": "unverifiable",
        "summary": summary or "Chưa có đủ dữ liệu để tạo tóm tắt.",
        "key_points": key_points,
        "corrections": [],
        "topic_tags": extract_topic_tags(content),
    }


def build_quiz_fallback(
    title: str,
    summary: str,
    key_points: list[str],
    num_questions: int,
) -> list[dict[str, Any]]:
    points = key_points[:4] or extract_key_points(summary, 4)
    if not points:
        points = [f"Ý chính về {title}"]

    generic_distractors = [
        "Một chi tiết không liên quan trực tiếp đến nội dung chính.",
        "Một nhận định quá chung và thiếu căn cứ.",
        "Một ví dụ không phản ánh đúng trọng tâm của chủ đề.",
    ]

    questions: list[dict[str, Any]] = []
    option_ids = ["A", "B", "C", "D"]

    for index in range(min(num_questions, max(len(points), 3))):
        correct_text = points[index % len(points)]
        distractors = [point for point in points if point != correct_text][:3]
        while len(distractors) < 3:
            distractors.append(generic_distractors[len(distractors)])

        correct_position = index % 4
        option_texts = distractors[:]
        option_texts.insert(correct_position, correct_text)
        option_texts = option_texts[:4]
        options = [
            {"id": option_ids[option_index], "text": text}
            for option_index, text in enumerate(option_texts)
        ]

        questions.append(
            {
                "order_index": index,
                "question_type": "multiple_choice",
                "question_text": f"Ý nào phù hợp nhất với nội dung chính của phần {index + 1}?",
                "options": options,
                "correct_answer": option_ids[correct_position],
                "explanation": f"Đáp án đúng là ý bám sát nội dung: {correct_text}",
                "difficulty": "medium",
            }
        )

    questions.extend(
        [
            {
                "order_index": len(questions),
                "question_type": "open",
                "question_text": f"Theo bạn, {title} có thể được áp dụng như thế nào trong thực tế?",
                "thinking_hints": [
                    "Nêu bối cảnh cụ thể",
                    "Giải thích vì sao ví dụ đó phù hợp",
                ],
                "sample_answer_points": [
                    "Nêu được ví dụ thực tế",
                    "Liên hệ đúng với ý chính của chủ đề",
                ],
                "difficulty": "medium",
            },
            {
                "order_index": len(questions) + 1,
                "question_type": "open",
                "question_text": f"Nếu phải giải thích {title} cho người mới bắt đầu, bạn sẽ bắt đầu từ đâu?",
                "thinking_hints": [
                    "Chọn ý cơ bản nhất",
                    "Ưu tiên ví dụ dễ hiểu",
                ],
                "sample_answer_points": [
                    "Bắt đầu từ định nghĩa cốt lõi",
                    "Dùng ví dụ trực quan",
                ],
                "difficulty": "easy",
            },
        ]
    )

    return questions


def build_open_feedback_fallback(user_answer: str) -> dict[str, Any]:
    answer_length = len(normalize_text(user_answer))
    if answer_length >= 280:
        score = 8
    elif answer_length >= 140:
        score = 6
    elif answer_length >= 60:
        score = 4
    else:
        score = 2

    return {
        "critical_thinking_score": score,
        "ai_feedback": (
            "Hệ thống đang dùng chế độ đánh giá dự phòng. "
            "Bạn đã có câu trả lời bước đầu, nhưng nên bổ sung thêm lập luận, ví dụ "
            "và liên hệ trực tiếp với nội dung vừa học để câu trả lời chặt chẽ hơn."
        ),
        "strengths": ["Đã đưa ra quan điểm hoặc hướng trả lời ban đầu."],
        "improvements": [
            "Bổ sung ví dụ cụ thể",
            "Giải thích rõ vì sao lập luận của bạn hợp lý",
        ],
    }

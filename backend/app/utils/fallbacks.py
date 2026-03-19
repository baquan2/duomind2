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

TOPIC_FILLER_PHRASES = [
    "la gi",
    "hoat dong nhu the nao",
    "nhu the nao",
    "ra sao",
    "giai thich don gian",
    "giai thich",
    "cho nguoi moi bat dau",
    "co ban",
    "tong quan",
]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def clean_topic_text(text: str) -> str:
    cleaned = normalize_text(text)
    accentless = strip_accents(cleaned.lower())
    for phrase in TOPIC_FILLER_PHRASES:
        accentless = accentless.replace(phrase, " ")
    accentless = re.sub(r"\s*[:\-|]\s*", " ", accentless)
    accentless = re.sub(r"\s{2,}", " ", accentless).strip(" .,-")
    return accentless or strip_accents(cleaned)


def split_sentences(text: str, limit: int = 5) -> list[str]:
    chunks = [
        normalize_text(part)
        for part in re.split(r"(?<=[.!?])\s+|\n+", text)
        if normalize_text(part)
    ]
    return chunks[:limit]


def infer_title(text: str, fallback: str) -> str:
    first_sentence = split_sentences(text, 1)
    if not first_sentence:
        return fallback
    title = first_sentence[0][:60].strip(" .:-")
    return title or fallback


def extract_key_points(text: str, limit: int = 5) -> list[str]:
    sentences = split_sentences(text, limit + 2)
    if sentences:
        return sentences[:limit]

    normalized = normalize_text(text)
    if not normalized:
        return ["Chua co du du lieu de tao y chinh."]
    return [normalized[:160]]


def extract_topic_tags(text: str, limit: int = 5) -> list[str]:
    cleaned = clean_topic_text(text)
    phrases = [
        normalize_text(part)
        for part in re.split(r"\s*(?:,|/|-|\bva\b|\band\b)\s*", cleaned, flags=re.IGNORECASE)
        if normalize_text(part)
    ]

    filtered_phrases: list[str] = []
    for phrase in phrases:
        normalized_phrase = phrase.lower()
        if normalized_phrase in STOP_WORDS or len(normalized_phrase) < 3:
            continue
        if normalized_phrase not in [item.lower() for item in filtered_phrases]:
            filtered_phrases.append(phrase)
        if len(filtered_phrases) >= limit:
            return filtered_phrases

    words = re.findall(r"[a-z0-9_]{4,}", cleaned.lower())
    seen: list[str] = []
    for word in words:
        if word in STOP_WORDS or word.isdigit():
            continue
        if word not in seen:
            seen.append(word)
        if len(seen) >= limit:
            break
    return seen


def build_basic_mindmap(title: str, key_points: list[str]) -> dict[str, Any]:
    points = key_points[:5] or ["tong quan", "y chinh", "vi du", "ung dung"]
    nodes: list[dict[str, Any]] = [
        {
            "id": "root",
            "type": "root",
            "data": {
                "label": title[:36],
                "full_label": title,
                "description": "Chu de trung tam",
                "details": "Tam cua so do kien thuc.",
            },
            "position": {"x": 0, "y": 0},
        }
    ]
    edges: list[dict[str, Any]] = []

    palette = ["#0f766e", "#2563eb", "#7c3aed", "#ea580c", "#0891b2"]
    x_positions = [-320, -160, 0, 160, 320]

    for index, point in enumerate(points):
        main_id = f"main_{index}"
        nodes.append(
            {
                "id": main_id,
                "type": "main",
                "data": {
                    "label": point[:42],
                    "full_label": point,
                    "description": "Y chinh",
                    "details": point,
                    "color": palette[index % len(palette)],
                },
                "position": {"x": x_positions[index % len(x_positions)], "y": 180},
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

        sub_id = f"sub_{index}_0"
        nodes.append(
            {
                "id": sub_id,
                "type": "sub",
                "data": {
                    "label": "Chi tiet",
                    "full_label": point,
                    "description": "Mo rong nhanh nay",
                    "details": point,
                },
                "position": {
                    "x": x_positions[index % len(x_positions)] + 40,
                    "y": 320,
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


def build_basic_infographic(
    title: str,
    summary: str,
    key_points: list[str],
) -> dict[str, Any]:
    sections = [
        {
            "icon": str(index + 1),
            "heading": f"Diem {index + 1}",
            "content": point,
        }
        for index, point in enumerate(key_points[:5])
    ]
    if not sections:
        sections = [
            {
                "icon": "1",
                "heading": "Tong quan",
                "content": summary or "Chua co du du lieu de tao infographic chi tiet.",
            }
        ]

    return {
        "type": "list",
        "theme_color": "#0f766e",
        "title": title,
        "subtitle": summary[:160] if summary else "Tom tat nhanh ve chu de",
        "sections": sections,
        "footer_note": "Infographic du phong duoc tao khi AI chua tra du du lieu.",
    }


def build_analyze_fallback(content: str) -> dict[str, Any]:
    summary_sentences = split_sentences(content, 4)
    summary = (
        "\n".join(f"- {sentence}" for sentence in summary_sentences)
        or normalize_text(content)[:240]
    )
    key_points = extract_key_points(content)
    return {
        "title": infer_title(content, "Phan tich noi dung"),
        "accuracy_score": None,
        "accuracy_assessment": "unverifiable",
        "summary": summary or "Chua co du du lieu de tao tom tat.",
        "key_points": key_points,
        "corrections": [],
        "topic_tags": extract_topic_tags(content),
    }


def build_explore_fallback(prompt: str) -> dict[str, Any]:
    topic = clean_topic_text(prompt) or "chu de moi"
    title = infer_title(topic, "Kham pha chu de")
    key_points = [
        "Khai niem cot loi va muc tieu chinh.",
        "Cach van hanh o muc co ban.",
        "Thanh phan quan trong va moi lien he giua chung.",
        "Vi du, ung dung hoac tac dong thuc te.",
        "Rui ro, gioi han va huong tim hieu tiep theo.",
    ]
    summary = "\n".join(
        [
            f"- Khai niem cot loi cua chu de {topic}.",
            "- Co che hoac cach van hanh o muc co ban.",
            "- Thanh phan quan trong va moi lien he giua chung.",
            "- Vi du, ung dung hoac tac dong thuc te can nho.",
        ]
    )
    return {
        "title": title,
        "summary": summary,
        "key_points": key_points,
        "topic_tags": extract_topic_tags(topic, limit=3),
    }


def build_quiz_fallback(
    title: str,
    summary: str,
    key_points: list[str],
    num_questions: int,
) -> list[dict[str, Any]]:
    points = key_points[:4] or extract_key_points(summary, 4)
    if not points:
        points = [f"Y chinh ve {title}"]

    generic_distractors = [
        "Mot chi tiet khong lien quan truc tiep den noi dung chinh.",
        "Mot nhan dinh qua chung va thieu can cu.",
        "Mot vi du khong phan anh dung trong tam cua chu de.",
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
                "question_text": f"Y nao phu hop nhat voi noi dung chinh cua phan {index + 1}?",
                "options": options,
                "correct_answer": option_ids[correct_position],
                "explanation": f"Dap an dung la y bam sat noi dung: {correct_text}",
                "difficulty": "medium",
            }
        )

    questions.extend(
        [
            {
                "order_index": len(questions),
                "question_type": "open",
                "question_text": f"Theo ban, {title} co the duoc ap dung nhu the nao trong thuc te?",
                "thinking_hints": [
                    "Neu boi canh cu the",
                    "Giai thich vi sao vi du do phu hop",
                ],
                "sample_answer_points": [
                    "Neu duoc vi du thuc te",
                    "Lien he dung voi y chinh cua chu de",
                ],
                "difficulty": "medium",
            },
            {
                "order_index": len(questions) + 1,
                "question_type": "open",
                "question_text": f"Neu phai giai thich {title} cho nguoi moi bat dau, ban se bat dau tu dau?",
                "thinking_hints": [
                    "Chon y co ban nhat",
                    "Uu tien vi du de hieu",
                ],
                "sample_answer_points": [
                    "Bat dau tu dinh nghia cot loi",
                    "Dung vi du truc quan",
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
            "He thong dang dung che do danh gia du phong. "
            "Ban da co cau tra loi buoc dau, nhung nen bo sung them lap luan, vi du "
            "va lien he truc tiep voi noi dung vua hoc de cau tra loi chat che hon."
        ),
        "strengths": ["Da dua ra quan diem hoac huong tra loi ban dau."],
        "improvements": [
            "Bo sung vi du cu the",
            "Giai thich ro vi sao lap luan cua ban hop ly",
        ],
    }

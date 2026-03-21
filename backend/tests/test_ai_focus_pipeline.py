from app.routers.analyze import _build_analysis_fallback, _extract_analysis_focus, _extract_analysis_goal
from app.routers.explore import _build_fallback_payload, _key_points_need_fallback
from app.routers.quiz import _quiz_questions_need_fallback
from app.services.mentor_service import _build_decision_summary, _normalize_items, _normalize_list_of_strings
from app.utils.content_blueprint import (
    build_blueprint_fallback,
    build_section_content_from_blueprint,
    build_section_briefs,
    semantic_overlap_ratio,
)
from app.utils.fallbacks import build_targeted_quiz_fallback_v2
from app.utils.helpers import build_core_title, build_input_preview, build_prompt_learning_context
from app.utils.source_references import normalize_source_references


def test_extract_analysis_goal_prefers_explicit_goal() -> None:
    content = (
        "Câu hỏi cần phân tích: Business Analyst khác Product Analyst ở điểm nào?\n"
        "Nội dung của tôi: BA tập trung vào requirement, còn Product Analyst chỉ làm dashboard."
    )

    result = _extract_analysis_goal(content, "Business Analyst khác Product Analyst ở điểm nào?")

    assert result == "Business Analyst khác Product Analyst ở điểm nào?"


def test_build_prompt_learning_context_filters_unknown_values() -> None:
    prompt_context = build_prompt_learning_context(
        {
            "difficulty_level": "intermediate",
            "target_role": "Business Analyst",
            "current_focus": "unknown",
            "desired_outcome": "Đổi việc trong 3 tháng",
            "daily_study_minutes": 30,
            "content_depth": "gọn, ưu tiên hiểu bản chất trước",
        }
    )

    assert prompt_context["difficulty_level"] == "intermediate"
    assert prompt_context["target_role"] == "Business Analyst"
    assert prompt_context["desired_outcome"] == "Đổi việc trong 3 tháng"
    assert prompt_context["daily_study_minutes"] == 30
    assert "current_focus" not in prompt_context


def test_quiz_questions_need_fallback_rejects_generic_questions() -> None:
    quiz_material = {
        "title": "Business Analyst và Product Analyst",
        "summary": "Khác nhau ở mục tiêu, đầu ra và cách làm việc hằng ngày.",
        "key_points": [
            "Business Analyst tập trung vào requirement và quy trình.",
            "Product Analyst tập trung vào dữ liệu sản phẩm và insight.",
        ],
        "corrections": [],
        "detailed_sections": [
            {
                "title": "Khác biệt cốt lõi",
                "content": "BA làm rõ bài toán và requirement. Product Analyst đọc dữ liệu để rút insight.",
            }
        ],
    }
    generic_questions = [
        {
            "question_type": "multiple_choice",
            "question_text": "Ý nào phù hợp nhất với nội dung chính của phần 1?",
            "options": [
                {"id": "A", "text": "Một ý đúng"},
                {"id": "B", "text": "Một ý sai"},
                {"id": "C", "text": "Một ý khác"},
                {"id": "D", "text": "Một ý còn lại"},
            ],
            "correct_answer": "A",
            "explanation": "Đây là đáp án đúng.",
        },
        {
            "question_type": "open",
            "question_text": "Theo bạn, chủ đề trên quan trọng thế nào?",
            "thinking_hints": ["Nêu ý kiến", "Nêu cảm nhận"],
            "sample_answer_points": ["Có ích", "Quan trọng"],
        },
    ]

    assert _quiz_questions_need_fallback(generic_questions, quiz_material, 1, True) is True


def test_targeted_quiz_fallback_uses_corrections_and_sections() -> None:
    quiz_material = {
        "title": "Business Analyst và Product Analyst",
        "summary": "Khác nhau ở mục tiêu, đầu ra và cách làm việc hằng ngày.",
        "key_points": [
            "Business Analyst tập trung vào requirement và stakeholder.",
            "Product Analyst tập trung vào dữ liệu sản phẩm và insight.",
        ],
        "corrections": [
            {
                "original": "Product Analyst chỉ làm dashboard.",
                "correction": "Product Analyst dùng dữ liệu để tìm insight và đề xuất quyết định sản phẩm.",
                "explanation": "Dashboard chỉ là công cụ, không phải toàn bộ vai trò.",
            }
        ],
        "detailed_sections": [
            {
                "title": "Khác biệt cốt lõi",
                "content": "BA làm rõ requirement và quy trình. Product Analyst đọc dữ liệu để hiểu hành vi sản phẩm.",
            }
        ],
    }

    questions = build_targeted_quiz_fallback_v2(
        "Business Analyst và Product Analyst",
        quiz_material["summary"],
        quiz_material["key_points"],
        3,
        quiz_material=quiz_material,
    )

    mcq_texts = [question["question_text"] for question in questions if question["question_type"] == "multiple_choice"]
    open_texts = [question["question_text"] for question in questions if question["question_type"] == "open"]

    assert any("dinh chinh" in text.lower() for text in mcq_texts)
    assert any("Product Analyst chỉ làm dashboard" in text for text in open_texts)

def test_analysis_fallback_includes_knowledge_detail_data() -> None:
    result = _build_analysis_fallback(
        analysis_content=(
            "Business Analyst lam ro requirement va quy trinh. "
            "Product Analyst doc du lieu de rut insight cho san pham."
        ),
        focus_topic="Business Analyst va Product Analyst",
        analysis_goal="Business Analyst khac Product Analyst o diem nao?",
        learner_context={"target_role": "Business Analyst"},
    )

    knowledge_detail_data = result["knowledge_detail_data"]

    assert knowledge_detail_data["title"]
    assert knowledge_detail_data["summary"]
    assert knowledge_detail_data["detailed_sections"]["core_concept"]["content"]
    assert knowledge_detail_data["detailed_sections"]["persona_based_example"]["content"]


def test_explore_fallback_includes_theory_overview_and_detail_sections() -> None:
    result = _build_fallback_payload(
        "Business Analyst khac Product Analyst o diem nao?",
        {"target_role": "Business Analyst"},
    )

    assert result["title"]
    assert len(result["summary"].splitlines()) == 4
    assert len(result["key_points"]) == 5
    assert result["content_blueprint"]["core_definition"]
    assert result["section_briefs"]["overview"]
    assert result["active_section_keys"]
    assert result["detailed_sections"]["core_concept"]["content"]
    assert result["detailed_sections"]["mechanism"]["content"]
    assert result["detailed_sections"]["real_world_applications"]["content"]


def test_explore_key_points_need_fallback_for_generic_output() -> None:
    weak_points = [
        "Day la mot chu de quan trong can hieu ro.",
        "Nguoi hoc nen nam tong quan truoc.",
        "Phan nay giup ban co goc nhin tot hon.",
        "Can xem xet boi canh ap dung.",
        "Vi du se giup de hinh dung hon.",
    ]

    assert _key_points_need_fallback(
        "Business Analyst khac Product Analyst o diem nao?",
        "Business Analyst va Product Analyst",
        weak_points,
    )


def test_build_core_title_removes_trailing_filler() -> None:
    title = build_core_title(
        "Tri tue nhan tao va",
        "Chu de chinh",
    )

    assert title == "Tri tue nhan tao"


def test_build_core_title_extracts_subject_from_definition_sentence() -> None:
    title = build_core_title(
        "Khái niệm của thuyết quản trị là các tư tưởng, nguyên lý và cách tiếp cận nền tảng.",
        "Chủ đề chính",
    )

    assert title == "Thuyết quản trị"


def test_blueprint_section_briefs_keep_overview_and_takeaways_distinct() -> None:
    blueprint = build_blueprint_fallback(
        title="Business Analyst va Product Analyst",
        question_type="comparison",
        learner_context={"target_role": "Business Analyst"},
        comparison_targets=["Business Analyst", "Product Analyst"],
    )

    briefs = build_section_briefs(
        blueprint,
        title="Business Analyst va Product Analyst",
        question_type="comparison",
        mode="explore",
    )

    overview_text = " ".join(briefs["overview"])
    takeaway_text = " ".join(briefs["core_takeaways"])

    assert len(briefs["overview"]) >= 3
    assert len(briefs["core_takeaways"]) >= 4
    assert semantic_overlap_ratio(overview_text, takeaway_text) < 0.9


def test_blueprint_section_briefs_do_not_clip_items_with_ellipsis() -> None:
    blueprint = build_blueprint_fallback(
        title="SQL",
        question_type="concept",
        learner_context={"target_role": "Backend Developer"},
    )

    briefs = build_section_briefs(
        blueprint,
        title="SQL",
        question_type="concept",
        mode="explore",
    )

    for section_items in briefs.values():
        assert all("..." not in item for item in section_items)


def test_blueprint_section_content_keeps_complete_sentences() -> None:
    blueprint = build_blueprint_fallback(
        title="SQL",
        question_type="concept",
        learner_context={"target_role": "Backend Developer"},
    )

    content = build_section_content_from_blueprint(
        "mechanism",
        title="SQL",
        blueprint=blueprint,
    )

    assert "..." not in content


def test_build_input_preview_keeps_full_content_without_ellipsis() -> None:
    content = (
        "SQL (Structured Query Language) là ngôn ngữ dùng để làm việc với cơ sở dữ liệu quan hệ. "
        "Nó cho phép người dùng tạo bảng, thêm dữ liệu, chỉnh sửa dữ liệu, xóa dữ liệu và truy vấn thông tin."
    )

    preview = build_input_preview(content)

    assert preview == content
    assert "..." not in preview


def test_mentor_decision_summary_does_not_clip_user_facing_fields() -> None:
    result = {
        "skill_gaps": [
            {
                "skill": "SQL nền tảng",
                "suggested_action": "Trong 7 ngày tới, hãy dành 30 phút để xem 5-7 mô tả công việc Data Analyst và ghi lại 3 nhóm kỹ năng lặp lại nhiều nhất.",
                "why_it_matters": "Bạn đang chuẩn bị cho dự án cá nhân và cần chốt đúng trục kỹ năng để tránh học dàn trải.",
            }
        ],
        "recommended_learning_steps": [
            "Trong 7 ngày tới, hãy dành 30 phút để xem 5-7 mô tả công việc Data Analyst và ghi lại 3 nhóm kỹ năng lặp lại nhiều nhất."
        ],
        "decision_summary": {
            "headline": "Tập trung xác định kỹ năng cốt lõi cho Data Analyst để xây dựng dự án cá nhân đầu tiên một cách có định hướng rõ ràng.",
            "reason": "Người dùng đang chuẩn bị cho dự án cá nhân và gặp khó khăn trong việc học dễ bị lan man, khó nhớ. Việc chốt trục kỹ năng cốt lõi giúp tránh học dàn trải.",
            "next_action": "Trong 7 ngày tới, hãy dành 30 phút để xem 5-7 mô tả công việc Data Analyst và ghi lại 3 nhóm kỹ năng lặp lại nhiều nhất.",
            "confidence_note": "Đã bám đủ bối cảnh mục tiêu, đầu ra và ràng buộc học tập.",
        },
    }
    onboarding = {
        "target_role": "Data Analyst",
        "desired_outcome": "xây dự án cá nhân",
        "current_focus": "SQL và trực quan hóa dữ liệu",
        "current_challenges": "dễ học lan man",
        "learning_constraints": "30 phút mỗi ngày",
        "daily_study_minutes": 30,
    }

    summary = _build_decision_summary(result, onboarding)

    assert "..." not in summary["headline"]
    assert "..." not in summary["reason"]
    assert "..." not in summary["next_action"]
    assert summary["confidence_note"] == "Đã bám đủ bối cảnh mục tiêu, đầu ra và ràng buộc học tập."


def test_analysis_fallback_summary_keeps_complete_bullets() -> None:
    result = _build_analysis_fallback(
        analysis_content=(
            "Khái niệm của thuyết quản trị cơ bản là các tư tưởng, nguyên lý và cách tiếp cận nền tảng "
            "dùng để giải thích quản trị là gì, nhà quản trị làm gì và tổ chức được điều hành như thế nào."
        ),
        focus_topic="Khái niệm của thuyết quản trị là các tư tưởng, nguyên lý và cách tiếp cận nền tảng",
        analysis_goal="Khái niệm của thuyết quản trị là các tư tưởng, nguyên lý và cách tiếp cận nền tảng",
        learner_context={"target_role": "Business Analyst"},
    )

    assert "..." not in result["summary"]


def test_normalize_source_references_deduplicates_and_requires_urls() -> None:
    sources = normalize_source_references(
        [
            {"label": "Nguon 1", "url": "https://example.com/a", "snippet": "A"},
            {"label": "Nguon 1 duplicate", "url": "https://example.com/a", "snippet": "A2"},
            {"label": "Nguon 2", "url": "https://example.com/b", "snippet": "B"},
            {"label": "Thieu url", "snippet": "missing"},
        ]
    )

    assert len(sources) == 2
    assert sources[0]["url"] == "https://example.com/a"
    assert sources[1]["url"] == "https://example.com/b"


def test_extract_analysis_focus_prefers_subject_for_definition_text() -> None:
    focus = _extract_analysis_focus(
        (
            "Khai niem cua thuyet quan tri co ban la cac tu tuong, nguyen ly "
            "va cach tiep can nen tang dung de giai thich quan tri la gi."
        ),
        "Khai niem cua thuyet quan tri co ban la cac tu tuong, nguyen ly va cach tiep can nen tang",
    )

    assert focus == "Thuyet quan tri"


def test_mentor_normalizers_keep_full_items_without_ellipsis() -> None:
    items = _normalize_items(
        [
            {
                "role": "Data Analyst",
                "fit_reason": "Phu hop vi ban dang chuyen truc sang du an phan tich du lieu va can dau ra thuc hanh ro rang.",
                "entry_level": "Junior",
                "required_skills": [
                    "SQL nen tang de truy van va kiem tra du lieu",
                    "Thong ke co ban de doc dung tin hieu",
                ],
                "next_step": "Hoan thanh 1 mini project phan tich co dashboard va ghi ly do chon metric.",
            }
        ],
        {
            "role": "role",
            "fit_reason": "fit_reason",
            "entry_level": "entry_level",
            "required_skills": "required_skills",
            "next_step": "next_step",
        },
    )
    steps = _normalize_list_of_strings(
        [
            "Trong 7 ngay toi, hay xem 5 JD Data Analyst va ghi lai 3 nhom ky nang xuat hien lap lai nhieu nhat."
        ],
        3,
        clip=False,
    )

    assert "..." not in items[0]["fit_reason"]
    assert "..." not in items[0]["next_step"]
    assert all("..." not in skill for skill in items[0]["required_skills"])
    assert "..." not in steps[0]

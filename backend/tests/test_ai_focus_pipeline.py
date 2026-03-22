from app.routers.analyze import (
    _build_analysis_fallback,
    _detect_analysis_mode,
    _extract_analysis_focus,
    _extract_analysis_goal,
    _should_generate_analysis_blueprint,
)
from app.routers.explore import (
    _build_fallback_payload,
    _key_points_need_fallback,
    _normalize_explore_summary,
    _should_generate_explore_blueprint,
    _should_lookup_explore_sources,
)
from app.routers.quiz import _quiz_questions_need_fallback
from app.services.mentor_service import (
    _align_result_to_target_role,
    _build_decision_summary,
    _low_signal,
    _prune_result_for_intent,
    _sanitize_mentor_result,
    _normalize_items,
    _normalize_list_of_strings,
    build_personalized_fallback,
    build_suggested_questions,
    detect_mentor_intent,
    mentor_focus_topic,
)
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


def test_analyze_auto_routes_question_input_to_deep_dive() -> None:
    mode = _detect_analysis_mode(
        "Business Analyst khac Product Analyst o diem nao?",
        None,
        None,
        "auto",
    )

    assert mode == "deep_dive"


def test_analyze_auto_routes_note_dump_to_critique() -> None:
    mode = _detect_analysis_mode(
        (
            "Business Analyst la nguoi lam ro requirement va quy trinh. "
            "Product Analyst chi lam dashboard. "
            "BA khong can quan tam den stakeholder."
        ),
        "Kiem tra noi dung nay dung hay sai?",
        None,
        "auto",
    )

    assert mode == "critique"


def test_deep_dive_short_question_still_generates_analysis_blueprint() -> None:
    assert (
        _should_generate_analysis_blueprint(
            {"analysis_kind": "definition"},
            "SQL la gi?",
            "deep_dive",
        )
        is True
    )


def test_mentor_low_signal_flags_skill_gap_answer_without_skill_gaps() -> None:
    assert (
        _low_signal(
            "Voi muc tieu Data Analyst, day la mot khai niem can duoc hieu theo pham vi ap dung va co che van hanh cu the.",
            "Voi muc tieu Data Analyst, toi dang thieu nhung ky nang nao quan trong nhat?",
            {"target_role": "Data Analyst"},
            {
                "skill_gaps": [],
                "recommended_learning_steps": [],
                "decision_summary": {
                    "headline": "Day la y chinh can giu.",
                    "priority_value": "chu de hien tai",
                },
            },
        )
        is True
    )


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


def test_short_explore_question_still_requests_sources() -> None:
    assert _should_lookup_explore_sources({"question_type": "definition"}, "SQL la gi?") is True


def test_short_explore_question_still_generates_blueprint() -> None:
    assert (
        _should_generate_explore_blueprint(
            {"question_type": "comparison"},
            "Business Analyst khac Product Analyst o diem nao?",
        )
        is True
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


def test_blueprint_section_briefs_anchor_to_main_question() -> None:
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
        main_question="Business Analyst khac Product Analyst o diem nao?",
        focus_topic="Business Analyst va Product Analyst",
        comparison_targets=["Business Analyst", "Product Analyst"],
    )

    assert "Business Analyst" in briefs["overview"][0]
    assert "Product Analyst" in briefs["overview"][0]
    assert len(briefs["core_takeaways"]) >= 4


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


def test_align_result_to_target_role_does_not_override_existing_answer() -> None:
    result = {
        "answer": "Thi truong hien tai uu tien kha nang lam ro requirement va process mapping truoc.",
        "career_paths": [],
        "skill_gaps": [],
        "recommended_learning_steps": [],
        "suggested_followups": [],
    }

    aligned = _align_result_to_target_role(
        result,
        {"target_role": "Business Analyst"},
        intent="career_fit",
    )

    assert aligned["answer"] == "Thi truong hien tai uu tien kha nang lam ro requirement va process mapping truoc."
    assert aligned["career_paths"]
    assert aligned["skill_gaps"]


def test_align_result_to_target_role_skips_general_guidance_alignment() -> None:
    result = {
        "answer": "SQL la ngon ngu truy van duoc dung de thao tac va truy van du lieu trong co so du lieu quan he.",
        "career_paths": [],
        "skill_gaps": [],
        "recommended_learning_steps": [],
        "suggested_followups": [],
    }

    aligned = _align_result_to_target_role(
        result,
        {"target_role": "Business Analyst"},
        intent="general_guidance",
    )

    assert aligned["career_paths"] == []
    assert aligned["skill_gaps"] == []


def test_mentor_market_outlook_fallback_stays_on_market_signal() -> None:
    result = build_personalized_fallback(
        profile=None,
        onboarding={
            "target_role": "Data Analyst",
            "desired_outcome": "xin intern",
            "daily_study_minutes": 30,
        },
        intent="market_outlook",
        message="Thi truong hien tai dang can gi cho Data Analyst?",
        market_signals=[],
        web_research=[
            {
                "title": "Data Analyst demand",
                "snippet": "Nha tuyen dung nhac SQL, dashboard va business insight.",
                "source_name": "Example source",
                "url": "https://example.com/data-analyst",
            }
        ],
    )

    lowered_answer = result["answer"].lower()
    assert "jd" in lowered_answer or "thi truong" in lowered_answer
    assert len(result["recommended_learning_steps"]) == 2


def test_detect_mentor_intent_scores_roadmap_above_generic_market_terms() -> None:
    intent = detect_mentor_intent(
        "Thi truong dang yeu cau nhung ky nang nao va toi nen hoc gi truoc theo lo trinh?"
    )

    assert intent == "learning_roadmap"


def test_learning_roadmap_fallback_keeps_ordered_steps_in_answer() -> None:
    result = build_personalized_fallback(
        profile=None,
        onboarding={
            "target_role": "Data Analyst",
            "desired_outcome": "co roadmap hoc 8 tuan",
            "daily_study_minutes": 45,
        },
        intent="learning_roadmap",
        message="Len cho toi lo trinh hoc Data Analyst tu dau.",
        market_signals=[],
        web_research=[],
    )

    lowered_answer = result["answer"].lower()
    assert "buoc 1" in lowered_answer
    assert "buoc 2" in lowered_answer
    assert len(result["recommended_learning_steps"]) == 3


def test_intent_aware_decision_summary_uses_roadmap_headline() -> None:
    summary = _build_decision_summary(
        {
            "skill_gaps": [
                {
                    "skill": "SQL",
                    "suggested_action": "Buoc 1 la hoc SQL nen tang va lam bai tap query co ban.",
                }
            ],
            "recommended_learning_steps": [
                "Buoc 1 la hoc SQL nen tang va lam bai tap query co ban.",
                "Buoc 2 la lam sach du lieu va doc metric co ban.",
                "Buoc 3 la dung dashboard va viet insight tu du lieu.",
            ],
            "career_paths": [{"role": "Data Analyst"}],
            "market_signals": [],
        },
        {
            "target_role": "Data Analyst",
            "desired_outcome": "co roadmap hoc 8 tuan",
            "daily_study_minutes": 45,
        },
        intent="learning_roadmap",
    )

    lowered_headline = summary["headline"].lower()
    assert "roadmap" in lowered_headline or "buoc" in lowered_headline
    assert "SQL" not in summary["priority_label"]


def test_business_analyst_fallback_is_not_forced_into_data_track() -> None:
    result = build_personalized_fallback(
        profile=None,
        onboarding={
            "target_role": "Business Analyst",
            "desired_outcome": "xin intern BA",
            "daily_study_minutes": 30,
        },
        intent="career_fit",
        message="Toi hop voi huong Business Analyst khong?",
        market_signals=[],
        web_research=[],
    )

    assert result["career_paths"]
    assert result["career_paths"][0]["role"] == "Business Analyst"


def test_general_guidance_specific_answer_is_not_flagged_low_signal() -> None:
    result = {
        "decision_summary": {
            "headline": "SQL la ngon ngu truy van du lieu.",
            "priority_label": "Khai niem cot loi",
            "priority_value": "SQL",
            "reason": "No duoc dung de truy van va thao tac du lieu co cau truc.",
            "next_action": "Doc them 3 nhom lenh chinh cua SQL.",
            "confidence_note": "Khong can them boi canh ca nhan de tra loi cau hoi nay.",
        },
        "recommended_learning_steps": [],
        "skill_gaps": [],
        "career_paths": [],
        "market_signals": [],
    }

    assert (
        _low_signal(
            "SQL la ngon ngu truy van co cau truc duoc dung de tao, sua, xoa va truy van du lieu trong he quan tri co so du lieu quan he.",
            "SQL la gi?",
            {"target_role": "Business Analyst"},
            result,
        )
        is False
    )


def test_explore_summary_prefers_direct_answer_over_generic_brief_fallback() -> None:
    summary = _normalize_explore_summary(
        "- SQL la ngon ngu truy van co cau truc duoc dung de lam viec voi co so du lieu quan he.\n"
        "- SQL tap trung vao dinh nghia cau truc, thao tac du lieu va truy van.\n"
        "- Gia tri cua SQL nam o kha nang lay va bien doi du lieu bang lenh co cau truc.\n"
        "- Khong nen dong nhat SQL voi toan bo he quan tri co so du lieu.",
        [
            "SQL duoc dung de tao bang, thao tac du lieu va truy van thong tin.",
            "Can phan biet SQL voi he quan tri co so du lieu.",
            "Co the nhin SQL theo nhom lenh va muc dich su dung.",
            "SQL co gia tri khi can xu ly du lieu co cau truc.",
        ],
        "- Day la mot chu de quan trong.\n- Nguoi hoc nen nam tong quan truoc.",
        prompt="SQL la gi?",
        focus_topic="SQL",
        detailed_sections={
            "core_concept": {
                "content": "SQL la ngon ngu truy van co cau truc duoc dung de lam viec voi co so du lieu quan he."
            }
        },
    )

    assert "SQL la ngon ngu truy van" in summary
    assert "Day la mot chu de quan trong" not in summary


def test_prune_result_for_market_outlook_hides_irrelevant_sections() -> None:
    pruned = _prune_result_for_intent(
        {
            "career_paths": [{"role": "Data Analyst"}],
            "market_signals": [{"role_name": "Data Analyst"}],
            "skill_gaps": [{"skill": "SQL"}],
            "recommended_learning_steps": ["Buoc 1", "Buoc 2", "Buoc 3"],
            "suggested_followups": [],
            "sources": [],
        },
        "market_outlook",
    )

    assert pruned["career_paths"] == []
    assert pruned["skill_gaps"] == []
    assert len(pruned["recommended_learning_steps"]) == 2
    items = _normalize_items(
        [
            {
                "role": "Data Analyst",
                "fit_reason": "Phu hop vi ban dang chuyen truc sang du an phan tich du lieu va can dau ra thuc hanh ro rang.",
                "entry_level": "Intern / Junior",
                "required_skills": ["SQL", "Excel", "Power BI", "Dashboarding"],
                "next_step": "Lam mot dashboard tu du lieu that va viet 3 insight kinh doanh.",
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


def test_direct_knowledge_question_maps_to_general_guidance() -> None:
    assert detect_mentor_intent("Business Analyst khac Product Analyst o diem nao?") == "general_guidance"


def test_personalized_skill_gap_question_maps_to_skill_gap() -> None:
    intent = detect_mentor_intent(
        "Voi muc tieu Data Analyst, toi dang thieu nhung ky nang nao quan trong nhat?"
    )

    assert intent == "skill_gap"


def test_personalized_skill_gap_focus_topic_extracts_target_role() -> None:
    focus_topic = mentor_focus_topic(
        "Voi muc tieu Data Analyst, toi dang thieu nhung ky nang nao quan trong nhat?"
    )

    assert focus_topic == "Data Analyst"


def test_general_mentor_question_does_not_force_profile_context() -> None:
    result = build_personalized_fallback(
        profile={"full_name": "Test User"},
        onboarding={
            "target_role": "Data Analyst",
            "current_focus": "SQL",
        },
        intent="general_guidance",
        message="TCP 3-way handshake hoạt động thế nào?",
        market_signals=[],
        web_research=[],
    )

    current_question = result["request_payload"]["current_question"]
    assert current_question["use_profile_context"] is True
    assert result["context_snapshot"]["context_policy"] == "personalized_by_default_but_question_first"
    assert result["generation_trace"]["context_usage"]["ignored_fields"]


def test_mentor_suggested_questions_are_open_domain_first() -> None:
    suggestions = build_suggested_questions(
        {"full_name": "Test User"},
        {"target_role": "Data Analyst"},
    )

    joined = " ".join(suggestions)
    assert "TCP 3-way handshake" in joined or "Business Analyst" in joined
    assert "Data Analyst" not in suggestions[0]


def test_general_guidance_fallback_keeps_knowledge_answer_shape() -> None:
    result = build_personalized_fallback(
        profile=None,
        onboarding={
            "target_role": "Business Analyst",
            "current_focus": "Requirement analysis",
        },
        intent="general_guidance",
        message="Business Analyst khac Product Analyst o diem nao?",
        market_signals=[],
        web_research=[],
    )

    assert result["career_paths"] == []
    assert result["skill_gaps"] == []
    assert "Business Analyst" in result["answer"]
    assert "Product Analyst" in result["answer"]


def test_general_guidance_answer_matching_question_is_not_low_signal() -> None:
    answer = (
        "Business Analyst va Product Analyst khac nhau o bai toan chinh, dau ra va bang chung su dung. "
        "Business Analyst lam ro requirement, quy trinh va pham vi nghiep vu; Product Analyst doc metric, hanh vi san pham "
        "va du lieu de rut insight. Vi vay khong nen dong nhat hai vai tro chi vi cung lien quan den san pham."
    )

    assert (
        _low_signal(
            answer,
            "Business Analyst khac Product Analyst o diem nao?",
            {"target_role": "Business Analyst"},
            {
                "decision_summary": {
                    "headline": "Business Analyst va Product Analyst khac nhau o bai toan chinh."
                }
            },
        )
        is False
    )


def test_mentor_low_signal_flags_off_target_career_paths() -> None:
    assert (
        _low_signal(
            "Data Analyst la huong phu hop nhat cho ban luc nay.",
            "Toi hop voi huong Business Analyst khong?",
            {"target_role": "Business Analyst"},
            {
                "career_paths": [{"role": "Data Analyst"}],
                "decision_summary": {
                    "headline": "Nen uu tien Data Analyst truoc.",
                },
            },
        )
        is True
    )


def test_sanitize_mentor_result_only_keeps_model_selected_sources() -> None:
    result = _sanitize_mentor_result(
        {
            "answer": "SQL la ngon ngu truy van du lieu co cau truc.",
            "sources": [],
        },
        intent="general_guidance",
        message="SQL la gi?",
        onboarding=None,
        allowed_sources=[
            {
                "label": "Example source",
                "url": "https://example.com/sql",
                "snippet": "SQL definition",
            }
        ],
    )

    assert result["sources"] == []


def test_mentor_low_signal_flags_off_topic_knowledge_answer() -> None:
    assert (
        _low_signal(
            "Đây là một chủ đề quan trọng trong nhiều bối cảnh và thường cần nhìn ở góc rộng hơn.",
            "SQL la gi?",
            {"target_role": "Business Analyst"},
            {
                "decision_summary": {
                    "headline": "Can nhin chu de theo nhieu goc do.",
                }
            },
        )
        is True
    )

# 04 — AI Prompts Engine (Gemini Templates)

## Mục tiêu
Tạo file `app/utils/prompts.py` chứa tất cả prompt templates cho Gemini.
Prompts được thiết kế để output JSON có cấu trúc chính xác.

---

## `app/utils/prompts.py`

```python
# ============================================================
# DUO MIND — Gemini Prompt Templates
# ============================================================

# ─────────────────────────────────────────────────────────────
# 1. ONBOARDING: Phân loại người dùng
# ─────────────────────────────────────────────────────────────
ONBOARDING_CLASSIFY_PROMPT = """
Bạn là chuyên gia giáo dục. Dựa vào thông tin người dùng sau, hãy phân loại họ và đề xuất lộ trình học.

THÔNG TIN NGƯỜI DÙNG:
- Độ tuổi: {age_range}
- Trạng thái: {status} (student/working/both/other)
- Trình độ học vấn: {education_level}
- Chuyên ngành: {major}
- Ngành nghề: {industry}
- Chức vụ: {job_title}
- Kinh nghiệm (năm): {years_experience}
- Mục tiêu học: {learning_goals}
- Chủ đề quan tâm: {topics_of_interest}
- Phong cách học: {learning_style}

Trả về JSON với format chính xác:
{{
  "persona": "tên_persona_ngắn_gọn",
  "description": "Mô tả 2-3 câu về đặc điểm và nhu cầu học của người này",
  "recommended_topics": ["topic1", "topic2", "topic3", "topic4", "topic5"],
  "learning_tips": ["mẹo1", "mẹo2", "mẹo3"],
  "difficulty_level": "beginner|intermediate|advanced"
}}

Ví dụ persona: "university_tech_student", "high_school_stem", "professional_marketing", "career_changer_tech"
"""

# ─────────────────────────────────────────────────────────────
# 2. ANALYZE MODE: Phân tích nội dung người dùng nhập
# ─────────────────────────────────────────────────────────────
ANALYZE_CONTENT_PROMPT = """
Bạn là chuyên gia kiểm tra thông tin và giáo dục. Phân tích nội dung sau đây.

THÔNG TIN NGƯỜI DÙNG:
- Persona: {user_persona}
- Trình độ: {difficulty_level}

NỘI DUNG CẦN PHÂN TÍCH:
\"\"\"
{content}
\"\"\"

Hãy:
1. Đánh giá độ chính xác của từng thông tin
2. Tóm tắt nội dung súc tích
3. Chỉ ra các điểm sai/cần chỉnh sửa (nếu có)
4. Trích xuất các ý chính

Trả về JSON:
{{
  "title": "Tiêu đề ngắn mô tả chủ đề (tối đa 60 ký tự)",
  "accuracy_score": 75,
  "accuracy_assessment": "high|medium|low|unverifiable",
  "accuracy_reasoning": "Giải thích ngắn tại sao cho điểm này",
  "summary": "Tóm tắt nội dung trong 3-5 câu, phù hợp với trình độ người học",
  "key_points": [
    "Điểm chính 1",
    "Điểm chính 2",
    "Điểm chính 3",
    "Điểm chính 4",
    "Điểm chính 5"
  ],
  "corrections": [
    {{
      "original": "Thông tin sai/chưa chính xác trong nội dung",
      "correction": "Thông tin đúng",
      "explanation": "Giải thích tại sao"
    }}
  ],
  "topic_tags": ["tag1", "tag2", "tag3"],
  "enrichment": "Thông tin bổ sung thú vị liên quan (2-3 câu)"
}}

Lưu ý:
- accuracy_score: 0-100 (0=hoàn toàn sai, 100=hoàn toàn đúng)
- Nếu không thể kiểm chứng (quan điểm cá nhân), dùng "unverifiable" và score = null
- corrections = [] nếu nội dung chính xác
- Trả lời bằng ngôn ngữ: {language}
"""

# ─────────────────────────────────────────────────────────────
# 3. EXPLORE MODE: Tìm hiểu chủ đề từ prompt tự nhiên
# ─────────────────────────────────────────────────────────────
EXPLORE_TOPIC_PROMPT = """
Bạn là trợ lý giáo dục thông minh. Người dùng muốn tìm hiểu về chủ đề sau.

THÔNG TIN NGƯỜI DÙNG:
- Persona: {user_persona}
- Trình độ: {difficulty_level}
- Mục tiêu học: {learning_goals}

CHỦ ĐỀ MUỐN TÌM HIỂU:
\"\"\"
{prompt}
\"\"\"

Hãy cung cấp thông tin toàn diện, chính xác, phù hợp với trình độ người học.

Trả về JSON:
{{
  "title": "Tiêu đề chủ đề (tối đa 60 ký tự)",
  "summary": "Tổng quan chủ đề trong 4-6 câu",
  "key_points": [
    "Điểm quan trọng 1",
    "Điểm quan trọng 2",
    "Điểm quan trọng 3",
    "Điểm quan trọng 4",
    "Điểm quan trọng 5"
  ],
  "detailed_sections": [
    {{
      "heading": "Tên mục",
      "content": "Nội dung chi tiết mục này (3-5 câu)",
      "examples": ["Ví dụ 1", "Ví dụ 2"]
    }}
  ],
  "fun_facts": ["Sự thật thú vị 1", "Sự thật thú vị 2"],
  "common_misconceptions": ["Hiểu nhầm phổ biến 1", "Hiểu nhầm phổ biến 2"],
  "topic_tags": ["tag1", "tag2", "tag3"],
  "related_topics": ["Chủ đề liên quan 1", "Chủ đề liên quan 2", "Chủ đề liên quan 3"]
}}

Trả lời bằng ngôn ngữ: {language}
"""

# ─────────────────────────────────────────────────────────────
# 4. MIND MAP: Tạo cấu trúc mind map từ nội dung
# ─────────────────────────────────────────────────────────────
MINDMAP_GENERATE_PROMPT = """
Tạo cấu trúc mind map cho nội dung sau để hiển thị bằng ReactFlow.

NỘI DUNG:
\"\"\"
{content}
\"\"\"

CHỦ ĐỀ CHÍNH: {title}

Tạo mind map với cấu trúc phân cấp rõ ràng: 1 node trung tâm → 3-5 node chính → 2-4 node con mỗi node chính.

Trả về JSON:
{{
  "nodes": [
    {{
      "id": "root",
      "type": "root",
      "data": {{
        "label": "Chủ đề chính",
        "description": "Mô tả ngắn"
      }},
      "position": {{"x": 400, "y": 300}}
    }},
    {{
      "id": "main_1",
      "type": "main",
      "data": {{
        "label": "Nhánh chính 1",
        "description": "Mô tả",
        "color": "#6366f1"
      }},
      "position": {{"x": 100, "y": 150}}
    }},
    {{
      "id": "sub_1_1",
      "type": "sub",
      "data": {{
        "label": "Nhánh con 1.1",
        "description": "Chi tiết"
      }},
      "position": {{"x": -100, "y": 80}}
    }}
  ],
  "edges": [
    {{
      "id": "e_root_main1",
      "source": "root",
      "target": "main_1",
      "type": "smoothstep"
    }},
    {{
      "id": "e_main1_sub1",
      "source": "main_1",
      "target": "sub_1_1",
      "type": "smoothstep"
    }}
  ]
}}

Màu sắc cho các main nodes: dùng xen kẽ ["#6366f1","#8b5cf6","#06b6d4","#10b981","#f59e0b"]
Vị trí: root ở giữa (400,300), main nodes trải quanh, sub nodes xa hơn.
"""

# ─────────────────────────────────────────────────────────────
# 5. INFOGRAPHIC: Tạo dữ liệu infographic từ nội dung
# ─────────────────────────────────────────────────────────────
INFOGRAPHIC_GENERATE_PROMPT = """
Tạo dữ liệu để render infographic trực quan cho nội dung sau.

NỘI DUNG/CHỦ ĐỀ: {title}
TÓM TẮT: {summary}
CÁC ĐIỂM CHÍNH: {key_points}

Trả về JSON để render infographic:
{{
  "type": "steps|comparison|statistics|timeline|list",
  "theme_color": "#6366f1",
  "title": "Tiêu đề infographic",
  "subtitle": "Mô tả phụ",
  "sections": [
    {{
      "icon": "emoji hoặc ký tự đơn giản",
      "heading": "Tiêu đề section",
      "content": "Nội dung ngắn gọn",
      "highlight": "Số liệu hoặc từ khóa nổi bật (tùy chọn)"
    }}
  ],
  "footer_note": "Ghi chú cuối (tùy chọn)"
}}

Chọn type phù hợp:
- "steps": quy trình có bước
- "comparison": so sánh 2 thứ
- "statistics": dữ liệu số liệu
- "timeline": theo thời gian
- "list": danh sách thông tin
"""

# ─────────────────────────────────────────────────────────────
# 6. QUIZ: Tạo câu hỏi trắc nghiệm
# ─────────────────────────────────────────────────────────────
QUIZ_GENERATE_PROMPT = """
Tạo bộ câu hỏi kiểm tra kiến thức dựa vào nội dung sau.

THÔNG TIN NGƯỜI DÙNG:
- Trình độ: {difficulty_level}
- Persona: {user_persona}

NỘI DUNG:
\"\"\"
{content}
\"\"\"

TÓM TẮT: {summary}

Tạo đúng {num_questions} câu hỏi trắc nghiệm 4 đáp án (A,B,C,D).
Phân bổ: 40% easy, 40% medium, 20% hard.

Trả về JSON:
{{
  "questions": [
    {{
      "order_index": 0,
      "question_type": "multiple_choice",
      "question_text": "Câu hỏi?",
      "options": [
        {{"id": "A", "text": "Đáp án A"}},
        {{"id": "B", "text": "Đáp án B"}},
        {{"id": "C", "text": "Đáp án C"}},
        {{"id": "D", "text": "Đáp án D"}}
      ],
      "correct_answer": "A",
      "explanation": "Giải thích tại sao A đúng",
      "difficulty": "easy|medium|hard"
    }}
  ]
}}

Trả lời bằng ngôn ngữ: {language}
"""

# ─────────────────────────────────────────────────────────────
# 7. OPEN QUESTIONS: Câu hỏi tư duy phản biện
# ─────────────────────────────────────────────────────────────
OPEN_QUESTIONS_PROMPT = """
Tạo câu hỏi tự luận để kích thích tư duy phản biện về chủ đề sau.

THÔNG TIN NGƯỜI DÙNG:
- Persona: {user_persona}
- Trình độ: {difficulty_level}

CHỦ ĐỀ: {title}
NỘI DUNG TÓM TẮT: {summary}

Tạo 3 câu hỏi tự luận kích thích tư duy:
1. Câu phân tích (analyze)
2. Câu đánh giá (evaluate)
3. Câu sáng tạo/ứng dụng (create/apply)

Trả về JSON:
{{
  "questions": [
    {{
      "order_index": 0,
      "question_type": "open",
      "question_text": "Câu hỏi kích thích tư duy?",
      "thinking_hints": ["Gợi ý suy nghĩ 1", "Gợi ý suy nghĩ 2"],
      "sample_answer_points": ["Điểm cần đề cập 1", "Điểm cần đề cập 2"],
      "difficulty": "medium|hard"
    }}
  ]
}}

Trả lời bằng ngôn ngữ: {language}
"""

# ─────────────────────────────────────────────────────────────
# 8. OPEN ANSWER FEEDBACK: AI đánh giá câu trả lời tự luận
# ─────────────────────────────────────────────────────────────
OPEN_ANSWER_FEEDBACK_PROMPT = """
Đánh giá câu trả lời tự luận của người học.

CÂU HỎI: {question}
GỢI Ý ĐÁNH GIÁ: {sample_points}
CÂU TRẢ LỜI CỦA NGƯỜI HỌC:
\"\"\"
{user_answer}
\"\"\"

Trả về JSON:
{{
  "critical_thinking_score": 7,
  "ai_feedback": "Nhận xét chi tiết về câu trả lời (3-5 câu): điểm mạnh, điểm cần cải thiện",
  "strengths": ["Điểm mạnh 1", "Điểm mạnh 2"],
  "improvements": ["Cần cải thiện 1", "Cần cải thiện 2"],
  "missed_points": ["Điểm quan trọng chưa đề cập"]
}}

critical_thinking_score: 0-10
- 0-3: Chưa thể hiện tư duy phản biện
- 4-6: Tư duy cơ bản
- 7-8: Tư duy tốt
- 9-10: Xuất sắc

Trả lời bằng ngôn ngữ: {language}
"""

# ─────────────────────────────────────────────────────────────
# 9. KNOWLEDGE ANALYTICS: Tổng hợp kiến thức người học
# ─────────────────────────────────────────────────────────────
KNOWLEDGE_ANALYTICS_PROMPT = """
Phân tích tổng hợp lịch sử học tập của người dùng.

THÔNG TIN NGƯỜI DÙNG:
- Persona: {user_persona}
- Ngày bắt đầu dùng app: {member_since}

LỊCH SỬ HỌC (JSON):
{sessions_summary}

THỐNG KÊ QUIZ:
- Tổng số lần quiz: {total_quizzes}
- Điểm trung bình: {avg_quiz_score}%

Phân tích và đưa ra insights.

Trả về JSON:
{{
  "ai_summary": "Tóm tắt tổng thể hành trình học của người dùng (3-5 câu)",
  "strongest_topics": ["Chủ đề giỏi nhất 1", "Chủ đề giỏi nhất 2"],
  "weakest_topics": ["Chủ đề cần cải thiện 1", "Chủ đề cần cải thiện 2"],
  "learning_pattern": "consistent|sporadic|intensive|new",
  "knowledge_depth": "surface|intermediate|deep",
  "ai_recommendations": [
    "Gợi ý học tiếp theo 1",
    "Gợi ý học tiếp theo 2",
    "Gợi ý học tiếp theo 3"
  ],
  "achievement_highlights": ["Thành tích nổi bật 1", "Thành tích nổi bật 2"],
  "next_milestone": "Cột mốc tiếp theo nên đạt được"
}}
"""
```

---

## `app/utils/helpers.py`

```python
import json
import re
from typing import Any

def safe_parse_json(text: str) -> dict:
    """Parse JSON an toàn, xử lý markdown code blocks."""
    # Xóa markdown backticks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse AI response as JSON: {e}\nResponse: {text[:200]}")

def truncate_content(content: str, max_chars: int = 8000) -> str:
    """Giới hạn độ dài nội dung để không vượt quá context window."""
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "\n...[Nội dung đã được rút gọn]"

def get_user_context(onboarding_data: dict | None) -> dict:
    """Lấy context người dùng để inject vào prompts."""
    if not onboarding_data:
        return {
            "user_persona": "general_learner",
            "difficulty_level": "intermediate",
            "learning_goals": "general_knowledge"
        }
    return {
        "user_persona": onboarding_data.get("ai_persona", "general_learner"),
        "difficulty_level": onboarding_data.get("ai_recommended_topics", "intermediate"),
        "learning_goals": ", ".join(onboarding_data.get("learning_goals", []))
    }
```

---

## ✅ Checklist Bước 04

- [ ] File `app/utils/prompts.py` tạo với đủ 9 prompt templates
- [ ] File `app/utils/helpers.py` tạo với 3 helper functions
- [ ] Test từng prompt bằng cách print để kiểm tra format string
- [ ] Verify JSON output format trong Gemini Playground

---

## ➡️ Bước Tiếp theo
Đọc `05-api-endpoints.md` để implement tất cả API endpoints.

---

## 🤖 Codex Prompt

```
Tạo file backend/app/utils/prompts.py với đủ 9 prompt templates theo code trong file 04-ai-prompts-engine.md.
Tạo file backend/app/utils/helpers.py với các helper functions.
Không thay đổi nội dung prompt, chỉ copy chính xác.
```

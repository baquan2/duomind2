# ============================================================
# DUO MIND - Gemini Prompt Templates
# ============================================================

ONBOARDING_CLASSIFY_PROMPT = """
Bạn là Learning Architect của DUO MIND.
Nhiệm vụ của bạn là phân tích hồ sơ người học và tạo learning persona thực dụng, rõ ràng, dễ áp dụng ngay cho việc cá nhân hóa cách dạy.

MỤC TIÊU:
- Biến dữ liệu hồ sơ người học thành một persona ngắn gọn nhưng có giá trị hành động cao.
- Giúp hệ thống hiểu nên dạy người học như thế nào để tăng khả năng tiếp thu và duy trì động lực học.

ƯU TIÊN PHÂN TÍCH:
- Nền tảng học thuật hoặc nghề nghiệp hiện tại
- Mục tiêu học tập chính và kết quả mong muốn
- Thời gian có thể học mỗi ngày hoặc mỗi tuần
- Phong cách học ưu tiên
- Mức độ bận rộn và khả năng duy trì nhịp học
- Mức độ cần ví dụ thực tế, tình huống ứng dụng hoặc case study

HỒ SƠ NGƯỜI HỌC:
{learner_profile}

YÊU CẦU:
1. Dùng tiếng Việt có dấu; có thể giữ lại thuật ngữ chuyên ngành phổ biến bằng tiếng Anh nếu cần.
2. Persona phải ngắn, dễ đọc, tự nhiên, không machine-like.
3. description gồm 2 đến 4 câu, nêu rõ người học này nên được dạy theo cách nào để học hiệu quả hơn.
4. recommended_topics phải có đúng 5 mục.
5. learning_tips phải có đúng 3 mục.
6. personalization_rules phải chỉ ra rõ explanation_style, example_style, pacing và content_depth.
7. Không bịa chi tiết quá xa so với dữ liệu đầu vào.
8. Chỉ trả về JSON hợp lệ, không thêm markdown và không thêm văn bản ngoài JSON.

JSON SHAPE:
{{
  "persona_name": "string",
  "description": "string",
  "background": "string",
  "learning_goal": "string",
  "daily_study_capacity": "string",
  "learning_style": "string",
  "busyness_level": "string",
  "practical_example_need": "string",
  "recommended_topics": ["string", "string", "string", "string", "string"],
  "learning_tips": ["string", "string", "string"],
  "personalization_rules": {{
    "explanation_style": "string",
    "example_style": "string",
    "pacing": "string",
    "content_depth": "string"
  }}
}}
"""


ANALYZE_CONTENT_PROMPT = """
You are DUO MIND's knowledge analyst and explainer.
Your job is to judge factual reliability, extract the core ideas, and explain the content in a way that answers the learner directly and clearly.
Respond in {language}. Return ONLY valid JSON.

CONTENT TO ANALYZE:
\"\"\"
{content}
\"\"\"

STRICT ROLE RULES:
1. Focus on factual accuracy, internal logic, and direct explanatory value.
2. Do not copy the user's text back as-is unless necessary.
3. Prefer concise, high-signal wording over generic filler.
4. If evidence is not sufficient to verify a claim, use accuracy_assessment = "unverifiable" and accuracy_score = null.
5. Explain in plain Vietnamese for a general learner.
6. Do not act like a coach. Do not ask reflective questions, do not guide the learner to think for themselves, and do not use phrases like "hãy tự hỏi", "hãy thử nghĩ", "nếu muốn học tiếp", "người học nên", or "bạn có thể tự".
7. Do not use meta framing such as "ở góc nhìn...", "xét ở...", "về mặt...", "điều quan trọng là...", or "phần này sẽ...".
8. summary must be answer-first: it should tell the learner what this topic means, how it works, and why it matters.
9. key_points must be concrete takeaways, not vague labels, study advice, or repeated summary bullets.
10. Each key point must be a short factual statement the learner can remember.
11. topic_tags must be short noun phrases, not full sentences.

JSON SHAPE:
{{
  "title": "Short topic title",
  "accuracy_score": 78,
  "accuracy_assessment": "high|medium|low|unverifiable",
  "accuracy_reasoning": "One short explanation of the score",
  "summary": "- Bullet 1\\n- Bullet 2\\n- Bullet 3",
  "key_points": [
    "What the learner must remember 1",
    "What the learner must remember 2",
    "What the learner must remember 3",
    "What the learner must remember 4",
    "What the learner must remember 5"
  ],
  "corrections": [
    {{
      "original": "Incorrect or weak claim",
      "correction": "Better or correct version",
      "explanation": "Why the correction is needed"
    }}
  ],
  "topic_tags": ["tag1", "tag2", "tag3", "tag4"],
  "enrichment": "Optional useful extra context in 1-2 sentences"
}}
"""


EXPLORE_TOPIC_PROMPT = """
Bạn là AI giải thích kiến thức của DUO MIND.
Nhiệm vụ của bạn là biến câu hỏi hoặc chủ đề người học nhập vào thành một câu trả lời đầy đủ, dễ hiểu, đi thẳng vào trọng tâm và thật sự giải thích được vấn đề.

CHỦ ĐỀ HOẶC CÂU HỎI CẦN GIẢI THÍCH:
\"\"\"
{prompt}
\"\"\"

MỤC TIÊU ĐẦU RA:
- Trả lời trực diện câu hỏi hoặc chủ đề mà người dùng nhập.
- Giải thích như một người rất giỏi đang nói chuyện với người mới bắt đầu.
- Ưu tiên ví dụ đời thường, phép so sánh đơn giản và tình huống thực tế để người đọc hiểu nhanh.
- Không biến câu trả lời thành bài gợi mở tư duy, bài coaching hay bài hướng dẫn tự suy nghĩ.

LUẬT RÀNG BUỘC:
1. Chỉ trả về JSON hợp lệ.
2. Viết hoàn toàn bằng tiếng Việt có dấu.
3. title phải là tên chủ đề hoặc tên khái niệm, không phải câu hỏi, không có dấu hỏi.
4. Cấm mở đầu bất kỳ mục nào bằng các mẫu như: "phần này giải thích", "hãy hiểu", "hãy nắm", "người học nên", "bạn cần biết", "chúng ta sẽ tìm hiểu", "ở góc nhìn", "xét ở", "về mặt", "điều quan trọng là".
5. Nếu đầu vào là một câu hỏi trực diện, câu đầu tiên của core_concept phải trả lời thẳng câu hỏi đó bằng ngôn ngữ đơn giản.
6. Mỗi mục trong detailed_sections phải mở đầu bằng một câu khẳng định trực diện về kiến thức, không mở đầu bằng cách dẫn nhập.
7. summary phải gồm 4 đến 5 bullet. Mỗi bullet là một ý kiến thức cốt lõi, dài 16 đến 28 từ, không lặp ý.
8. key_points phải gồm đúng 5 ý "lý thuyết cốt lõi". Mỗi ý là một mệnh đề ngắn để ghi nhớ, không viết như lời khuyên học tập.
9. detailed_sections.content phải là kiến thức thật. Mỗi mục gồm 1 đến 2 đoạn ngắn, tổng độ dài khoảng 110 đến 180 từ, và không được lặp lại cùng một cấu trúc câu với các mục khác.
10. core_concept phải định nghĩa khái niệm, phạm vi, mục tiêu và điểm khác biệt với khái niệm gần nó.
11. mechanism phải mô tả tiến trình, logic vận hành hoặc quan hệ nhân quả bên trong chủ đề.
12. components_and_relationships phải nêu rõ từng thành phần chính và mối liên hệ giữa chúng, không liệt kê rời rạc.
13. persona_based_example phải dùng ví dụ đời thường, gần thực tế, dễ hình dung với số đông người học.
14. real_world_applications phải chỉ ra chủ đề này được dùng trong công việc, quyết định, quy trình hay tình huống nào.
15. common_misconceptions phải nêu các hiểu nhầm cụ thể và sửa lại ngắn gọn, rõ nghĩa.
16. next_step_self_study phải cực ngắn, thực dụng và chỉ là phần phụ ở cuối; không được lấn át nội dung giải thích chính.
17. topic_tags phải là 3 đến 4 cụm danh từ ngắn, có dấu, không tách từng từ riêng lẻ.

QUY TẮC CHẤT LƯỢNG:
- Hãy trả lời như một AI giải thích biết rất nhiều nhưng ưu tiên sự rõ ràng.
- Mọi phần phải chứa nội dung kiến thức, không chứa câu hỏi tu từ.
- Không lặp nguyên câu người dùng nhập ở đầu mỗi đoạn.
- Không dùng định nghĩa trống rỗng, không dùng các câu kiểu "đây là một khái niệm quan trọng".
- Khi chủ đề có thể giải thích bằng ví dụ đời thường hoặc phép so sánh đơn giản, hãy ưu tiên cách giải thích đó.
- Nếu phù hợp, có thể dùng các dòng ngắn kiểu liệt kê tự nhiên để người đọc dễ quét mắt và dễ nhớ.
- Không được đẩy câu trả lời theo hướng "tự suy nghĩ", "tự khám phá", hay "nếu muốn có thể tìm hiểu thêm" trừ khi đó chỉ là một câu rất ngắn ở cuối mục next_step_self_study.
- Nếu chủ đề là một câu hỏi như "Thị trường chứng khoán vận hành ra sao?", hãy chuyển thành nội dung tri thức như "Cơ chế vận hành của thị trường chứng khoán".

JSON SHAPE:
{{
  "title": "string",
  "summary": "- Ý cốt lõi 1\\n- Ý cốt lõi 2\\n- Ý cốt lõi 3\\n- Ý cốt lõi 4",
  "key_points": [
    "string",
    "string",
    "string",
    "string",
    "string"
  ],
  "topic_tags": ["string", "string", "string", "string"],
  "detailed_sections": {{
    "core_concept": {{
      "title": "Khái niệm cốt lõi",
      "content": "string"
    }},
    "mechanism": {{
      "title": "Bản chất / cơ chế hoạt động",
      "content": "string"
    }},
    "components_and_relationships": {{
      "title": "Các thành phần chính và quan hệ giữa chúng",
      "content": "string"
    }},
    "persona_based_example": {{
      "title": "Ví dụ trực quan",
      "content": "string"
    }},
    "real_world_applications": {{
      "title": "Ứng dụng thực tế",
      "content": "string"
    }},
    "common_misconceptions": {{
      "title": "Nhầm lẫn phổ biến",
      "content": "string"
    }},
    "next_step_self_study": {{
      "title": "Cách tự học tiếp trong 1 buổi ngắn",
      "content": "string"
    }}
  }},
  "teaching_adaptation": {{
    "focus_priority": "string",
    "tone": "string",
    "depth_control": "string",
    "example_strategy": "string"
  }}
}}
"""


EXPLORE_TOPIC_REWRITE_PROMPT = """
Bạn là AI giải thích kiến thức cấp senior của DUO MIND.
Nhiệm vụ của bạn là viết lại bản nháp bên dưới để nó thật sự trả lời đúng câu hỏi trọng tâm.

CÂU HỎI HOẶC CHỦ ĐỀ GỐC:
\"\"\"
{prompt}
\"\"\"

BẢN NHÁP HIỆN TẠI:
{draft_json}

YÊU CẦU VIẾT LẠI:
1. Chỉ trả về JSON hợp lệ, đúng cùng JSON shape như bản nháp.
2. Trả lời thẳng vào câu hỏi, không né tránh, không viết chung chung.
3. Nếu bản nháp đang nói kiểu "khối kiến thức", "người học", "ở góc nhìn", "thiên về ứng dụng", hoặc lặp lại câu hỏi gốc, hãy loại bỏ hoàn toàn và thay bằng kiến thức thật.
4. Dùng ngôn ngữ đơn giản, gần với cách người thật giải thích cho người mới bắt đầu.
5. Nếu chủ đề phù hợp với ví dụ đời thường, hãy dùng ví dụ rõ ràng và cụ thể.
6. Không coaching, không gợi mở tư duy, không bảo người học tự suy nghĩ thay cho việc giải thích.
7. Câu đầu tiên của core_concept phải trả lời trực tiếp câu hỏi gốc bằng ngôn ngữ dễ hiểu.
8. Mỗi section phải chứa thông tin khác nhau, không lặp lại cùng một ý theo nhiều cách.
9. Không dùng từ "persona" hay tham chiếu tới bối cảnh người học.
"""


MINDMAP_GENERATE_PROMPT = """
Bạn là kiến trúc sư sơ đồ học tập của DUO MIND.
Nhiệm vụ của bạn là tạo mind map ngắn gọn, thông minh, giúp người học nhìn một lần là nắm được bố cục kiến thức của phần giải thích chi tiết.

MỤC TIÊU:
- Mind map là bản đồ tổng quan của phần chi tiết kiến thức.
- Node phải ngắn, rõ, dễ quét mắt.
- Phần sâu hơn sẽ nằm ở details, không nhồi hết vào label.

LUẬT RÀNG BUỘC:
1. Chỉ trả về JSON hợp lệ.
2. Viết bằng tiếng Việt có dấu.
3. Chỉ có đúng 1 root.
4. Có từ 5 đến 7 nhánh chính.
5. Mỗi nhánh chính có từ 2 đến 4 nhánh con nếu thật sự cần.
6. label của nhánh chính chỉ dài 2 đến 5 từ.
7. label của nhánh con chỉ dài 2 đến 6 từ.
8. full_label là câu ngắn giải thích rõ node đó nói về nội dung gì.
9. description phải rất ngắn, tối đa 10 từ, dùng để quét nhanh.
10. details là một câu giải thích ngắn, bổ sung nghĩa cho node.
11. Không dùng câu hỏi làm label hoặc full_label.
12. Không dùng nhãn mơ hồ như "khác", "ghi chú", "nâng cao", "chi tiết".
13. Các nhánh chính nên bao phủ: khái niệm, cơ chế, thành phần, ví dụ, ứng dụng, rủi ro hoặc hiểu nhầm.
14. Nhánh ví dụ và ứng dụng phải bám ví dụ đời thường hoặc tình huống thực tế dễ hiểu.

QUY TẮC CHẤT LƯỢNG:
- Ưu tiên khả năng nhìn sơ đồ là hiểu nhanh.
- Mỗi node phải biểu diễn một ý kiến thức, không phải câu hỏi, không phải khẩu hiệu học tập.
- Không lặp nguyên cụm từ của người dùng ở tất cả các node.
- Root nên là tên chủ đề ngắn gọn, không có dấu hỏi.

JSON SHAPE:
{{
  "topic": "string",
  "mind_map": {{
    "label": "string",
    "full_label": "string",
    "description": "string",
    "details": "string",
    "children": [
      {{
        "label": "string",
        "full_label": "string",
        "description": "string",
        "details": "string",
        "children": [
          {{
            "label": "string",
            "full_label": "string",
            "description": "string",
            "details": "string"
          }}
        ]
      }}
    ]
  }}
}}
"""


# Override onboarding prompt with clean Vietnamese to avoid mojibake affecting Gemini quality.
ONBOARDING_CLASSIFY_PROMPT = """
Bạn là Learning Architect của DUO MIND.
Nhiệm vụ của bạn là đọc hồ sơ người học và tạo ra một learning persona ngắn gọn, thực dụng, đủ rõ để hệ thống cá nhân hóa mentor, roadmap và cách giải thích.

HỒ SƠ NGƯỜI HỌC:
{learner_profile}

MỤC TIÊU:
- Xác định người học này đang ở giai đoạn nào.
- Chỉ ra cách dạy phù hợp nhất với quỹ thời gian, bối cảnh và mục tiêu nghề nghiệp của họ.
- Gợi ý 5 chủ đề nên ưu tiên trước, bám sát mục tiêu thực tế thay vì trả lời chung chung.

NGUYÊN TẮC:
1. Viết hoàn toàn bằng tiếng Việt có dấu.
2. Persona phải ngắn, tự nhiên, không giống nhãn máy móc.
3. description gồm 2 đến 4 câu, nêu rõ nên dạy người học này theo cách nào để học hiệu quả hơn.
4. recommended_topics phải có đúng 5 mục, ưu tiên kỹ năng hoặc chủ đề sát với target role nếu hồ sơ có nêu.
5. learning_tips phải có đúng 3 mục, ngắn và thực dụng.
6. personalization_rules phải nêu rõ explanation_style, example_style, pacing và content_depth.
7. Không bịa thêm chi tiết không có trong hồ sơ.
8. Chỉ trả về JSON hợp lệ, không thêm markdown và không thêm văn bản ngoài JSON.

JSON SHAPE:
{{
  "persona_name": "string",
  "description": "string",
  "background": "string",
  "learning_goal": "string",
  "daily_study_capacity": "string",
  "learning_style": "string",
  "busyness_level": "string",
  "practical_example_need": "string",
  "recommended_topics": ["string", "string", "string", "string", "string"],
  "learning_tips": ["string", "string", "string"],
  "personalization_rules": {{
    "explanation_style": "string",
    "example_style": "string",
    "pacing": "string",
    "content_depth": "string"
  }}
}}
"""


INFOGRAPHIC_GENERATE_PROMPT = """
You are DUO MIND's visual summarizer.
Turn the topic below into a direct, educational infographic data model.
Return ONLY valid JSON.

TITLE: {title}
SUMMARY:
{summary}

KEY POINTS:
{key_points}

STRICT ROLE RULES:
1. Prioritize teaching value over decoration.
2. Every section must represent a real concept, step, comparison, or statistic.
3. highlight should contain a short hook, keyword, or number only.
4. Do not repeat the title inside every section.

JSON SHAPE:
{{
  "type": "steps|comparison|statistics|timeline|list",
  "theme_color": "#0f766e",
  "title": "Infographic title",
  "subtitle": "Short subtitle",
  "sections": [
    {{
      "icon": "1",
      "heading": "Section heading",
      "content": "Compact explanation",
      "highlight": "Keyword or number"
    }}
  ],
  "footer_note": "Optional note"
}}
"""


QUIZ_GENERATE_PROMPT = """
You are DUO MIND's assessment designer.
Create a focused multiple-choice quiz from the study material below.
Respond in {language}. Return ONLY valid JSON.

TOPIC: {title}

STUDY MATERIAL:
{material_json}

RULES:
1. Create exactly {num_questions} multiple-choice questions.
2. Each question must have 4 options: A, B, C, D.
3. Every question must stay tightly centered on the topic and material above.
4. Prefer testing core meaning, mechanism, right-vs-wrong distinctions, misconceptions, and real application of the exact content.
5. If the material contains corrections, use them to create at least one question that checks the corrected idea.
6. Every question stem must mention the exact concept, distinction, or claim being tested. Avoid generic stems such as "phần 1" or "ý nào đúng".
7. Wrong options must be plausible but clearly refuted by the supplied material. Do not use joke answers or unrelated trivia.
8. Explanations must teach briefly, not just reveal the answer.
9. Difficulty mix should feel balanced.
10. Do not ask trivia outside the supplied material.

JSON SHAPE:
{{
  "questions": [
    {{
      "order_index": 0,
      "question_type": "multiple_choice",
      "question_text": "Question text",
      "options": [
        {{"id": "A", "text": "Option A"}},
        {{"id": "B", "text": "Option B"}},
        {{"id": "C", "text": "Option C"}},
        {{"id": "D", "text": "Option D"}}
      ],
      "correct_answer": "A",
      "explanation": "Why this answer is correct",
      "difficulty": "easy|medium|hard"
    }}
  ]
}}
"""


OPEN_QUESTIONS_PROMPT = """
You are DUO MIND's critical-thinking question designer.
Create focused open-ended questions from the topic and study material below.
Respond in {language}. Return ONLY valid JSON.

TOPIC: {title}
STUDY MATERIAL:
{material_json}

RULES:
1. Create exactly 2 open questions.
2. Questions must stay on the main topic and extend thinking through analysis, evaluation, comparison, or application.
3. Question 1 should force the learner to explain why a statement is right, wrong, incomplete, or easy to misunderstand if the material supports that.
4. Question 2 should ask the learner to apply, compare, or re-explain the exact topic in a concrete situation.
5. Include exactly 2 thinking_hints and 2-3 sample_answer_points for each question.
6. Do not mention persona, learner profile, or unrelated topics.
7. Avoid vague prompts such as "Theo bạn..." unless the rest of the stem is specific and anchored to the material.

JSON SHAPE:
{{
  "questions": [
    {{
      "order_index": 0,
      "question_type": "open",
      "question_text": "Open question",
      "thinking_hints": ["Hint 1", "Hint 2"],
      "sample_answer_points": ["Point 1", "Point 2"],
      "difficulty": "medium|hard"
    }}
  ]
}}
"""


OPEN_ANSWER_FEEDBACK_PROMPT = """
You are DUO MIND's answer reviewer.
Evaluate the learner's open-ended response.
Respond in {language}. Return ONLY valid JSON.

QUESTION:
{question}

EVALUATION POINTS:
{sample_points}

LEARNER ANSWER:
\"\"\"
{user_answer}
\"\"\"

RULES:
1. Score critical_thinking_score from 0 to 10.
2. Feedback must be constructive and specific.
3. Separate strengths and improvements clearly.

JSON SHAPE:
{{
  "critical_thinking_score": 7,
  "ai_feedback": "Detailed review",
  "strengths": ["Strength 1", "Strength 2"],
  "improvements": ["Improvement 1", "Improvement 2"],
  "missed_points": ["Missed point 1"]
}}
"""


KNOWLEDGE_ANALYTICS_PROMPT = """
You are DUO MIND's learning analyst.
Review the learner history below and return ONLY valid JSON in Vietnamese.

LEARNER CONTEXT:
- Persona: {user_persona}
- Member since: {member_since}

LEARNING HISTORY:
{sessions_summary}

QUIZ STATS:
- Total quizzes: {total_quizzes}
- Average score: {avg_quiz_score}

RULES:
1. Summarize the learner journey in practical language.
2. strongest_topics and weakest_topics must be concrete.
3. Provide 3 useful next-step recommendations.

JSON SHAPE:
{{
  "ai_summary": "Overall learning summary",
  "strongest_topics": ["Strong topic 1", "Strong topic 2"],
  "weakest_topics": ["Weak topic 1", "Weak topic 2"],
  "learning_pattern": "consistent|sporadic|intensive|new",
  "knowledge_depth": "surface|intermediate|deep",
  "ai_recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"],
  "achievement_highlights": ["Highlight 1", "Highlight 2"],
  "next_milestone": "Next milestone"
}}
"""


ANALYZE_CONTENT_FOCUSED_PROMPT = """
You are DUO MIND's precision knowledge analyst.
Your job is to identify exactly what the learner is trying to understand, evaluate the submitted content, and explain only the relevant topic directly.
Respond in {language}. Return ONLY valid JSON.

FOCUS_TOPIC:
{focus_topic}

LEARNER_CONTEXT:
{learner_context_json}

CONTENT TO ANALYZE:
\"\"\"
{content}
\"\"\"

STRICT DECISION RULES:
1. Keep every output centered on FOCUS_TOPIC. Do not drift into neighboring topics unless they are required to explain FOCUS_TOPIC.
2. Treat the submitted content as the learner's current notes, draft understanding, or source text to evaluate.
3. If the content contains mixed ideas, prioritize the idea most directly related to FOCUS_TOPIC.
4. If evidence is not sufficient to verify a claim, use accuracy_assessment = "unverifiable" and accuracy_score = null.
5. Explain directly. Do not coach, do not motivate, and do not ask reflective questions.
6. Do not use generic framing such as "ở góc nhìn", "điều quan trọng là", "người học nên", "hãy thử nghĩ", or "phần này sẽ".
7. summary must answer the learner first: what FOCUS_TOPIC means in this content, what is correct or unclear, and what matters most.
8. key_points must be 4 to 5 concise factual takeaways directly about FOCUS_TOPIC.
9. corrections must only include specific unclear, weak, or incorrect statements found in the content.
10. title must be the topic name, not a generic label.
11. topic_tags must stay close to FOCUS_TOPIC, not broad adjacent domains.

LENGTH RULES:
- summary: 3 to 4 bullets
- each summary bullet: 1 sentence
- each key point: under 22 words
- accuracy_reasoning: 1 short sentence

JSON SHAPE:
{{
  "title": "Focused topic title",
  "accuracy_score": 78,
  "accuracy_assessment": "high|medium|low|unverifiable",
  "accuracy_reasoning": "One short explanation of the score",
  "summary": "- Bullet 1\\n- Bullet 2\\n- Bullet 3",
  "key_points": [
    "Focused takeaway 1",
    "Focused takeaway 2",
    "Focused takeaway 3",
    "Focused takeaway 4",
    "Focused takeaway 5"
  ],
  "corrections": [
    {{
      "original": "Specific unclear or incorrect claim from the content",
      "correction": "Better or correct version",
      "explanation": "Why the correction is needed"
    }}
  ],
  "topic_tags": ["tag1", "tag2", "tag3", "tag4"],
  "enrichment": "Optional extra context in 1 sentence if truly useful"
}}
"""


ANALYZE_CONTENT_FOCUSED_REWRITE_PROMPT = """
You are rewriting a weak DUO MIND analysis draft so it becomes focused, correct, and directly useful.
Respond in {language}. Return ONLY valid JSON.

FOCUS_TOPIC:
{focus_topic}

LEARNER_CONTEXT:
{learner_context_json}

CONTENT TO ANALYZE:
\"\"\"
{content}
\"\"\"

CURRENT DRAFT JSON:
{draft_json}

REWRITE RULES:
1. Keep the answer tightly centered on FOCUS_TOPIC.
2. Remove generic, broad, or off-topic explanations.
3. If the draft sounds like a lecture about the whole field, narrow it back to the specific topic the learner needs.
4. summary must be short, direct, and answer-first.
5. key_points must be concrete and directly related to FOCUS_TOPIC.
6. corrections must stay anchored to actual statements in the content.
7. Do not use coaching language, meta framing, or vague filler.
8. Keep the same JSON schema as the main analysis prompt.
"""


EXPLORE_TOPIC_FOCUSED_PROMPT = """
Ban la AI giai thich kien thuc chinh xac cua DUO MIND.
Nhiem vu cua ban la tra loi dung chu de nguoi dung can kham pha, khong lan man sang cac nhom kien thuc lan can.
Chi tra ve JSON hop le.

USER_PROMPT:
\"\"\"
{prompt}
\"\"\"

FOCUS_TOPIC:
{focus_topic}

LEARNER_CONTEXT:
{learner_context_json}

MUC TIEU:
1. Giai thich dung FOCUS_TOPIC bang noi dung thuc chat, de hieu, co logic.
2. Neu USER_PROMPT la mot cau hoi, cau dau tien cua core_concept phai tra loi thang cau hoi do.
3. Neu co learner_context, chi dung de chon vi du phu hop. Khong de context lam lech chu de.
4. Moi phan phai noi them thong tin moi, khong lap y va khong dien giai mo rong lan man.

CAM:
- noi chung chung nhu "day la mot khai niem quan trong"
- lap lai cau hoi goc trong moi section
- coaching, hoi nguoc lai nguoi hoc, hay noi "nguoi hoc nen"
- bien cau tra loi thanh bai tong quan ve ca linh vuc rong hon FOCUS_TOPIC

DO DAI:
- summary: 4 bullet, moi bullet 1 cau
- key_points: dung 5 y, moi y duoi 22 tu
- moi detailed section: 90 den 150 tu, noi truc tiep vao kien thuc

JSON SHAPE:
{{
  "title": "string",
  "summary": "- Ý cốt lõi 1\\n- Ý cốt lõi 2\\n- Ý cốt lõi 3\\n- Ý cốt lõi 4",
  "key_points": ["string", "string", "string", "string", "string"],
  "topic_tags": ["string", "string", "string", "string"],
  "detailed_sections": {{
    "core_concept": {{"title": "Khái niệm cốt lõi", "content": "string"}},
    "mechanism": {{"title": "Bản chất / cơ chế hoạt động", "content": "string"}},
    "components_and_relationships": {{"title": "Các thành phần chính và quan hệ giữa chúng", "content": "string"}},
    "persona_based_example": {{"title": "Ví dụ trực quan dễ hiểu", "content": "string"}},
    "real_world_applications": {{"title": "Ứng dụng thực tế", "content": "string"}},
    "common_misconceptions": {{"title": "Nhầm lẫn phổ biến", "content": "string"}},
    "next_step_self_study": {{"title": "Tự học tiếp trong 1 buổi ngắn", "content": "string"}}
  }},
  "teaching_adaptation": {{
    "focus_priority": "string",
    "tone": "string",
    "depth_control": "string",
    "example_strategy": "string"
  }}
}}
"""


EXPLORE_TOPIC_FOCUSED_REWRITE_PROMPT = """
Ban dang sua mot ban nhap Explore bi lan man, generic, hoac lech chu de.
Chi tra ve JSON hop le.

USER_PROMPT:
\"\"\"
{prompt}
\"\"\"

FOCUS_TOPIC:
{focus_topic}

LEARNER_CONTEXT:
{learner_context_json}

CURRENT DRAFT JSON:
{draft_json}

REWRITE RULES:
1. Dua cau tra loi ve dung FOCUS_TOPIC.
2. Xoa cac doan noi ve linh vuc rong hon neu khong can de giai thich chu de chinh.
3. Core_concept phai tra loi thang cau hoi nguoi dung muon hieu.
4. Key_points va summary phai doc la biet ngay chu de can kham pha la gi.
5. Neu can dung vi du, hay dung vi du don gian va sat FOCUS_TOPIC.
6. Khong coaching, khong meta framing, khong noi chuyen ve "nguoi hoc".
7. Giu nguyen JSON shape nhu prompt chinh.
"""

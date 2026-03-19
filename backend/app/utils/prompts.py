# ============================================================
# DUO MIND - Gemini Prompt Templates
# ============================================================

ONBOARDING_CLASSIFY_PROMPT = """
You are DUO MIND's learning architect.
Classify the learner profile below and return ONLY valid JSON.

LEARNER PROFILE:
- Age range: {age_range}
- Status: {status}
- Education level: {education_level}
- Major: {major}
- School: {school_name}
- Industry: {industry}
- Job title: {job_title}
- Years of experience: {years_experience}
- Learning goals: {learning_goals}
- Topics of interest: {topics_of_interest}
- Learning style: {learning_style}
- Daily study minutes: {daily_study_minutes}

OUTPUT RULES:
1. Persona must be short, concrete, and easy to understand.
2. Description must explain learner needs in 2-3 sentences.
3. Recommend exactly 5 topics.
4. Recommend exactly 3 practical learning tips.
5. difficulty_level must be one of: beginner, intermediate, advanced.
6. Return ONLY JSON.

JSON SHAPE:
{{
  "persona": "university_tech_student",
  "description": "Short profile description.",
  "recommended_topics": ["topic1", "topic2", "topic3", "topic4", "topic5"],
  "learning_tips": ["tip1", "tip2", "tip3"],
  "difficulty_level": "beginner|intermediate|advanced"
}}
"""

ANALYZE_CONTENT_PROMPT = """
You are DUO MIND's knowledge auditor and study coach.
Your job is to judge factual reliability, extract the core ideas, and rewrite the result so a learner can review it quickly.
Respond in {language}. Return ONLY valid JSON.

LEARNER CONTEXT:
- Persona: {user_persona}
- Difficulty level: {difficulty_level}

CONTENT TO ANALYZE:
\"\"\"
{content}
\"\"\"

STRICT ROLE RULES:
1. Focus on factual accuracy, internal logic, and teachable value.
2. Do not copy the user's text back as-is unless necessary.
3. Prefer concise, high-signal wording over generic filler.
4. If evidence is not sufficient to verify a claim, use accuracy_assessment = "unverifiable" and accuracy_score = null.
5. key_points must be concrete takeaways, not vague labels.
6. topic_tags must be short noun phrases, not full sentences.

OUTPUT DESIGN:
- title: short and focused, max 60 characters.
- summary: 3-5 short review bullets separated by newline characters. Each bullet must be a self-contained idea.
- key_points: exactly the most important facts/concepts the learner should remember.
- corrections: only include real problems. Use [] if nothing meaningful needs correction.

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
You are DUO MIND's teaching explainer.
Your job is to help the learner understand a topic fast, clearly, and in the right order.
Respond in {language}. Return ONLY valid JSON.

LEARNER CONTEXT:
- Persona: {user_persona}
- Difficulty level: {difficulty_level}
- Learning goals: {learning_goals}

TOPIC OR QUESTION:
\"\"\"
{prompt}
\"\"\"

STRICT ROLE RULES:
1. Explain in a teaching sequence: definition -> how it works -> example -> applications or limits.
2. Avoid hype, vague claims, and decorative language.
3. Write for learning, not for marketing.
4. key_points must be the exact things a learner should know and remember.
5. topic_tags must be short core concepts only.

OUTPUT DESIGN:
- title: short, direct, learner-friendly.
- summary: 4-6 short bullets separated by newline characters. These bullets must answer "What should I understand first?"
- key_points: 5 clear "must remember" bullets.
- detailed_sections: each section must add value, not repeat summary.
- common_misconceptions: include only real misconceptions if relevant.

JSON SHAPE:
{{
  "title": "Clear topic title",
  "summary": "- Core idea 1\\n- Core idea 2\\n- Core idea 3\\n- Core idea 4",
  "key_points": [
    "Must-remember point 1",
    "Must-remember point 2",
    "Must-remember point 3",
    "Must-remember point 4",
    "Must-remember point 5"
  ],
  "detailed_sections": [
    {{
      "heading": "Section name",
      "content": "Concrete explanation in 2-4 sentences",
      "examples": ["Example 1", "Example 2"]
    }}
  ],
  "fun_facts": ["Useful fact 1", "Useful fact 2"],
  "common_misconceptions": ["Misconception 1", "Misconception 2"],
  "topic_tags": ["tag1", "tag2", "tag3", "tag4"],
  "related_topics": ["Related topic 1", "Related topic 2", "Related topic 3"]
}}
"""

MINDMAP_GENERATE_PROMPT = """
You are DUO MIND's knowledge mapper.
Convert the content below into a precise learning mind map for React Flow.
Return ONLY valid JSON.

MAIN TOPIC: {title}
CONTENT:
\"\"\"
{content}
\"\"\"

STRICT ROLE RULES:
1. Build a true hierarchy: 1 root -> 4-6 main branches -> 2-4 child nodes per main branch whenever useful.
2. Root and main branches must cover the topic comprehensively without overlap.
3. label must be short enough for display, but meaningful.
4. Put the full explanation in description or details, not in a giant label.
5. Do not generate vague labels such as "Overview", "Thing", "Misc", or "Info".
6. Use node types exactly: root, main, sub.

JSON SHAPE:
{{
  "nodes": [
    {{
      "id": "root",
      "type": "root",
      "data": {{
        "label": "Short root label",
        "full_label": "Full root label if needed",
        "description": "One-line explanation",
        "details": "Longer explanation for click-to-view mode"
      }},
      "position": {{"x": 0, "y": 0}}
    }},
    {{
      "id": "main_1",
      "type": "main",
      "data": {{
        "label": "Short branch label",
        "full_label": "Full branch label",
        "description": "One-line explanation",
        "details": "Longer explanation",
        "color": "#0f766e"
      }},
      "position": {{"x": -220, "y": 180}}
    }},
    {{
      "id": "sub_1_1",
      "type": "sub",
      "data": {{
        "label": "Short sub label",
        "full_label": "Full sub label",
        "description": "One-line explanation",
        "details": "Longer explanation"
      }},
      "position": {{"x": -360, "y": 320}}
    }}
  ],
  "edges": [
    {{
      "id": "edge_root_main_1",
      "source": "root",
      "target": "main_1",
      "type": "smoothstep"
    }},
    {{
      "id": "edge_main_1_sub_1_1",
      "source": "main_1",
      "target": "sub_1_1",
      "type": "smoothstep"
    }}
  ]
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
Create a multiple-choice quiz from the content below.
Respond in {language}. Return ONLY valid JSON.

LEARNER CONTEXT:
- Persona: {user_persona}
- Difficulty level: {difficulty_level}

CONTENT:
\"\"\"
{content}
\"\"\"

SUMMARY:
{summary}

RULES:
1. Create exactly {num_questions} multiple-choice questions.
2. Each question must have 4 options: A, B, C, D.
3. Explanations must teach, not just reveal the answer.
4. Difficulty mix should feel balanced.

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
You are DUO MIND's critical-thinking coach.
Create open-ended questions from the topic below.
Respond in {language}. Return ONLY valid JSON.

LEARNER CONTEXT:
- Persona: {user_persona}
- Difficulty level: {difficulty_level}

TOPIC: {title}
SUMMARY:
{summary}

RULES:
1. Create 2-3 open questions.
2. Questions must invite analysis, evaluation, or application.
3. Include thinking_hints and sample_answer_points for each question.

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

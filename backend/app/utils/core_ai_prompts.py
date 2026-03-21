import json
from typing import Any


ONBOARDING_CLASSIFY_CORE_PROMPT = """
You are DUO MIND's onboarding intelligence.
Read the learner profile and create a practical persona for a Vietnamese learning platform.
Return ONLY valid JSON.

LEARNER PROFILE:
{learner_profile}

GOAL:
- Understand the learner's real study context, short-term outcome, constraints, and target role.
- Produce a persona that is specific enough to personalize mentor and roadmap flows.
- Prioritize the learner's own target role, desired outcome, current focus, and current challenges.

RULES:
1. The final JSON values must be written in natural Vietnamese.
2. Do not invent a different career path from the learner's target role.
3. The description must explicitly reflect current context, desired outcome, constraints, and recommended teaching approach.
4. recommended_topics must contain exactly 5 concrete topics or skills.
5. learning_tips must contain exactly 3 short, practical tips.
6. personalization_rules must stay concrete and actionable.
7. Avoid generic labels unless the profile truly lacks data.
8. If the profile includes a custom target role, keep that role as the main direction.

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


EXPLORE_QUERY_PLAN_PROMPT = """
You are DUO MIND's topic understanding layer.
Read the learner's prompt and produce a strict answer plan before any explanation is written.
Return ONLY valid JSON.

USER_PROMPT:
\"\"\"
{prompt}
\"\"\"

RULES:
1. Identify the exact question the learner wants answered.
2. Keep only one central focus topic.
3. If the prompt is a comparison, preserve both comparison targets exactly.
4. If the prompt asks "gom gi", "bao gom gi", "thanh phan nao", or "cau truc ra sao", set question_type to "structure".
5. Remove stylistic instructions such as "easy", "short", "for beginners", or "career-oriented" from focus_topic.
6. Do not write the final explanation here.

JSON SHAPE:
{{
  "question_type": "definition|comparison|mechanism|structure|general",
  "main_question": "string",
  "focus_topic": "string",
  "comparison_targets": ["string", "string"],
  "must_include": ["string", "string", "string"],
  "must_avoid": ["string", "string"],
  "answer_strategy": "string"
}}
"""


ANALYZE_QUERY_PLAN_PROMPT = """
You are DUO MIND's analysis understanding layer.
Read the learner's analysis request and determine exactly what must be checked.
Return ONLY valid JSON.

USER_ANALYSIS_GOAL:
{analysis_goal}

FOCUS_TOPIC_CANDIDATE:
{focus_topic}

CONTENT TO ANALYZE:
\"\"\"
{content}
\"\"\"

RULES:
1. Identify the single main question the learner wants checked.
2. Keep only one central focus topic.
3. If the learner is comparing two things, preserve both targets exactly.
4. If the learner asks "gom gi", "bao gom gi", "thanh phan nao", or "cau truc ra sao", set analysis_kind to "structure".
5. Extract 2 to 4 evidence targets that should be checked in the content.
6. Do not write the final analysis here.

JSON SHAPE:
{{
  "analysis_kind": "definition|comparison|mechanism|structure|review",
  "main_question": "string",
  "focus_topic": "string",
  "comparison_targets": ["string", "string"],
  "evidence_targets": ["string", "string", "string"],
  "must_include": ["string", "string", "string"],
  "must_avoid": ["string", "string"],
  "answer_strategy": "string"
}}
"""


ANALYZE_CONTENT_BLUEPRINT_PROMPT = """
You are DUO MIND's analysis planning layer.
Build a content blueprint before any teaching note is written.
Return ONLY valid JSON.

LANGUAGE: {language}
USER_ANALYSIS_GOAL: {analysis_goal}
FOCUS_TOPIC: {focus_topic}
ANALYSIS_BRIEF:
{analysis_brief_json}
VERIFICATION_SOURCES:
{source_brief_json}

CONTENT TO ANALYZE:
\"\"\"
{content}
\"\"\"

MISSION:
1. Identify the corrected knowledge the learner should keep after this analysis.
2. Build a blueprint with non-overlapping knowledge axes.
3. Keep the blueprint tightly centered on FOCUS_TOPIC and the learner's actual question.

RULES:
1. Do not write the final explanation yet.
2. Every field must contain concrete knowledge, not filler.
3. If sources are thin, stay conservative and avoid invented specifics.
4. For comparison topics, keep both sides visible across the blueprint.
5. For structure topics, make the main parts explicit in components and their relationships.
6. For definition topics, make the scope boundary explicit.

JSON SHAPE:
{{
  "core_definition": "string",
  "scope_boundary": "string",
  "mechanism": "string",
  "components": "string",
  "input_process_output": "string",
  "example": "string",
  "application": "string",
  "misconceptions": "string",
  "conditions_and_limits": "string",
  "related_concepts": "string",
  "decision_value": "string"
}}
"""


ANALYZE_CONTENT_CORE_PROMPT = """
You are DUO MIND's precision analysis engine.
You must judge the learner's submitted content, then render a corrected teaching note from the approved blueprint.
Return ONLY valid JSON.

LANGUAGE: {language}
USER_ANALYSIS_GOAL: {analysis_goal}
FOCUS_TOPIC: {focus_topic}
LEARNER_CONTEXT:
{learner_context_json}
ANALYSIS_BRIEF:
{analysis_brief_json}
VERIFICATION_SOURCES:
{source_brief_json}
CONTENT_BLUEPRINT:
{blueprint_json}

IMPORTANT CONTEXT RULE:
- LEARNER_CONTEXT is optional supporting context.
- Use it only when it materially improves clarity, framing, or example choice.
- If it distracts from USER_ANALYSIS_GOAL or from the submitted content, ignore it.
- Prioritize a direct expert answer over personalization.

QUESTION-FRAME PRIORITY:
- If USER_ANALYSIS_GOAL asks "la gi", correct the definition and scope before broader explanation.
- If USER_ANALYSIS_GOAL asks "gom gi", "bao gom gi", "thanh phan nao", or "cau truc ra sao", name the main parts first and explain each part's role.
- If USER_ANALYSIS_GOAL is a comparison, keep both sides visible from the start and compare on clear axes.
- If USER_ANALYSIS_GOAL asks "hoat dong nhu the nao" or "vi sao", explain the operating logic first.
- Never widen a narrow question into a generic overview of the whole field.

CONTENT TO ANALYZE:
\"\"\"
{content}
\"\"\"

SECTION ROLES:
1. summary = a verdict block about the learner's submitted content
2. detailed_sections.core_concept = what the topic is, what it is not, and the scope boundary
3. detailed_sections.mechanism = how it works or why it behaves that way
4. detailed_sections.components_and_relationships = the main parts and their relationships
5. detailed_sections.persona_based_example = one concrete example close to the learner context
6. detailed_sections.real_world_applications = where this knowledge matters in practice
7. detailed_sections.common_misconceptions = misunderstanding, false comparison, or misuse case
8. detailed_sections.next_step_self_study = the next boundary or deeper question, not motivational advice

GUARDRAILS:
1. Do not paraphrase the same idea across sections.
2. Do not use empty phrases such as "this is important", "helps understand better", or "need to grasp the essence".
3. If a section cannot add new information, narrow the section instead of repeating.
4. Corrections must only address claims present in the submitted content.
5. Do not answer with a generic field overview when the learner asked one concrete question.
6. Never invent citations or output URLs.
7. Every bullet and section must teach a real idea, not a learning tip or motivational sentence.
8. Prefer concrete nouns, mechanisms, criteria, parts, limits, and confusion points over abstract filler.

OUTPUT CONTRACT:
- title: short and core to the topic
- accuracy_assessment: high|medium|low|unverifiable
- accuracy_score: null when unverifiable
- accuracy_reasoning: one short sentence
- summary: exactly 4 bullets
- key_points: exactly 4 to 5 corrected knowledge bullets, short and concrete
- summary bullet 1: direct verdict on the submitted content
- summary bullet 2: what is correct or usable
- summary bullet 3: what is weak, missing, or unsupported
- summary bullet 4: what corrected knowledge the learner should keep
- each summary bullet should be one dense teaching sentence, not a vague comment
- key_points bullet 1: corrected core definition or main conclusion
- key_points bullet 2: mechanism or operating logic
- key_points bullet 3: main structure, criteria, or comparison axis
- key_points bullet 4: limit, misuse, or application condition
- key_points bullet 5 when present: practical implication or misconception worth remembering
- key_points must be theory-heavy and non-overlapping with summary; avoid verdict language inside key_points
- corrections: at most 4 items, only when the submitted content contains a specific weak or wrong claim
- every detailed section must be grounded in CONTENT_BLUEPRINT and have a distinct role
- detailed_sections.core_concept must explicitly answer "topic nay la gi"
- detailed_sections.mechanism must include at least two of: mechanism, logic, input-process-output, limits
- if USER_ANALYSIS_GOAL asks about structure or components, detailed_sections.components_and_relationships must name the main parts before discussing applications
- detailed_sections.common_misconceptions must include at least one of: misunderstanding, comparison trap, misuse case
- never end sections by asking the learner a question back
- detailed_sections.core_concept should open with a direct answer, then draw the scope boundary
- detailed_sections.mechanism should explain a causal chain, operating logic, or input-process-output flow
- detailed_sections.components_and_relationships should explicitly name parts, criteria, or comparison axes before deeper explanation

JSON SHAPE:
{{
  "title": "Focused topic title",
  "accuracy_score": 78,
  "accuracy_assessment": "high|medium|low|unverifiable",
  "accuracy_reasoning": "One short explanation of the score",
  "summary": "- Bullet 1\\n- Bullet 2\\n- Bullet 3\\n- Bullet 4",
  "key_points": ["string", "string", "string", "string"],
  "corrections": [
    {{
      "original": "Specific unclear or incorrect claim from the content",
      "correction": "Better or correct version",
      "explanation": "Why the correction is needed"
    }}
  ],
  "topic_tags": ["tag1", "tag2", "tag3", "tag4"],
  "detailed_sections": {{
    "core_concept": {{"title": "Khái niệm cốt lõi", "content": "string"}},
    "mechanism": {{"title": "Bản chất / cơ chế hoạt động", "content": "string"}},
    "components_and_relationships": {{"title": "Các thành phần chính và quan hệ giữa chúng", "content": "string"}},
    "persona_based_example": {{"title": "Ví dụ trực quan", "content": "string"}},
    "real_world_applications": {{"title": "Ứng dụng thực tế", "content": "string"}},
    "common_misconceptions": {{"title": "Nhầm lẫn phổ biến", "content": "string"}},
    "next_step_self_study": {{"title": "Điểm cần nắm tiếp", "content": "string"}}
  }},
  "teaching_adaptation": {{
    "focus_priority": "string",
    "tone": "string",
    "depth_control": "string",
    "example_strategy": "string"
  }}
}}
"""


ANALYZE_CONTENT_REPAIR_PROMPT = """
You are DUO MIND's analysis answer rewriter.
A previous draft was too generic, drifted away from the learner's question, or did not judge the submitted content sharply enough.
Rewrite the analysis from scratch using the approved blueprint.
Return ONLY valid JSON.

LANGUAGE: {language}
USER_ANALYSIS_GOAL: {analysis_goal}
FOCUS_TOPIC: {focus_topic}
LEARNER_CONTEXT:
{learner_context_json}
ANALYSIS_BRIEF:
{analysis_brief_json}
VERIFICATION_SOURCES:
{source_brief_json}
CONTENT_BLUEPRINT:
{blueprint_json}
WEAK_DRAFT:
{weak_draft_json}

CONTENT TO ANALYZE:
\"\"\"
{content}
\"\"\"

MISSION:
1. Judge the learner's submitted content directly and intelligently.
2. Keep the analysis tightly centered on USER_ANALYSIS_GOAL.
3. Repair filler, drift, repetition, weak verdicts, and weak section roles.

QUESTION-FRAME RULES:
- Definition analysis: correct the definition first, then scope, then confusion points.
- Structure analysis: list the main parts first, then explain each part's role and relationship.
- Comparison analysis: mention both sides immediately and compare on clear axes.
- Mechanism analysis: explain the operating chain first, not broad history or adjacent topics.
- Review analysis: stay with the learner's real question and the submitted claims.

GUARDRAILS:
1. Open with a clear verdict on the submitted content, not with meta commentary.
2. Do not write filler such as "this is important", "helps understand better", or "in many fields".
3. Do not repeat the same idea across summary, key points, and sections.
4. Corrections must only target claims that are actually present in CONTENT TO ANALYZE.
5. Use LEARNER_CONTEXT only if it improves the example. Never let it hijack the answer.
6. Never invent citations or URLs inside the explanation.
7. Every bullet and section must carry concrete knowledge, not study advice or generic observations.

OUTPUT CONTRACT:
- title: short and direct
- accuracy_assessment: high|medium|low|unverifiable
- accuracy_score: null when unverifiable
- summary: exactly 4 bullets
- key_points: exactly 4 to 5 bullets
- summary bullet 1: direct verdict on the submitted content
- summary bullet 2: what is correct or usable
- summary bullet 3: what is weak, missing, or unsupported
- summary bullet 4: what corrected knowledge the learner should keep
- each summary bullet should contain a concrete claim, boundary, mechanism, or criterion
- corrections: at most 4 items
- key_points must be dense corrected theory bullets, not a softer paraphrase of summary
- core_concept first sentence must answer the real question being checked
- components_and_relationships must name the main parts when USER_ANALYSIS_GOAL asks about structure or components
- mechanism must explain the operating logic or causal chain, not just reword the concept
- next_step_self_study must point to a deeper boundary, not generic encouragement

JSON SHAPE:
{{
  "title": "Focused topic title",
  "accuracy_score": 78,
  "accuracy_assessment": "high|medium|low|unverifiable",
  "accuracy_reasoning": "One short explanation of the score",
  "summary": "- Bullet 1\\n- Bullet 2\\n- Bullet 3\\n- Bullet 4",
  "key_points": ["string", "string", "string", "string"],
  "corrections": [
    {{
      "original": "string",
      "correction": "string",
      "explanation": "string"
    }}
  ],
  "topic_tags": ["string", "string", "string"],
  "detailed_sections": {{
    "core_concept": {{"title": "string", "content": "string"}},
    "mechanism": {{"title": "string", "content": "string"}},
    "components_and_relationships": {{"title": "string", "content": "string"}},
    "persona_based_example": {{"title": "string", "content": "string"}},
    "real_world_applications": {{"title": "string", "content": "string"}},
    "common_misconceptions": {{"title": "string", "content": "string"}},
    "next_step_self_study": {{"title": "string", "content": "string"}}
  }},
  "teaching_adaptation": {{
    "focus_priority": "string",
    "tone": "string",
    "depth_control": "string",
    "example_strategy": "string"
  }}
}}
"""


EXPLORE_TOPIC_BLUEPRINT_PROMPT = """
You are DUO MIND's topic planning layer.
Build a content blueprint before writing the final explanation.
Return ONLY valid JSON.

USER_PROMPT:
\"\"\"
{prompt}
\"\"\"

FOCUS_TOPIC: {focus_topic}
EXPLORE_BRIEF:
{explore_brief_json}
VERIFICATION_SOURCES:
{source_brief_json}

MISSION:
1. Identify the exact knowledge the learner needs to understand.
2. Split that knowledge into distinct teaching axes.
3. Keep the blueprint tightly centered on FOCUS_TOPIC.

RULES:
1. Do not write the final lesson yet.
2. Each field must add new information, not rephrase another field.
3. If the prompt is a comparison, keep both topics visible.
4. If the prompt asks for components, structure, or main parts, make those parts explicit in components and their relationships.
5. If the prompt is a definition, state the scope boundary.
6. Never invent article titles, URLs, authors, or dates.

JSON SHAPE:
{{
  "core_definition": "string",
  "scope_boundary": "string",
  "mechanism": "string",
  "components": "string",
  "input_process_output": "string",
  "example": "string",
  "application": "string",
  "misconceptions": "string",
  "conditions_and_limits": "string",
  "related_concepts": "string",
  "decision_value": "string"
}}
"""


EXPLORE_TOPIC_CORE_PROMPT = """
You are DUO MIND's focused explainer.
Your job is to render a high-value learning note from the approved blueprint without drifting away from the learner's question.
Return ONLY valid JSON.

USER_PROMPT:
\"\"\"
{prompt}
\"\"\"

FOCUS_TOPIC: {focus_topic}
LEARNER_CONTEXT:
{learner_context_json}
EXPLORE_BRIEF:
{explore_brief_json}
VERIFICATION_SOURCES:
{source_brief_json}
CONTENT_BLUEPRINT:
{blueprint_json}

IMPORTANT CONTEXT RULE:
- LEARNER_CONTEXT is optional supporting context.
- Use it only when it makes the explanation clearer or the example more relevant.
- If it bends the answer away from the real question, ignore it.
- Prefer a direct expert explanation over personalization.

QUESTION-FRAME PRIORITY:
- If the learner asks "la gi", answer the definition and scope before any broad overview.
- If the learner asks "gom gi", "bao gom gi", "thanh phan nao", or "cau truc ra sao", answer the main parts first and explain each part's role.
- If the learner asks for comparison, show the comparison axes immediately instead of teaching each topic separately.
- If the learner asks "hoat dong nhu the nao", "van hanh ra sao", or "vi sao", explain the operating logic first.
- Never widen a narrow question into an overview of the whole field.

SECTION ROLES:
1. core_concept = what the topic is, why the scope matters, and what it should not be confused with
2. mechanism = how the topic works and why it behaves that way
3. components_and_relationships = the main parts, criteria, or comparison axes
4. persona_based_example = one concrete example close to the learner context when helpful, otherwise use a universal real-world example
5. real_world_applications = where the topic matters in practice
6. common_misconceptions = misunderstanding, confusion, or misuse case
7. next_step_self_study = the next boundary or deeper question to understand

GUARDRAILS:
1. Do not paraphrase the same definition across sections.
2. Every section must add new knowledge.
3. Do not use filler such as "this is an important concept" or "helps understand better".
4. If a section becomes repetitive, narrow it to a more specific role.
5. Do not answer with a generic field overview when the learner asked one concrete question.
6. Never output citations or URLs inside the explanation.

OUTPUT CONTRACT:
- title: short, direct, not a question
- summary: exactly 4 bullets that orient the learner and answer the main question directly
- key_points: exactly 4 to 5 core theory bullets, short, sharp, and non-overlapping with summary
- summary bullet 1: direct answer to the user's question
- summary bullet 2: scope boundary or what the topic is not
- summary bullet 3: the central mechanism, structure, or comparison axis
- summary bullet 4: why it matters, when it applies, or where people misunderstand it
- key_points bullet 1: core definition
- key_points bullet 2: operating logic or mechanism
- key_points bullet 3: main component, comparison axis, or structure
- key_points bullet 4: application condition, limit, or misuse risk
- key_points bullet 5 when present: memorable misconception or decision value
- topic_tags: 3 to 4 concrete tags
- detailed_sections must contain the 7 section keys above
- core_concept must directly answer the learner's question in the first sentence
- mechanism must explain logic and at least one cause-effect or input-process-output chain
- components_and_relationships must explain structure, criteria, or comparison axes
- if the learner asks about structure or components, components_and_relationships must name the main parts before discussing applications
- common_misconceptions must include at least one misunderstanding or misuse case
- next_step_self_study must point to a deeper boundary, not generic study advice
- never ask the learner to provide more context

JSON SHAPE:
{{
  "title": "string",
  "summary": "- Bullet 1\\n- Bullet 2\\n- Bullet 3\\n- Bullet 4",
  "key_points": ["string", "string", "string", "string"],
  "topic_tags": ["string", "string", "string", "string"],
  "detailed_sections": {{
    "core_concept": {{"title": "Khái niệm cốt lõi", "content": "string"}},
    "mechanism": {{"title": "Bản chất / cơ chế hoạt động", "content": "string"}},
    "components_and_relationships": {{"title": "Các thành phần chính và quan hệ giữa chúng", "content": "string"}},
    "persona_based_example": {{"title": "Ví dụ trực quan", "content": "string"}},
    "real_world_applications": {{"title": "Ứng dụng thực tế", "content": "string"}},
    "common_misconceptions": {{"title": "Nhầm lẫn phổ biến", "content": "string"}},
    "next_step_self_study": {{"title": "Điểm cần nắm tiếp", "content": "string"}}
  }},
  "teaching_adaptation": {{
    "focus_priority": "string",
    "tone": "string",
    "depth_control": "string",
    "example_strategy": "string"
  }}
}}
"""


EXPLORE_TOPIC_REPAIR_PROMPT = """
You are DUO MIND's explore answer rewriter.
A previous draft was too generic, drifted away from the question, or did not answer sharply enough.
Rewrite the answer from scratch using the approved blueprint.
Return ONLY valid JSON.

USER_PROMPT:
\"\"\"
{prompt}
\"\"\"

FOCUS_TOPIC: {focus_topic}
LEARNER_CONTEXT:
{learner_context_json}
EXPLORE_BRIEF:
{explore_brief_json}
VERIFICATION_SOURCES:
{source_brief_json}
CONTENT_BLUEPRINT:
{blueprint_json}
WEAK_DRAFT:
{weak_draft_json}

MISSION:
1. Answer the learner's exact question directly and intelligently.
2. Keep the response narrow, concrete, and theory-strong.
3. Repair drift, filler, repetition, and weak section roles.

QUESTION-FRAME RULES:
- Definition question: define first, then scope boundary, then why people confuse it.
- Structure question: list the main parts first, then explain each part's role and relationship.
- Comparison question: mention both sides immediately and compare on clear axes.
- Mechanism question: explain the operating chain first, not the history or broad context.
- General question: stay with the learner's real goal, not a textbook overview.

GUARDRAILS:
1. Open with the core answer, not with meta commentary.
2. Do not write filler such as "this is important", "helps understand more clearly", or "in many fields".
3. Do not repeat the same definition across summary, key points, and sections.
4. Every section must contribute a distinct knowledge angle.
5. Use LEARNER_CONTEXT only if it improves the example. Never let it hijack the answer.
6. Never output citations or URLs inside the explanation.

OUTPUT CONTRACT:
- title: short, direct, not a question
- summary: exactly 4 bullets
- key_points: exactly 4 to 5 bullets
- summary bullet 1: direct answer to the learner's question
- summary bullet 2: scope boundary or what should not be confused
- summary bullet 3: mechanism, structure, or comparison axis
- summary bullet 4: application, condition, or misconception
- core_concept first sentence must answer the question directly
- components_and_relationships must name the main parts when the learner asks about components or structure
- next_step_self_study must point to a deeper boundary, not generic encouragement

JSON SHAPE:
{{
  "title": "string",
  "summary": "- Bullet 1\\n- Bullet 2\\n- Bullet 3\\n- Bullet 4",
  "key_points": ["string", "string", "string", "string"],
  "topic_tags": ["string", "string", "string"],
  "detailed_sections": {{
    "core_concept": {{"title": "string", "content": "string"}},
    "mechanism": {{"title": "string", "content": "string"}},
    "components_and_relationships": {{"title": "string", "content": "string"}},
    "persona_based_example": {{"title": "string", "content": "string"}},
    "real_world_applications": {{"title": "string", "content": "string"}},
    "common_misconceptions": {{"title": "string", "content": "string"}},
    "next_step_self_study": {{"title": "string", "content": "string"}}
  }},
  "teaching_adaptation": {{
    "focus_priority": "string",
    "tone": "string",
    "depth_control": "string",
    "example_strategy": "string"
  }}
}}
"""


def _json_block(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_analyze_blueprint_prompt(
    *,
    content: str,
    language: str,
    analysis_goal: str,
    focus_topic: str,
    analysis_brief: dict[str, Any],
    source_brief: dict[str, Any],
) -> str:
    return ANALYZE_CONTENT_BLUEPRINT_PROMPT.format(
        content=content,
        language=language,
        analysis_goal=analysis_goal,
        focus_topic=focus_topic,
        analysis_brief_json=_json_block(analysis_brief),
        source_brief_json=_json_block(source_brief),
    )


def build_explore_query_plan_prompt(*, prompt: str) -> str:
    return EXPLORE_QUERY_PLAN_PROMPT.format(prompt=prompt)


def build_analyze_query_plan_prompt(
    *,
    analysis_goal: str,
    focus_topic: str,
    content: str,
) -> str:
    return ANALYZE_QUERY_PLAN_PROMPT.format(
        analysis_goal=analysis_goal,
        focus_topic=focus_topic,
        content=content,
    )


def build_analyze_core_prompt(
    *,
    content: str,
    language: str,
    analysis_goal: str,
    focus_topic: str,
    learner_context: dict[str, Any],
    analysis_brief: dict[str, Any],
    source_brief: dict[str, Any],
    content_blueprint: dict[str, Any],
) -> str:
    return ANALYZE_CONTENT_CORE_PROMPT.format(
        content=content,
        language=language,
        analysis_goal=analysis_goal,
        focus_topic=focus_topic,
        learner_context_json=_json_block(learner_context),
        analysis_brief_json=_json_block(analysis_brief),
        source_brief_json=_json_block(source_brief),
        blueprint_json=_json_block(content_blueprint),
    )


def build_analyze_repair_prompt(
    *,
    content: str,
    language: str,
    analysis_goal: str,
    focus_topic: str,
    learner_context: dict[str, Any],
    analysis_brief: dict[str, Any],
    source_brief: dict[str, Any],
    content_blueprint: dict[str, Any],
    weak_draft: dict[str, Any],
) -> str:
    return ANALYZE_CONTENT_REPAIR_PROMPT.format(
        content=content,
        language=language,
        analysis_goal=analysis_goal,
        focus_topic=focus_topic,
        learner_context_json=_json_block(learner_context),
        analysis_brief_json=_json_block(analysis_brief),
        source_brief_json=_json_block(source_brief),
        blueprint_json=_json_block(content_blueprint),
        weak_draft_json=_json_block(weak_draft),
    )


def build_explore_blueprint_prompt(
    *,
    prompt: str,
    focus_topic: str,
    explore_brief: dict[str, Any],
    source_brief: dict[str, Any],
) -> str:
    return EXPLORE_TOPIC_BLUEPRINT_PROMPT.format(
        prompt=prompt,
        focus_topic=focus_topic,
        explore_brief_json=_json_block(explore_brief),
        source_brief_json=_json_block(source_brief),
    )


def build_explore_core_prompt(
    *,
    prompt: str,
    focus_topic: str,
    learner_context: dict[str, Any],
    explore_brief: dict[str, Any],
    source_brief: dict[str, Any],
    content_blueprint: dict[str, Any],
) -> str:
    return EXPLORE_TOPIC_CORE_PROMPT.format(
        prompt=prompt,
        focus_topic=focus_topic,
        learner_context_json=_json_block(learner_context),
        explore_brief_json=_json_block(explore_brief),
        source_brief_json=_json_block(source_brief),
        blueprint_json=_json_block(content_blueprint),
    )


def build_explore_repair_prompt(
    *,
    prompt: str,
    focus_topic: str,
    learner_context: dict[str, Any],
    explore_brief: dict[str, Any],
    source_brief: dict[str, Any],
    content_blueprint: dict[str, Any],
    weak_draft: dict[str, Any],
) -> str:
    return EXPLORE_TOPIC_REPAIR_PROMPT.format(
        prompt=prompt,
        focus_topic=focus_topic,
        learner_context_json=_json_block(learner_context),
        explore_brief_json=_json_block(explore_brief),
        source_brief_json=_json_block(source_brief),
        blueprint_json=_json_block(content_blueprint),
        weak_draft_json=_json_block(weak_draft),
    )


MINDMAP_CORE_PROMPT = """
You are DUO MIND's learning mind-map generator.
Return ONLY valid JSON.

TOPIC:
{topic}

SUMMARY:
{summary}

KEY POINTS:
{key_points}

DETAIL OUTLINE:
{detail_outline}

RULES:
1. Build one clear root node from the topic.
2. Create 5 to 7 main branches.
3. Every branch must come from SUMMARY, KEY POINTS, or DETAIL OUTLINE. Do not invent generic branches from the topic name alone.
4. Each branch should represent a real knowledge chunk such as concept, mechanism, components, example, application, or misconception.
5. Keep labels short and readable.
6. Write node content in Vietnamese.
7. Avoid branches like "overview", "notes", "other", or "extra".
8. The map must help the learner recall the actual answer, not just the topic name.

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

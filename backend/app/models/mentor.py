from typing import Any, Literal

from pydantic import BaseModel, Field


MentorIntent = Literal[
    "career_roles",
    "market_outlook",
    "skill_gap",
    "learning_roadmap",
    "career_fit",
    "general_guidance",
]

MessageRole = Literal["user", "assistant", "system"]


class MentorThreadCreateRequest(BaseModel):
    title: str | None = None


class MentorMessageRequest(BaseModel):
    thread_id: str | None = None
    message: str = Field(min_length=1)
    language: str = "vi"


class MentorThreadSummary(BaseModel):
    id: str
    title: str
    status: str = "active"
    last_message_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class MentorMessageItem(BaseModel):
    id: str
    thread_id: str
    role: MessageRole
    intent: str | None = None
    content: str
    answer_mode: str | None = None
    response_data: dict[str, Any] | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)
    related_materials: list[dict[str, Any]] = Field(default_factory=list)
    request_payload: dict[str, Any] | None = None
    context_snapshot: dict[str, Any] | None = None
    generation_trace: dict[str, Any] | None = None
    created_at: str | None = None


class MentorThreadDetail(BaseModel):
    thread: MentorThreadSummary
    messages: list[MentorMessageItem] = Field(default_factory=list)


class MentorSuggestedQuestionsResponse(BaseModel):
    questions: list[str] = Field(default_factory=list)


class MentorChatResponse(BaseModel):
    thread_id: str
    thread_title: str
    message_id: str
    intent: MentorIntent
    answer: str
    answer_mode: str | None = None
    career_paths: list[dict[str, Any]] = Field(default_factory=list)
    market_signals: list[dict[str, Any]] = Field(default_factory=list)
    skill_gaps: list[dict[str, Any]] = Field(default_factory=list)
    decision_summary: dict[str, Any] | None = None
    recommended_learning_steps: list[str] = Field(default_factory=list)
    suggested_followups: list[str] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    related_materials: list[dict[str, Any]] = Field(default_factory=list)
    request_payload: dict[str, Any] | None = None
    context_snapshot: dict[str, Any] | None = None
    generation_trace: dict[str, Any] | None = None
    save_metadata: dict[str, Any] | None = None
    messages: list[MentorMessageItem] = Field(default_factory=list)

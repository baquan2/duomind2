from typing import Any

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    content: str
    language: str = "vi"
    analysis_goal: str | None = None


class Correction(BaseModel):
    original: str
    correction: str
    explanation: str


class SourceReference(BaseModel):
    label: str
    url: str
    snippet: str | None = None


class AnalyzeResult(BaseModel):
    session_id: str
    title: str
    verdict: str
    accuracy_score: int | None
    accuracy_assessment: str
    summary: str
    key_points: list[str] = Field(default_factory=list)
    corrections: list[Correction] = Field(default_factory=list)
    knowledge_detail_data: dict[str, Any] = Field(default_factory=dict)
    topic_tags: list[str] = Field(default_factory=list)
    mindmap_data: dict[str, Any] = Field(default_factory=dict)
    sources: list[SourceReference] = Field(default_factory=list)
    source_label: str | None = None
    input_preview: str | None = None


class ExploreRequest(BaseModel):
    prompt: str
    language: str = "vi"


class ExploreResult(BaseModel):
    session_id: str
    title: str
    summary: str
    key_points: list[str] = Field(default_factory=list)
    knowledge_detail_data: dict[str, Any] = Field(default_factory=dict)
    topic_tags: list[str] = Field(default_factory=list)
    mindmap_data: dict[str, Any] = Field(default_factory=dict)
    sources: list[SourceReference] = Field(default_factory=list)

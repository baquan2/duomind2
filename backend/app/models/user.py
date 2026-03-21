from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


AgeRange = Literal["under_18", "18_24", "25_34", "35_44", "45_plus"]
UserStatus = Literal["student", "working", "both", "other"]
EducationLevel = Literal["high_school", "college", "university", "postgrad", "other"]
LearningStyle = Literal["visual", "reading", "practice", "mixed"]


class UserProfile(BaseModel):
    id: str
    email: str | None = None
    full_name: str | None = None
    avatar_url: str | None = None
    is_onboarded: bool = False
    created_at: datetime | None = None


class OnboardingData(BaseModel):
    age_range: AgeRange
    status: UserStatus
    education_level: EducationLevel | None = None
    major: str | None = None
    school_name: str | None = None
    industry: str | None = None
    job_title: str | None = None
    years_experience: int | None = Field(default=None, ge=0)
    target_role: str | None = None
    current_focus: str | None = None
    current_challenges: str | None = None
    desired_outcome: str | None = None
    learning_constraints: str | None = None
    learning_goals: list[str] = Field(default_factory=list)
    topics_of_interest: list[str] = Field(default_factory=list)
    learning_style: LearningStyle = "mixed"
    daily_study_minutes: int = Field(default=30, ge=0, le=1440)


class OnboardingResponse(BaseModel):
    success: bool
    ai_persona: str
    ai_persona_description: str
    ai_recommended_topics: list[str] = Field(default_factory=list)

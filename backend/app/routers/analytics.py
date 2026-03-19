import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.services.gemini_service import gemini
from app.services.supabase_service import SupabaseService
from app.utils.prompts import KNOWLEDGE_ANALYTICS_PROMPT


router = APIRouter()


@router.get("/knowledge-report")
async def get_knowledge_report(
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict[str, Any]:
    svc = SupabaseService(supabase)
    sessions = svc.get_all_sessions_for_analytics(current_user["id"])
    onboarding = svc.get_onboarding(current_user["id"])
    profile = svc.get_profile(current_user["id"])

    attempt_scores = svc.get_quiz_attempt_percentages(current_user["id"])
    avg_score = round(sum(attempt_scores) / len(attempt_scores), 1) if attempt_scores else 0

    sessions_summary = json.dumps(
        [
            {
                "title": session.get("title"),
                "type": session.get("session_type"),
                "tags": session.get("topic_tags", []),
                "date": str(session.get("created_at", ""))[:10],
            }
            for session in sessions[:50]
        ],
        ensure_ascii=False,
    )

    try:
        ai_report = await gemini.generate_json(
            KNOWLEDGE_ANALYTICS_PROMPT.format(
                user_persona=(
                    onboarding.get("ai_persona", "general_learner")
                    if onboarding
                    else "general_learner"
                ),
                member_since=(str(profile.get("created_at", ""))[:10] if profile else ""),
                sessions_summary=sessions_summary,
                total_quizzes=len(attempt_scores),
                avg_quiz_score=avg_score,
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate knowledge report",
        ) from exc

    topics_covered = sorted(
        {
            str(tag).strip()
            for session in sessions
            for tag in (session.get("topic_tags") or [])
            if str(tag).strip()
        }
    )

    svc.save_analytics_report(
        current_user["id"],
        {
            "report_period": "all_time",
            "total_sessions": len(sessions),
            "topics_covered": topics_covered,
            "strongest_topics": ai_report.get("strongest_topics", []),
            "weakest_topics": ai_report.get("weakest_topics", []),
            "ai_summary": ai_report.get("ai_summary"),
            "ai_recommendations": ai_report.get("ai_recommendations", []),
            "learning_pattern": ai_report.get("learning_pattern"),
            "knowledge_depth": ai_report.get("knowledge_depth"),
            "avg_quiz_score": avg_score,
            "total_quizzes": len(attempt_scores),
        },
    )

    return {
        **ai_report,
        "total_sessions": len(sessions),
        "total_quizzes": len(attempt_scores),
    }


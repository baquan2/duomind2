from typing import Any

from supabase import Client


class SupabaseService:
    def __init__(self, client: Client) -> None:
        self.db = client

    @staticmethod
    def _first(data: Any) -> dict[str, Any] | None:
        if isinstance(data, list):
            return data[0] if data else None
        if isinstance(data, dict):
            return data
        return None

    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        try:
            result = (
                self.db.table("profiles")
                .select("*")
                .eq("id", user_id)
                .single()
                .execute()
            )
            return result.data
        except Exception:
            return None

    def update_profile(self, user_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        result = self.db.table("profiles").update(data).eq("id", user_id).execute()
        return self._first(result.data)

    def ensure_profile(
        self,
        user_id: str,
        email: str | None = None,
        full_name: str | None = None,
        avatar_url: str | None = None,
    ) -> dict[str, Any] | None:
        profile = self.get_profile(user_id)
        if profile:
            return profile

        payload = {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "avatar_url": avatar_url,
        }
        result = (
            self.db.table("profiles")
            .upsert(payload, on_conflict="id")
            .execute()
        )
        return self._first(result.data)

    def set_onboarded(self, user_id: str) -> None:
        self.db.table("profiles").update({"is_onboarded": True}).eq("id", user_id).execute()

    def get_onboarding(self, user_id: str) -> dict[str, Any] | None:
        result = (
            self.db.table("user_onboarding")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        return self._first(result.data)

    def upsert_onboarding(self, user_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        payload = {"user_id": user_id, **data}
        result = (
            self.db.table("user_onboarding")
            .upsert(payload, on_conflict="user_id")
            .execute()
        )
        return self._first(result.data)

    def create_session(self, user_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        payload = {"user_id": user_id, **data}
        result = self.db.table("learning_sessions").insert(payload).execute()
        return self._first(result.data)

    def get_sessions(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        result = (
            self.db.table("learning_sessions")
            .select(
                "id,title,session_type,topic_tags,accuracy_score,summary,created_at,is_bookmarked"
            )
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return result.data or []

    def get_session_detail(
        self,
        session_id: str,
        user_id: str,
    ) -> dict[str, Any] | None:
        try:
            result = (
                self.db.table("learning_sessions")
                .select("*")
                .eq("id", session_id)
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            return result.data
        except Exception:
            return None

    def save_quiz_questions(
        self,
        session_id: str,
        user_id: str,
        questions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        payload = [
            {"session_id": session_id, "user_id": user_id, **question}
            for question in questions
        ]
        if not payload:
            return []
        result = self.db.table("quiz_questions").insert(payload).execute()
        return result.data or []

    def get_quiz_questions(self, session_id: str) -> list[dict[str, Any]]:
        result = (
            self.db.table("quiz_questions")
            .select("*")
            .eq("session_id", session_id)
            .order("order_index")
            .execute()
        )
        return result.data or []

    def get_quiz_question(
        self,
        question_id: str,
        user_id: str,
    ) -> dict[str, Any] | None:
        try:
            result = (
                self.db.table("quiz_questions")
                .select("*")
                .eq("id", question_id)
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            return result.data
        except Exception:
            return None

    def save_quiz_attempt(
        self,
        user_id: str,
        session_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        payload = {"user_id": user_id, "session_id": session_id, **data}
        result = self.db.table("quiz_attempts").insert(payload).execute()
        return self._first(result.data)

    def save_open_question_response(
        self,
        user_id: str,
        question_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        payload = {"user_id": user_id, "question_id": question_id, **data}
        result = self.db.table("open_question_responses").insert(payload).execute()
        return self._first(result.data)

    def get_quiz_attempt_percentages(self, user_id: str) -> list[float]:
        result = (
            self.db.table("quiz_attempts")
            .select("percentage")
            .eq("user_id", user_id)
            .execute()
        )
        return [
            float(row["percentage"])
            for row in (result.data or [])
            if row.get("percentage") is not None
        ]

    def get_all_sessions_for_analytics(self, user_id: str) -> list[dict[str, Any]]:
        result = (
            self.db.table("learning_sessions")
            .select("title,session_type,topic_tags,accuracy_score,created_at,summary")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    def save_analytics_report(
        self,
        user_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        payload = {"user_id": user_id, **data}
        result = self.db.table("knowledge_analytics").insert(payload).execute()
        return self._first(result.data)

import re
from typing import Any

import google.generativeai as genai

from app.config import get_settings
from app.utils.helpers import safe_parse_json


class GeminiService:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name
        self._configured_api_key: str | None = None
        self._configured_model_name: str | None = None
        self._text_model: Any | None = None
        self._precise_text_model: Any | None = None
        self._json_model: Any | None = None

    def _configure(self) -> None:
        settings = get_settings()
        api_key = settings.GEMINI_API_KEY
        model_name = self.model_name or settings.GEMINI_MODEL or "gemini-2.5-flash"
        if not api_key:
            raise RuntimeError("Missing required setting: GEMINI_API_KEY")

        if (
            self._configured_api_key == api_key
            and self._configured_model_name == model_name
        ):
            return

        genai.configure(api_key=api_key)
        self._configured_api_key = api_key
        self._configured_model_name = model_name
        self._text_model = None
        self._precise_text_model = None
        self._json_model = None

    def _get_text_model(self) -> Any:
        self._configure()
        if self._text_model is None:
            self._text_model = genai.GenerativeModel(
                model_name=self._configured_model_name,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "max_output_tokens": 12288,
                },
            )
        return self._text_model

    def _get_precise_text_model(self) -> Any:
        self._configure()
        if self._precise_text_model is None:
            self._precise_text_model = genai.GenerativeModel(
                model_name=self._configured_model_name,
                generation_config={
                    "temperature": 0.25,
                    "top_p": 0.8,
                    "max_output_tokens": 8192,
                },
            )
        return self._precise_text_model

    def _get_json_model(self) -> Any:
        self._configure()
        if self._json_model is None:
            self._json_model = genai.GenerativeModel(
                model_name=self._configured_model_name,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_output_tokens": 12288,
                    "response_mime_type": "application/json",
                },
            )
        return self._json_model

    @staticmethod
    def _extract_text(response: Any) -> str:
        text = getattr(response, "text", "")
        if text:
            return text
        raise ValueError("Gemini returned an empty response")

    @staticmethod
    def _clean_json_text(text: str) -> str:
        text = re.sub(r"^```json\s*", "", text.strip())
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    @staticmethod
    def _extract_json_candidate(text: str) -> str:
        cleaned = GeminiService._clean_json_text(text)
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return cleaned[start : end + 1]
        return cleaned

    async def generate_text(self, prompt: str, *, precise: bool = False) -> str:
        model = self._get_precise_text_model() if precise else self._get_text_model()
        response = model.generate_content(prompt)
        return self._extract_text(response)

    async def generate_json(self, prompt: str) -> dict[str, Any]:
        response = self._get_json_model().generate_content(prompt)
        text = self._extract_json_candidate(self._extract_text(response))
        try:
            return safe_parse_json(text)
        except ValueError as exc:
            repair_prompt = (
                "Return only valid JSON for the request below. "
                "Do not include markdown, explanation, or extra text.\n\n"
                f"{prompt}"
            )
            repair_response = self._get_text_model().generate_content(repair_prompt)
            repaired_text = self._extract_json_candidate(self._extract_text(repair_response))
            try:
                return safe_parse_json(repaired_text)
            except ValueError as repair_exc:
                raise ValueError("Gemini returned invalid JSON") from repair_exc


gemini = GeminiService()

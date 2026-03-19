from time import perf_counter

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.models.analysis import AnalyzeRequest, AnalyzeResult, Correction
from app.services.file_parser_service import extract_text_from_upload
from app.services.gemini_service import gemini
from app.services.supabase_service import SupabaseService
from app.utils.fallbacks import build_analyze_fallback, build_basic_mindmap
from app.utils.helpers import (
    build_input_preview,
    build_stored_user_input,
    get_user_context,
    normalize_topic_tags,
    truncate_content,
)
from app.utils.prompts import ANALYZE_CONTENT_PROMPT, MINDMAP_GENERATE_PROMPT


router = APIRouter()


def _normalize_corrections(items: object) -> list[Correction]:
    if not isinstance(items, list):
        return []

    normalized: list[Correction] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized.append(
            Correction(
                original=str(item.get("original") or ""),
                correction=str(item.get("correction") or ""),
                explanation=str(item.get("explanation") or ""),
            )
        )
    return normalized


async def _run_analysis(
    *,
    content: str,
    language: str,
    current_user: dict[str, str | None],
    supabase: Client,
    source_label: str | None = None,
) -> AnalyzeResult:
    svc = SupabaseService(supabase)
    start_time = perf_counter()
    svc.ensure_profile(
        current_user["id"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        avatar_url=current_user.get("avatar_url"),
    )

    onboarding = svc.get_onboarding(current_user["id"])
    prompt_context = get_user_context(onboarding)
    truncated_content = truncate_content(content)

    try:
        ai_result = await gemini.generate_json(
            ANALYZE_CONTENT_PROMPT.format(
                content=truncated_content,
                language=language,
                **prompt_context,
            )
        )
    except Exception as exc:
        print(f"[analyze] Main analysis failed, using fallback: {exc}")
        ai_result = build_analyze_fallback(truncated_content)

    title = str(ai_result.get("title") or "Phan tich noi dung").strip()

    try:
        mindmap_data = await gemini.generate_json(
            MINDMAP_GENERATE_PROMPT.format(content=truncated_content, title=title)
        )
    except Exception as exc:
        print(f"[analyze] Mind map generation failed, using fallback: {exc}")
        mindmap_data = build_basic_mindmap(
            title,
            [
                str(point).strip()
                for point in (ai_result.get("key_points") or [])
                if str(point).strip()
            ],
        )

    accuracy_assessment = str(
        ai_result.get("accuracy_assessment") or "unverifiable"
    ).strip()
    raw_accuracy_score = ai_result.get("accuracy_score")
    accuracy_score: int | None
    if isinstance(raw_accuracy_score, bool):
        accuracy_score = int(raw_accuracy_score)
    elif isinstance(raw_accuracy_score, (int, float)):
        accuracy_score = max(0, min(100, int(raw_accuracy_score)))
    else:
        accuracy_score = None

    if accuracy_assessment == "unverifiable":
        accuracy_score = None

    summary = str(ai_result.get("summary") or "").strip()
    key_points = [
        str(point).strip()
        for point in (ai_result.get("key_points") or [])
        if str(point).strip()
    ]
    corrections = _normalize_corrections(ai_result.get("corrections"))
    topic_tags = normalize_topic_tags(ai_result.get("topic_tags"), title or content)
    effective_source_label = source_label or "Noi dung nhap tay"

    session = svc.create_session(
        current_user["id"],
        {
            "session_type": "analyze",
            "title": title,
            "user_input": build_stored_user_input(content, source_label),
            "topic_tags": topic_tags,
            "accuracy_score": accuracy_score,
            "accuracy_assessment": accuracy_assessment,
            "summary": summary,
            "key_points": key_points,
            "corrections": [item.model_dump() for item in corrections],
            "mindmap_data": mindmap_data,
            "language": language,
            "duration_ms": int((perf_counter() - start_time) * 1000),
        },
    )
    if not session or not session.get("id"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Khong the luu phien phan tich.",
        )

    return AnalyzeResult(
        session_id=session["id"],
        title=title,
        accuracy_score=accuracy_score,
        accuracy_assessment=accuracy_assessment,
        summary=summary,
        key_points=key_points,
        corrections=corrections,
        topic_tags=topic_tags,
        mindmap_data=mindmap_data,
        source_label=effective_source_label,
        input_preview=build_input_preview(content),
    )


@router.post("/", response_model=AnalyzeResult)
async def analyze_content(
    request: AnalyzeRequest,
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> AnalyzeResult:
    return await _run_analysis(
        content=request.content,
        language=request.language,
        current_user=current_user,
        supabase=supabase,
    )


@router.post("/upload", response_model=AnalyzeResult)
async def analyze_uploaded_file(
    file: UploadFile = File(...),
    language: str = Form("vi"),
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> AnalyzeResult:
    content, filename = await extract_text_from_upload(file)

    return await _run_analysis(
        content=content,
        language=language,
        current_user=current_user,
        supabase=supabase,
        source_label=filename,
    )

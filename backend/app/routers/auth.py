from fastapi import APIRouter, Depends
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.services.supabase_service import SupabaseService


router = APIRouter()


@router.get("/me")
async def get_me(
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    svc = SupabaseService(supabase)
    profile = svc.ensure_profile(
        current_user["id"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        avatar_url=current_user.get("avatar_url"),
    )
    if profile:
        return profile

    return {
        "id": current_user["id"],
        "email": current_user.get("email"),
        "is_onboarded": False,
    }


@router.get("/onboarding-status")
async def onboarding_status(
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict[str, bool]:
    svc = SupabaseService(supabase)
    profile = svc.ensure_profile(
        current_user["id"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        avatar_url=current_user.get("avatar_url"),
    )
    return {"is_onboarded": bool(profile and profile.get("is_onboarded", False))}

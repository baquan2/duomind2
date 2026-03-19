from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

from app.config import Settings, get_settings


security = HTTPBearer(auto_error=False)


def get_settings_dependency() -> Settings:
    return get_settings()


SettingsDep = Annotated[Settings, Depends(get_settings_dependency)]


def _require_setting(value: str, name: str) -> str:
    if value:
        return value
    raise RuntimeError(f"Missing required setting: {name}")


@lru_cache
def get_supabase() -> Client:
    settings = get_settings()
    return create_client(
        _require_setting(settings.SUPABASE_URL, "SUPABASE_URL"),
        _require_setting(
            settings.SUPABASE_SERVICE_ROLE_KEY,
            "SUPABASE_SERVICE_ROLE_KEY",
        ),
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    supabase: Client = Depends(get_supabase),
) -> dict[str, str | None]:
    """Verify a Supabase JWT and return a minimal user payload."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
        )

    token = credentials.credentials
    try:
        response = supabase.auth.get_user(token)
        user = response.user
    except Exception as exc:  # pragma: no cover - depends on Supabase runtime
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    metadata = user.user_metadata or {}
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": metadata.get("full_name"),
        "avatar_url": metadata.get("avatar_url"),
    }


CurrentUserDep = Annotated[dict[str, str | None], Depends(get_current_user)]

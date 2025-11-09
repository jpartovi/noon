from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _get_env(key: str) -> Optional[str]:
    value = os.getenv(key)
    if value is None:
        return None
    value = value.strip()
    return value or None


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_service_role_key: str
    google_client_id: str
    google_client_secret: str
    google_oauth_redirect_uri: str
    google_oauth_scopes: tuple[str, ...]
    google_oauth_app_redirect_uri: str
    supabase_anon_key: Optional[str] = None
    supabase_jwt_secret: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    url = _get_env("SUPABASE_URL")
    service_key = _get_env("SUPABASE_SERVICE_ROLE_KEY")
    google_client_id = _get_env("GOOGLE_CLIENT_ID")
    google_client_secret = _get_env("GOOGLE_CLIENT_SECRET")
    google_redirect_uri = _get_env("GOOGLE_OAUTH_REDIRECT_URI")
    app_redirect_uri = _get_env("GOOGLE_OAUTH_APP_REDIRECT_URI")
    scopes_raw = _get_env("GOOGLE_OAUTH_SCOPES")

    missing: list[str] = []
    if not url:
        missing.append("SUPABASE_URL")
    if not service_key:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")
    if not google_client_id:
        missing.append("GOOGLE_CLIENT_ID")
    if not google_client_secret:
        missing.append("GOOGLE_CLIENT_SECRET")
    if not google_redirect_uri:
        missing.append("GOOGLE_OAUTH_REDIRECT_URI")
    if not app_redirect_uri:
        missing.append("GOOGLE_OAUTH_APP_REDIRECT_URI")

    if missing:
        raise RuntimeError(
            "Missing required Supabase configuration: "
            + ", ".join(missing)
            + ". Set them in your environment or .env file."
        )

    scopes: tuple[str, ...]
    if scopes_raw:
        scopes = tuple(scope for scope in scopes_raw.split() if scope)
    else:
        scopes = (
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/calendar.events.readonly",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "openid",
        )

    return Settings(
        supabase_url=url,
        supabase_service_role_key=service_key,
        supabase_anon_key=_get_env("SUPABASE_ANON_KEY"),
        supabase_jwt_secret=_get_env("SUPABASE_JWT_SECRET"),
        google_client_id=google_client_id,
        google_client_secret=google_client_secret,
        google_oauth_redirect_uri=google_redirect_uri,
        google_oauth_scopes=scopes,
        google_oauth_app_redirect_uri=app_redirect_uri,
    )

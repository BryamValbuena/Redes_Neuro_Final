"""Cliente Supabase singleton para el backend."""
from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from backend.app.config import SUPABASE_KEY, SUPABASE_URL

if TYPE_CHECKING:
    from supabase import Client


class SupabaseNotConfiguredError(RuntimeError):
    """Supabase URL o service key no configurados."""


def is_supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


@lru_cache(maxsize=1)
def get_supabase() -> "Client":
    if not is_supabase_configured():
        raise SupabaseNotConfiguredError(
            "Configura SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en las variables de entorno."
        )
    from supabase import create_client

    return create_client(SUPABASE_URL, SUPABASE_KEY)

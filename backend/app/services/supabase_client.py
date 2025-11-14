# backend/app/services/supabase_client.py
from functools import lru_cache
from supabase import create_client, Client
from ..core.config import settings

@lru_cache  # cache one instance for the process
def service_client() -> Client:
    """
    Service-role client (bypasses RLS).
    Use ONLY for trusted jobs: migrations, admin tasks, system cron, signed URL generation, etc.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

def client_for_user(access_token: str) -> Client:
    """
    User-scoped client so RLS applies. Call this in request handlers where you act on behalf of the user.
    """
    c = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

    # supabase-py commonly exposes postgrest.auth(token) to set the Authorization header
    # for all PostgREST calls. If your version differs, adapt to its documented method.
    try:
        c.postgrest.auth(access_token)
    except Exception:
        # Fallback for older versions that accept global headers at init
        c = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY,
            options={"global": {"headers": {"Authorization": f"Bearer {access_token}"}}}
        )
    return c


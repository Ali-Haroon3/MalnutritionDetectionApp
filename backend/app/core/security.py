from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt  # PyJWT
from ..core.config import settings

auth_scheme = HTTPBearer(auto_error=False)

class TokenPayload:
    def __init__(self, sub: str | None, email: str | None, raw: dict, access_token: str):
        self.sub = sub
        self.email = email
        self.raw = raw
        self.access_token = access_token

def verify_supabase_jwt(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience=settings.SUPABASE_JWT_AUDIENCE,
            options={"require": ["exp", "iss", "aud"]},
        )
        iss = payload.get("iss", "")
        if settings.SUPABASE_URL not in iss:
            raise jwt.InvalidIssuerError("Invalid token issuer")
        return TokenPayload(sub=payload.get("sub"), email=payload.get("email"), raw=payload, access_token=token)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid auth token: {e}")

def get_current_user(creds: Annotated[HTTPAuthorizationCredentials | None, Depends(auth_scheme)]) -> TokenPayload:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")
    return verify_supabase_jwt(creds.credentials)

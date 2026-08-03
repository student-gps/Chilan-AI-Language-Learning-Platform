from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database.utils import decode_access_token_subject


_bearer_scheme = HTTPBearer(auto_error=False)


def require_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decode_access_token_subject(credentials.credentials)
    try:
        UUID(str(user_id))
    except (TypeError, ValueError):
        user_id = None

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


def require_matching_user_id(request_user_id: str | None, current_user_id: str) -> None:
    if request_user_id is not None and request_user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Cannot access another user's data")

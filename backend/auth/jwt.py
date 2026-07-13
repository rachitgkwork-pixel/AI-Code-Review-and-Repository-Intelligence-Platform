from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from backend.config import get_settings
from backend.schemas.auth import TokenData

settings = get_settings()


def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        user_id: str = payload.get("sub")
        role: str = payload.get("role", "user")
        if not user_id:
            raise ValueError("Invalid token payload")
        return TokenData(user_id=user_id, role=role)
    except JWTError as exc:
        raise ValueError("Could not validate token") from exc

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from backend.app.config import (
    AUTH_PASSWORD,
    AUTH_USERNAME,
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    JWT_SECRET,
)

security = HTTPBearer(auto_error=False)


def verify_credentials(username: str, password: str) -> bool:
    return username == AUTH_USERNAME and password == AUTH_PASSWORD


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str | None = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token inválido")
        return username
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido o expirado") from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)

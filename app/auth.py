from jose import jwt, JWTError

from app.config import ALGORITHM, SECRET_KEY


def get_username_from_token(token: str) -> str | None:
    if not SECRET_KEY or not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
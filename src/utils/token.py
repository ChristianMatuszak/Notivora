import jwt
from datetime import datetime, timedelta, UTC

SECRET_KEY = "dein_geheimer_schluessel"
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 30

def generate_reset_token(user_id: int) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=EXPIRATION_MINUTES)
    payload = {"user_id": user_id, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_reset_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

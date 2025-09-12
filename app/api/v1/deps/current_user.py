"""Dependency to extract current user from JWT in httpOnly cookie."""
from fastapi import Cookie, Depends, HTTPException, status, Request
from jose import jwt, JWTError
from app.config.settings import settings

def get_jwt_token_from_cookie(request: Request):
    token = request.cookies.get(settings.token_cookie_name)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return token

async def get_current_user(token: str = Depends(get_jwt_token_from_cookie)):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user = payload.get("user")
        if not user or not user.get("id"):
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
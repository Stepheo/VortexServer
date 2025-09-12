"""Telegram Web App authentication endpoint.

This endpoint verifies Telegram Web App `initData` using the bot token,
creates a short-lived JWT and sets it as an httpOnly cookie.
"""

import hashlib
import hmac
import time
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from jose import jwt

from app.config.settings import settings
from app.core.cache import cache_manager

router = APIRouter(prefix="/auth", tags=["auth"])


class InitDataModel(BaseModel):
    init_data: str


def parse_init_data(init_data: str) -> Dict[str, str]:
    """Parse Telegram initData string into dict.

    Telegram usually sends initData as 'k1=v1\nk2=v2' or a similar string.
    If the client sends a JSON object string, adapt accordingly on the client.
    """
    result: Dict[str, str] = {}
    for line in init_data.split('\n'):
        if not line:
            continue
        if '=' not in line:
            continue
        k, v = line.split('=', 1)
        result[k] = v
    return result


def verify_telegram_init_data(init_data: str, bot_token: str, max_age: int = 86400) -> Dict[str, str]:
    data = parse_init_data(init_data)
    if 'hash' not in data or 'auth_date' not in data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid init_data')

    received_hash = data.pop('hash')

    # Build data_check_string
    pairs = [f"{k}={v}" for k, v in sorted(data.items())]
    data_check_string = '\n'.join(pairs)

    # secret_key is SHA256 of bot_token
    secret_key = hashlib.sha256(bot_token.encode()).digest()

    calc_hmac = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calc_hmac, received_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid signature')

    # Check timestamp freshness
    try:
        auth_date = int(data.get('auth_date', '0'))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid auth_date')

    if int(time.time()) - auth_date > max_age:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='init_data expired')

    return data


RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 10     # max attempts per IP per window
REPLAY_WINDOW = 3600    # seconds to remember used auth_date+user combos


async def rate_limit(ip: str):
    if not ip:
        return
    key = f"rl:auth:{ip}"
    current = await cache_manager.get(key)
    if current is None:
        await cache_manager.set(key, 1, expire=RATE_LIMIT_WINDOW)
        return
    try:
        current_int = int(current)
    except ValueError:
        current_int = 0
    if current_int >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Too many auth attempts, slow down")
    await cache_manager.set(key, current_int + 1, expire=RATE_LIMIT_WINDOW)


async def check_replay(user_id: str, auth_date: str, signature: str):
    # Use combination of user_id + auth_date + signature hash to detect reuse
    if not user_id or not auth_date or not signature:
        return
    key = f"replay:tg:{user_id}:{auth_date}:{signature[:16]}"
    exists = await cache_manager.exists(key)
    if exists:
        raise HTTPException(status_code=401, detail="Replay detected")
    await cache_manager.set(key, 1, expire=REPLAY_WINDOW)


@router.post('/telegram')
async def auth_telegram(init: InitDataModel, request: Request, response: Response):
    """Verify Telegram initData and issue an httpOnly cookie with JWT.

    Request body: { init_data: string }
    Response: sets cookie, returns basic user info.
    """
    bot_token = settings.bot_token
    if not bot_token:
        raise HTTPException(status_code=500, detail='Bot token not configured')

    client_ip = request.client.host if request.client else "unknown"

    # Rate limit per IP
    await rate_limit(client_ip)

    data = verify_telegram_init_data(init.init_data, bot_token)

    # Replay protection (use provided signature+auth_date)
    await check_replay(
        user_id=data.get('user_id') or data.get('id') or data.get('user', ''),
        auth_date=data.get('auth_date', ''),
        signature=init.init_data.split('\n')[-1].split('=')[1] if 'hash=' in init.init_data else ''
    )

    # Create JWT payload (include minimal claims)
    user = {
        'id': data.get('user_id') or data.get('id') or data.get('user', ''),
        'username': data.get('username') or data.get('user', ''),
    }

    now = int(time.time())
    expires = now + settings.access_token_expire_minutes * 60

    payload = {
        'sub': str(user.get('id')),
        'user': user,
        'iat': now,
        'exp': expires,
    }

    token = jwt.encode(payload, settings.secret_key, algorithm='HS256')

    # Set cookie
    response.set_cookie(
        key=settings.token_cookie_name,
        value=token,
        httponly=settings.token_cookie_httponly,
        secure=settings.token_cookie_secure,
        samesite=settings.token_cookie_samesite,
        expires=expires,
        path='/'
    )

    return {'message': 'authenticated', 'user': user}

from fastapi import Request, HTTPException
from aiogram.utils.web_app import WebAppInitData, safe_parse_webapp_init_data

from app.config.settings import settings

def auth(request: Request) -> WebAppInitData:
    try:
        auth_string = request.headers.get("initData", None)
        if auth_string:
            data = safe_parse_webapp_init_data(
                settings.bot_token,
                auth_string
            )
    except Exception:
        raise HTTPException(401, {"error": "Unauthorized"})
    
    
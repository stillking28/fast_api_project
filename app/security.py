import os
from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "My-API-Key"
api_key_header_scheme = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def get_api_key(api_key_header: str = Security(api_key_header_scheme)):
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ключ API не настроен на сервере",
        )
    if not api_key_header or api_key_header != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверный или просроченный API ключ",
        )
    return api_key_header

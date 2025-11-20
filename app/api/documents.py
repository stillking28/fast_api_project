from fastapi import APIRouter, Depends, status, HTTPException
from .. import repository
from ..schemas import (
    AsyncDocumentRequest,
    TaskAccepted,
)
from ..security import get_api_key
import uuid
import json
import redis
import os

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True,
)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
    dependencies=[Depends(get_api_key)],
)


@router.post(
    "/generate/async", status_code=status.HTTP_202_ACCEPTED, response_model=TaskAccepted
)
def generate_document_async(req: AsyncDocumentRequest):
    user = repository.get_user_by_id(req.user_id)
    request_id = uuid.uuid4()

    redis_key = f"{request_id}_{req.content_type}"
    redis_value = {"user_data": user.model_dump(), "callback_url": req.callback_url}

    try:
        redis_client.set(redis_key, json.dumps(redis_value))
        repository.log_generation_request(
            request_id=request_id,
            user_id=user.id,
            doc_type=req.content_type,
            request_body=json.dumps(redis_value),
        )
    except redis.exceptions.ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Сервер Redis недоступен: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {e}")

    return {"message": f"Задача {request_id} принята в обработку"}

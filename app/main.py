import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .api import api_router
from .exceptions import UserNotFoundError, UserAlreadyExistsError
from . import repository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()


@app.on_event("startup")
def on_startup():
    logger.info("Приложение запускается")
    try:
        repository.create_table_if_not_exists()
        logger.info("Таблица пользователей готова к использованию")
    except Exception as e:
        logger.error(
            f"Ошибка: не удалось подключиться или создать таблицу в ClickHouse: {e}"
        )


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"message": f"Пользователь с ID {exc.user_id} не найден"},
    )


@app.exception_handler(UserAlreadyExistsError)
async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsError):
    return JSONResponse(status_code=400, content={"message": exc.detail})


app.include_router(api_router)


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Ping pong"}

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .api import api_router
from .exceptions import UserNotFoundError, UserAlreadyExistsError
from . import repository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Приложение запускается")

    try:
        repository.create_table_if_not_exists()
        logger.info("Таблица 'users' в ClickHouse готова")
    except Exception as e:
        logger.error(f"Не удалось подключиться или создать таблицу в ClickHouse: {e}")
    yield
    logger.info("Приложение останавливается")


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

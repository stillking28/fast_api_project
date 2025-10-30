from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from . import api
from .exceptions import UserNotFoundError, UserAlreadyExistsError

app = FastAPI()
app.include_router(api.user_router)
app.include_router(api.doc_router)


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"message": "Пользователь с указанным ID не найден."},
    )


@app.exception_handler(UserAlreadyExistsError)
async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsError):
    return JSONResponse(
        status_code=400,
        content={"message": exc.detail},
    )


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Ping pong"}

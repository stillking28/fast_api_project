from fastapi import FastAPI
from . import api
from .schemas import Message

app = FastAPI()
app.include_router(api.router)


@app.get("/", tags=["Root"], response_model=Message)
def read_root():
    return Message(message="Ping pong")

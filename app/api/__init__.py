from fastapi import APIRouter
from . import users, documents

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(documents.router) 
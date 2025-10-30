from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from . import repository, services
from .schemas import (
    User, UserCreate, DocumentRequest,
    AsyncDocumentRequest, DocumentResponse
)
from .security import get_api_key

user_router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_api_key)],
)


@user_router.post("/", response_model = User, status_code = status.HTTP_201_CREATED)
def create_user_(user: UserCreate):
    return repository.create_user(user)


@user_router.get("/", response_model = List[User])
def read_users_(skip : int = 0, limit : int = Query(10, le=100)):
    return repository.get_all_users(skip=skip, limit=limit)


@user_router.get("/{user_id}", response_model = User)
def read_user_(user_id: str):
    return repository.get_user_by_id(user_id)


@user_router.put("/{user_id}", response_model = User)
def update_user_(user_id: str, user_update: UserCreate):
    return repository.update_user(user_id, user_update)

@user_router.delete("/{user_id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_user_(user_id: str):
    repository.delete_user(user_id)
    return None


@user_router.get("/search/", response_model = List[User])
def search_users_(q: str = "", skip: int = 0, limit : int = Query(10, le=100)):
    return repository.search_users(q, skip=skip, limit=limit)


doc_router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
    dependencies=[Depends(get_api_key)],
)


@doc_router.post("/generate/sync", response_model = DocumentResponse)
def generate_document_sync(req: DocumentRequest):
    user = repository.get_user_by_id(req.user_id)
    link = services.generate_fake_document(user, req.content_type)
    return DocumentResponse(
        message="Документ успешно сгенерирован",
        document_url=link
    )


@doc_router.post("/generate/async", status_code = status.HTTP_202_ACCEPTED)
def generate_document_async(req: AsyncDocumentRequest, tasks: BackgroundTasks):
    tasks.add_task(
        services.generate_and_send_callback,
        req.user_id,
        req.content_type,
        req.callback_url
    )
    return {"message": "Запрос на генерацию документа принят в обработку"}
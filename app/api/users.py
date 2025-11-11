from typing import List
from fastapi import APIRouter, Depends, status, Query
from .. import repository
from ..schemas import User, UserCreate
from ..security import get_api_key

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_api_key)],
)


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user_(user: UserCreate):
    return repository.create_user(user)


@router.get("/", response_model=List[User])
def read_users(skip: int = 0, limit: int = Query(default=10, le=100)):
    users = repository.get_all_users(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=User)
def read_user(user_id: str):
    return repository.get_user_by_id(user_id)


@router.put("/{user_id}", response_model=User)
def update_user_(user_id: str, user: UserCreate):
    return repository.update_user(user_id=user_id, user_update=user)


@router.get("/search/", response_model=List[User])
def search_users_(q: str = "", skip: int = 0, limit: int = Query(default=10, le=100)):
    users = repository.search_users(q=q, skip=skip, limit=limit)
    return users


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_(user_id: str):
    repository.delete_user(user_id=user_id)
    return None

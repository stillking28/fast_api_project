from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from . import repository
from .schemas import User, UserCreate
from .security import get_api_key

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_api_key)],
)


@router.post("/", response_model = User, status_code = status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    db = repository.load_db()
    for u in db.values():
        if u.iin == user.iin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким ИИН уже существует")
        elif u.phone_number == user.phone_number:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким номером телефона уже существует")
    user_id = repository.get_next_id(db)
    new_user = User(id=user_id, **user.model_dump())
    db[user_id] = new_user
    repository.save_db(db)
    return new_user


@router.get("/", response_model = List[User])
def read_users():
    db = repository.load_db()
    return list(db.values())


@router.get("/{user_id}", response_model = User)
def read_user(user_id: str):
    db = repository.load_db()
    user = db.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user


@router.put("/{user_id}", response_model = User)
def update_user(user_id: str, user_update: UserCreate):
    db = repository.load_db()
    if user_id not in db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    updated_user = User(id=user_id, **user_update.model_dump())
    db[user_id] = updated_user
    repository.save_db(db)
    return updated_user


@router.delete("/{user_id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str):
    db = repository.load_db()
    if user_id not in db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    del db[user_id]
    repository.save_db(db)
    return None


@router.get("/search/", response_model = List[User])
def search_users(q: str):
    db = repository.load_db()
    query = q.lower()
    result = []
    for user in db.values():
        if (query in user.first_name.lower() or
            query in user.last_name.lower() or
            query in user.iin or
            query in user.phone_number):
            result.append(user)
    return result

import json
import os
from typing import List, Dict

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

DB_FILE = "db.json"

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "My-API-Key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

class UserBase(BaseModel):
    first_name: str = Field(..., description="Имя пользователя")
    last_name: str = Field(..., description="Фамилия пользователя")

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: str = Field(..., description="Уникальный идентификатор пользователя")
def load_db() -> Dict[str, User]:
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {user_id: User(**user_data) for user_id, user_data in data.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_db(db: Dict[str, User]):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json_data = {user_id: user.model_dump() for user_id, user in db.items()}
        json.dump(json_data, f, indent=4, ensure_ascii=False)


async def get_api_key(api_key_from_header: str = Depends(api_key_header)):
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ключ API не настроен на сервере"
        )
    if api_key_from_header != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверный или просроченный API ключ"
        )
    return api_key_from_header


@app.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(user: UserCreate, api_key: str = Depends(get_api_key)):
    db = load_db()
    
    if db:
        max_id = max(int(k) for k in db.keys())
        new_id = max_id + 1
    else:
        new_id = 1
    
    user_id = str(new_id)
    new_user = User(id=user_id, **user.model_dump())
    db[user_id] = new_user
    save_db(db)
    return new_user


@app.get("/users/", response_model=List[User], tags=["Users"])
def read_users(api_key: str = Depends(get_api_key)):
    db = load_db()
    return list(db.values())


@app.get("/users/{user_id}", response_model=User, tags=["Users"])
def read_user(user_id: str, api_key: str = Depends(get_api_key)):
    db = load_db()
    user = db.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user


@app.put("/users/{user_id}", response_model=User, tags=["Users"])
def update_user(user_id: str, user_update: UserCreate, api_key: str = Depends(get_api_key)):
    db = load_db()
    if user_id not in db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    updated_user = User(id=user_id, **user_update.model_dump())
    db[user_id] = updated_user
    save_db(db)
    return updated_user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
def delete_user(user_id: str, api_key: str = Depends(get_api_key)):
    db = load_db()
    if user_id not in db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    del db[user_id]
    save_db(db)
    return None

@app.get("/", tags=["Root"])
def root():
    return {"message": "Ping Pong"}
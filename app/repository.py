import json
from typing import Dict, List
from .schemas import User, UserCreate
from .exceptions import UserNotFoundError, UserAlreadyExistsError

DB_FILE = 'db.json'


def _load_db() -> Dict[str, Dict]:
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {user_id: User(**user_data) for user_id, user_data in data.items()}
    except (FileNotFoundError,json.JSONDecodeError):
        return {}


def _save_db(db: Dict[str, User]):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json_data = {user_id: user.model_dump() for user_id, user in db.items()}
        json.dump(json_data, f, indent=4, ensure_ascii=False)


def _get_next_id(db: Dict[str, User]) -> str:
    if db:
        max_id = max(int(k) for k in db.keys())
        return str(max_id + 1)
    return '1'


def get_user_by_id(user_id: str) -> User:
    db = _load_db()
    user = db.get(user_id)
    if user is None:
        raise UserNotFoundError(user_id=user_id)
    return user


def create_user(user_create: UserCreate) -> User:
    db = _load_db()
    for u in db.values():
        if u.iin == user_create.iin:
            raise UserAlreadyExistsError(f"Пользователь с таким ИИН уже существует.")
        if u.phone_number == user_create.phone_number:
            raise UserAlreadyExistsError(f"Пользователь с таким номером телефона уже существует.")
    new_id = _get_next_id(db)
    new_user = User(id=new_id, **user_create.model_dump())
    db[new_id] = new_user
    _save_db(db)
    return new_user


def get_all_users(skip: int = 0, limit: int = 10) -> List[User]:
    db = _load_db()
    users_list = list(db.values())
    return users_list[skip: skip + limit]


def search_users(q: str, skip: int = 0, limit: int = 10) -> List[User]:
    if not q:
        return get_all_users(skip, limit)
    db = _load_db()
    query = q.lower()
    results =[]
    for user in db.values():
        if (query in user.first_name.lower() or
            query in user.last_name.lower() or
            query in user.iin or
            query in user.phone_number):
            results.append(user)
    return results[skip: skip + limit]


def update_user(user_id: str, user_update: UserCreate) -> User:
    db = _load_db()
    if user_id not in db:
        raise UserNotFoundError(user_id = user_id)  
    updated_user = User(id=user_id, **user_update.model_dump())
    db[user_id] = updated_user
    _save_db(db)
    return updated_user


def delete_user(user_id: str):
    db = _load_db()
    if user_id not in db:
        raise UserNotFoundError(user_id = user_id)  
    del db[user_id]
    _save_db(db)

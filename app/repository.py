import json
from typing import Dict
from .schemas import User, UserCreate

DB_FILE = 'db.json'
def load_db() -> Dict[str, Dict]:
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {user_id: User(**user_data) for user_id, user_data in data.items()}
    except (FileNotFoundError,json.JSONDecodeError):
        return {}


def save_db(db: Dict[str, User]):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json_data = {user_id: user.model_dump() for user_id, user in db.items()}
        json.dump(json_data, f, indent=4, ensure_ascii=False)


def get_next_id(db: Dict[str, User]) -> str:
    if db:
        max_id = max(int(k) for k in db.keys())
        return str(max_id + 1)
    else:
        return '1'

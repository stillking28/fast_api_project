import os
import logging
from typing import List
import clickhouse_connect
from clickhouse_connect.driver.client import Client
from .schemas import User, UserCreate
from .exceptions import UserNotFoundError, UserAlreadyExistsError

logger = logging.getLogger(__name__)


def get_clickhouse_client() -> Client:
    try:
        client = clickhouse_connect.get_client(
            host=os.getenv("CLICKHOUSE_HOST", "localhost"),
            port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
            user=os.getenv("CLICKHOUSE_USER", "default"),
            password=os.getenv("CLICKHOUSE_PASSWORD", ""),
        )
        client.ping()
        return client
    except Exception as e:
        logger.error(f"Ошибка подключения к ClickHouse: {e}")
        raise


def create_table_if_not_exists():
    client = get_clickhouse_client()
    client.command(
        """
        CREATE TABLE IF NOT EXISTS users(
            id String,
            last_name String,
            first_name String,
            middle_name Nullable(String),
            phone_number String,
            iin String,
            photo_url Nullable(String)
        ) ENGINE = MergeTree()
        ORDER BY id
    """
    )


def get_user_by_id(user_id: str) -> User:
    client = get_clickhouse_client()
    result = client.query(
        "SELECT * FROM users WHERE id = %(id)s", parameters={"id": user_id}
    )
    if not result.result_rows:
        raise UserNotFoundError(user_id=user_id)
    user_dict = result.row.dict(0)
    return User(**user_dict)


def create_user(user_create: UserCreate) -> User:
    client = get_clickhouse_client()
    check_q = client.query(
        "SELECT 1 FROM users where iin = %(iin)s OR phone_number = %(phone)s LIMIT 1",
        parameters={"iin": user_create.iin, "phone": user_create.phone_number},
    )
    if check_q.result_rows:
        raise UserAlreadyExistsError(
            detail="Пользователь с таким ИИН или телефоном уже существует"
        )
    all_users = client.query("SELECT id from users")
    if not all_users.result_rows:
        new_id = 1
    else:
        max_id = max(int(row[0]) for row in all_users.result_rows)
        new_id = max_id + 1
    new_id_str = str(new_id)
    new_user = User(id=new_id_str, **user_create.model_dump())
    user_tuple = (
        new_user.id,
        new_user.last_name,
        new_user.first_name,
        new_user.middle_name,
        new_user.phone_number,
        new_user.iin,
        new_user.photo_url,
    )
    client.insert("users", [user_tuple])
    return new_user


def get_all_users(skip: int = 0, limit: int = 10) -> List[User]:
    client = get_clickhouse_client()
    query = "SELECT * FROM users ORDER BY id LIMIT %(limit)s OFFSET %(skip)s"
    result = client.query(query, parameters={"limit": limit, "skip": skip})
    column_names = result.column_names
    return [User(**dict(zip(column_names, row))) for row in result.result_rows]


def search_users(q: str, skip: int = 0, limit: int = 10) -> List[User]:
    if not q:
        return get_all_users(skip=skip, limit=limit)
    client = get_clickhouse_client()
    query = """
        SELECT * FROM users
        WHERE multiSearchAny(
            (last_name, first_name, iin, phone_number),
            [%(q)s]
        )
        ORDER BY id
        LIMIT %(limit)s OFFSET %(skip)s
    """
    result = client.query(query, parameters={"q": q, "limit": limit, "skip": skip})
    column_names = result.column_names
    return [User(**dict(zip(column_names, row))) for row in result.result_rows]


def update_user(user_id: str, user_update: UserCreate) -> User:
    client = get_clickhouse_client()
    get_user_by_id(user_id)
    update_data = user_update.model_dump()
    set_clauses = [f"{key} = %(key)s" for key in update_data.keys()]
    query = f"""
        ALTER TABLE users
        UPDATE {', '.join(set_clauses)}
        WHERE id = %(id)s
    """
    update_data["id"] = user_id
    client.command(query, parameters=update_data)

    return User(id=user_id, **user_update.model_dump())

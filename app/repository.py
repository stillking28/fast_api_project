import os
import logging
import uuid
from typing import List
import clickhouse_connect
from clickhouse_connect.driver.client import Client
from .schemas import User, UserCreate, UserUpdate
from .exceptions import UserNotFoundError, UserAlreadyExistsError
from datetime import datetime

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
    client.command(
        """
        CREATE TABLE IF NOT EXISTS generation_logs(
            request_id String,
            user_id String,
            doc_type String,
            status String,
            request_time DateTime,
            duration_ms Nullable(Int32),
            request_body String,
            result_url Nullable(String)
        )ENGINE = MergeTree()
        ORDER BY request_time
    """
    )


def get_user_by_id(user_id: str) -> User:
    client = get_clickhouse_client()
    result = client.query(
        "SELECT * FROM users WHERE id = %(id)s", parameters={"id": user_id}
    )
    if not result.result_rows:
        raise UserNotFoundError(user_id=user_id)
    row = result.result_rows[0]
    column_names = result.column_names
    user_dict = dict(zip(column_names, row))
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
        WHERE
            (first_name ILIKE %(q_like)s) OR
            (last_name ILIKE %(q_like)s) OR
            (iin ILIKE %(q_like)s) OR
            (phone_number ILIKE %(q_like)s)
        ORDER BY id
        LIMIT %(limit)s OFFSET %(skip)s
    """
    params = {"q_like": q, "limit": limit, "skip": skip}

    query = query.replace("%(q_like)s", "concat('%%', %(q_like)s, '%%')")
    result = client.query(query, parameters=params)
    column_names = result.column_names
    return [User(**dict(zip(column_names, row))) for row in result.result_rows]


def update_user(user_id: str, user_update: UserUpdate) -> User:
    client = get_clickhouse_client()
    current_user = get_user_by_id(user_id)
    update_data = user_update.model_dump(exclude_unset=True)
    if not update_data:
        return current_user
    if "iin" in update_data or "phone_number" in update_data:
        check_q = client.query(
            "SELECT 1 FROM users"
            "WHERE (iin = %(iin)s OR phone_number = %(phone)s) AND id != %(id)s"
            "LIMIT 1",
            parameters={
                "iin": update_data.get("iin", current_user.iin),
                "phone": update_data.get("phone_number", current_user.phone_number),
                "id": user_id,
            },
        )
        if check_q.result_rows:
            raise UserAlreadyExistsError(
                detail="Пользователь с таким ИИН или телефоном уже существует"
            )

    set_clauses = [f"{key} = %({key})s" for key in update_data.keys()]
    query = f"""
        ALTER TABLE users
        UPDATE {', '.join(set_clauses)}
        WHERE id  = %(id)s
    """
    update_data["id"] = user_id
    client.command(query, parameters=update_data)

    updated_user = current_user.model_copy(update=update_data)

    return updated_user


def delete_user(user_id: str):
    client = get_clickhouse_client()
    get_user_by_id(user_id)
    query = "ALTER TABLE users DELETE WHERE id=%(id)s"
    client.command(query, parameters={"id": user_id})


def log_generation_request(
    request_id: uuid.UUID, user_id: str, doc_type: str, request_body: str
):
    client = get_clickhouse_client()
    log_entry = {
        "request_id": str(request_id),
        "user_id": user_id,
        "doc_type": doc_type,
        "status": "PENDING",
        "request_time": datetime.now(),
        "duration_ms": None,
        "request_body": request_body,
        "result_url": None,
    }
    client.insert("generation_logs", [list(log_entry.values())])

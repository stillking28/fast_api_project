import os
import time
import json
import uuid
import asyncio
import logging
import redis
import clickhouse_connect
from datetime import datetime
from core import generate_fake_document, send_callback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GeneratorWorker")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
POLL_INTERVAL = 5


def get_clickhouse_client():
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", 8123)),
        user=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
    )


def update_log(request_id: str, status: str, duration_ms: int, result_url: str):
    try:
        client = get_clickhouse_client()
        query = f"""
            ALTER TABLE generation_logs
            UPDATE
                status=%(status)s,
                duration_ms=%(duration_ms)s,
                result_url=%(result_url)s
            WHERE request_id=%(id)s
        """
        client.command(
            query,
            parameters={
                "status": status,
                "duration_ms": duration_ms,
                "result_url": result_url,
                "id": request_id,
            }
        )
        logger.info(f"Лог для {request_id} обновлен в ClickHouse")
    except Exception as e:
        logger.error(f"Не удалось обновить лог для {request_id}: {e}")


async def process_task(redis_conn, ch_client, key: str):
    logger.info(f"Найдена задача: {key}")
    try:
        request_id, doc_type = key.split("_")
    except ValueError:
        logger.warning(f"Неверный формат ключа: {key}. Удаляю")
        redis_conn.delete(key)
        return
    raw_data = redis_conn.get(key)
    if not raw_data:
        logger.warning(f"Ключ {key} есть, но данных нет. Удаляю")
        redis_conn.delete(key)
        return
    try:
        data = json.loads(raw_data)
        user_data = data["user_data"]
        callback_url = data["callback_url"]
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Неверный формат json в {key}. Удаляю")
        redis_conn.delete(key)
        return
    start_time = time.time()

    try:
        doc_url = generate_fake_document(user_data, doc_type)
        status = "COMPLETED"
        result_payload = {"url": doc_url, "doc_type": doc_type, "status": "success"}
    except Exception as e:
        logger.error(f"Ошибка генерации документа для {key}: {e}")
        doc_url = None
        status = "FAILED"
        result_payload = {"error": str(e), "status": "failed"}

    duration_ms = int((time.time() - start_time) * 1000)

    asyncio.create_task(send_callback(callback_url, result_payload))
    update_log(request_id, status, duration_ms, doc_url)
    result_key = f"{key}_result"
    redis_conn.set(result_key, json.dumps(result_payload), ex=3600)
    redis_conn.delete(key)
    logger.info(f"Задача {key} завершена за {duration_ms} мс")


async def main_loop():
    logger.info(f"Воркер генератора запускается...")
    redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    while True:
        try:
            tasks = redis_conn.keys("*_*")
            tasks_to_process = []
            for t in tasks:
                if t.endswith("_result") or t.endswith("_processing"):
                    continue
                if not redis_conn.exists(f"{t}_processing"):
                    tasks_to_process.append(t)
            if tasks_to_process:
                logger.info(f"Найдено {len(tasks_to_process)} задач")
                for t in tasks_to_process:
                    redis_conn.set(f"{t}_processing", 1 , ex=60)
                for key in tasks_to_process:
                    await process_task(redis_conn, get_clickhouse_client(), key)
        except redis.exceptions.ConnectionError:
            logger.error(f"Не удалось подключиться к Redis, повторо через 5 секунд")
        except Exception as e:
            logger.error(f"Неизвестная ошибка в цикле:{e}")
        await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    
    asyncio.run(main_loop())

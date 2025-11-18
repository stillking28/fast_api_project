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
            },
        )
        logger.info(f"Лог для {request_id} обновлен в ClickHouse")
    except Exception as e:
        logger.error(f"Не удалось обновить лог для {request_id}: {e}")


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
                    redis_conn.set(f"{t}_processing", 1, ex=60)
                for key in tasks_to_process:
                    await process_task(redis_conn, get_clickhouse_client(), key)
        except redis.exceptions.ConnectionError:
            logger.error(f"Не удалось подключиться к Redis, повторо через 5 секунд")
        except Exception as e:
            logger.error(f"Неизвестная ошибка в цикле:{e}")
        await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":

    asyncio.run(main_loop())

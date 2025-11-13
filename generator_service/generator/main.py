import os
import logging
import clickhouse_connect
from fastapi import FastAPI, HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GeneratorAdmin")
app = FastAPI()


def get_clickhouse_client():
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", 8123)),
        user=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
    )


@app.get("/admin/logs")
def get_generation_logs(limit: int = 50):
    try:
        client = get_clickhouse_client()
        query = "SELECT * FROM generation_logs ORDER BY request_time DESC LIMIT %(limit)s"
        result = client.query(query, parameters={"limit": limit})

        column_names = result.column_names
        logs = [dict(zip(column_names, row)) for row in result.result_rows]
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/ping")
def ping():
    return {"message": "Ping Pong"}

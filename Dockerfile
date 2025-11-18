FROM python:3.12-slim

WORKDIR /app

ENV POETRY_NO_INTERACTION = 1 \
    POETRY_CACHE_DIR = /tmp/poetry_cache

RUN apt-get update && apt-get install -y wget && \
    rm -rf /var/lib/apt/lists/*    

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-root --without dev

COPY ./app ./app

EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port",  "8000"]

FROM python:3.12-slim
WORKDIR /app

ENV POETRY-NO-INTERACTION=1 \
    POETRY-CACHE-DIR=/tmp/poetry_cache

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-root

COPY ./generator ./generator

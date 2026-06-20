# charm-back-fastapi

REST API для приложения Charm на FastAPI.

## Стек

- FastAPI
- SQLAlchemy async
- PostgreSQL
- Alembic
- Pydantic settings
- uv
- Ruff, mypy, pytest

## Локальный Запуск

Создать и активировать виртуальное окружение:

```bash
uv venv
source .venv/bin/activate
```

Установить зависимости:

```bash
uv sync --extra dev
```

Создать локальный файл окружения:

```bash
cp .env.example .env
```

Запустить PostgreSQL:

```bash
docker compose up -d
```

Применить миграции:

```bash
uv run alembic upgrade head
```

Запустить API:

```bash
uv run uvicorn app.main:app --reload
```

Проверка health endpoint:

```text
http://127.0.0.1:8000/health
```

## Миграции

Создать новую миграцию после изменения SQLAlchemy-моделей:

```bash
uv run alembic revision --autogenerate -m "describe schema change"
```

После генерации нужно проверить файл в `alembic/versions/`, затем применить миграции:

```bash
uv run alembic upgrade head
```

Полезные команды:

```bash
uv run alembic current
uv run alembic history
uv run alembic downgrade -1
```

## Проверки

```bash
uv run ruff format .
uv run ruff check .
uv run mypy app
uv run pytest
```

## Заметки Для Разработки

- Приложение подключается к БД через `asyncpg`.
- Alembic-миграции подключаются к БД через синхронный `psycopg`.
- Локальные секреты лежат в `.env` и не коммитятся.
- `uv.lock` коммитится для воспроизводимой установки зависимостей.

# charm-back-fastapi

REST API для приложения Charm на FastAPI.

## Стек

- Python 3.12+
- FastAPI
- Uvicorn
- SQLAlchemy 2.0 async
- PostgreSQL
- asyncpg для приложения
- psycopg для Alembic-миграций
- Alembic
- Pydantic Settings
- pwdlib Argon2 для хеширования паролей
- python-jose для JWT
- email-validator
- Docker Compose для локального PostgreSQL
- uv для окружения, зависимостей и запуска команд
- pytest, pytest-asyncio, HTTPX для API-тестов
- Ruff и mypy для статических проверок

## Возможности API

- Регистрация и логин по email/password.
- JWT bearer-аутентификация.
- Получение, обновление и удаление текущего профиля.
- Смена email и пароля с проверкой текущего пароля.
- Optimistic locking через поле `version`.
- Charm discovery: получение следующего кандидата и реакции `like`, `dislike`, `skip`.
- Matches: список взаимных лайков с пагинацией.
- Admin profiles: поиск профилей, смена статуса и роли.
- CORS-настройка для подключения browser frontend.
- Единый формат ошибок вида `{"detail": "error.<domain>.<reason>"}`.

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

Основные переменные окружения:

- `DATABASE_URL` — async URL для приложения, например `postgresql+asyncpg://charm:charm@localhost:5433/charm`.
- `JWT_SECRET` — секрет для подписи JWT.
- `JWT_TTL_MINUTES` — время жизни access token.
- `BACKEND_CORS_ORIGINS` — список frontend origin через запятую, например `http://localhost:5173,http://127.0.0.1:5173`.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT` — настройки локального контейнера PostgreSQL.

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

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Структура

```text
app/api/              HTTP endpoint-ы, зависимости и presenter-ы
app/core/             настройки, безопасность, общие ошибки
app/db/               SQLAlchemy base/session
app/models/           SQLAlchemy ORM-модели
app/repositories/     SQL-запросы и работа с БД
app/schemas/          Pydantic request/response-схемы
app/services/         бизнес-логика
alembic/              миграции БД
tests/                интеграционные API-тесты
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

## Тесты

Тесты используют отдельную базу данных `charm_test`, чтобы не очищать локальную
dev-БД.

Создать локальный файл окружения для тестов:

```bash
cp .env.test.example .env.test
```

Создать тестовую базу:

```bash
docker compose exec postgres psql -U charm -d charm \
  -c "CREATE DATABASE charm_test;"
```

Применить миграции к тестовой базе:

```bash
ENV_FILE=.env.test uv run alembic upgrade head
```

Запустить тесты:

```bash
ENV_FILE=.env.test uv run pytest
```

Сейчас тестами покрыты:

- регистрация и логин;
- получение и обновление профиля;
- смена email и пароля;
- charm discovery и реакции;
- matches и пагинация;
- admin profile search и admin-действия.
- CORS preflight для разрешенного frontend origin.

## Проверки Кода

```bash
uv run ruff format .
uv run ruff check .
uv run mypy app
uv run pytest
```

## Заметки Для Разработки

- Приложение подключается к БД через `asyncpg`.
- Alembic-миграции подключаются к БД через синхронный `psycopg`.
- Локальные секреты лежат в `.env` и `.env.test`; эти файлы не коммитятся.
- `.env.example` и `.env.test.example` коммитятся как шаблоны.
- `uv.lock` коммитится для воспроизводимой установки зависимостей.
- Тесты используют `httpx.AsyncClient` с `ASGITransport`, поэтому запускать `uvicorn` для тестов не нужно.

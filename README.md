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
- Docker и Docker Compose для локального запуска API/PostgreSQL
- uv для окружения, зависимостей и запуска команд
- pytest, pytest-asyncio, HTTPX для API-тестов
- Ruff и mypy для статических проверок
- GitHub Actions для CI

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

## API Endpoints

Auth:

```text
POST /api/v1/registration
POST /api/v1/auth/login
```

Profile:

```text
GET    /api/v1/profile
PATCH  /api/v1/profile
PATCH  /api/v1/profile/email
PATCH  /api/v1/profile/password
DELETE /api/v1/profile
```

Charm:

```text
GET  /api/v1/charm
POST /api/v1/charm
```

Matches:

```text
GET /api/v1/matches
```

Admin:

```text
GET   /api/v1/admin/profiles
PATCH /api/v1/admin/profiles/{profile_id}/status
PATCH /api/v1/admin/profiles/{profile_id}/role
```

## Локальный запуск В Docker Compose

Создать локальный файл окружения:

```bash
cp .env.example .env
```

Основные переменные окружения:

- `API_PORT` — порт API на хосте, например `8000`.
- `DATABASE_URL` — async URL для приложения внутри compose-сети, например `postgresql+asyncpg://charm_user:charm_password@postgres:5432/charm`.
- `JWT_SECRET` — секрет для подписи JWT.
- `JWT_TTL_MINUTES` — время жизни access token.
- `BACKEND_CORS_ORIGINS` — список frontend origin через запятую, например `http://localhost:5173,http://127.0.0.1:5173`.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT` — настройки локального контейнера PostgreSQL.

Собрать образ и запустить PostgreSQL:

```bash
docker compose up --build -d postgres
```

Применить миграции:

```bash
docker compose run --rm api uv run alembic upgrade head
```

Запустить API:

```bash
docker compose up -d api
```

Проверка health endpoint:

```text
http://127.0.0.1:8000/health
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Остановить контейнеры:

```bash
docker compose down
```

Удалить volume с локальными данными:

```bash
docker compose down -v
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
dev-БД. API-контейнер для тестов не нужен: тесты запускают FastAPI-приложение
напрямую через `httpx.AsyncClient` и `ASGITransport`. Нужен только PostgreSQL.

Создать локальный файл окружения для тестов:

```bash
cp .env.test.example .env.test
```

Запустить PostgreSQL:

```bash
docker compose up -d postgres
```

Создать тестовую базу один раз:

```bash
docker compose exec postgres psql -U charm_user -d charm \
  -c "CREATE DATABASE charm_test;"
```

Если база уже создана, команда вернет ошибку `already exists`; это нормально.

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
- admin profile search и admin-действия;
- CORS preflight для разрешенного frontend origin.

## Проверки кода

```bash
uv run ruff format .
uv run ruff check .
uv run mypy app
ENV_FILE=.env.test uv run pytest
```

CI в GitHub Actions запускает:

- установку зависимостей через `uv sync --extra dev --locked`;
- применение Alembic-миграций к PostgreSQL service;
- `ruff format --check`;
- `ruff check`;
- `mypy app`;
- `pytest`.

## Заметки

- Приложение подключается к БД через `asyncpg`.
- Alembic-миграции подключаются к БД через синхронный `psycopg`.
- Локальные секреты лежат в `.env` и `.env.test`; эти файлы не коммитятся.
- `.env.example` и `.env.test.example` коммитятся как шаблоны.
- `uv.lock` коммитится для воспроизводимой установки зависимостей.
- Тесты используют `httpx.AsyncClient` с `ASGITransport`, поэтому запускать `uvicorn` для тестов не нужно.
- Docker image не запускает миграции автоматически; миграции выполняются отдельной командой.

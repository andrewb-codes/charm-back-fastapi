# charm-back-fastapi

REST API для приложения Charm на FastAPI.

## Демо

Публичный demo frontend: `https://<demo-domain>`

Demo-аккаунт:

```text
email: demo@example.com
password: vgoaV3WqMW9V079
```

При деплое seed-скрипт создает demo-пользователя и набор synthetic users для
наполнения discovery/admin сценариев. Часть synthetic users заранее лайкает demo
профиль, поэтому demo-аккаунт сразу показывает непустое состояние приложения.

## Стек

- Python 3.12+
- FastAPI
- Uvicorn
- Streamlit для простого frontend-интерфейса
- SQLAlchemy 2.0 async
- PostgreSQL
- asyncpg для приложения
- psycopg для Alembic-миграций
- Alembic
- Pydantic Settings
- pwdlib Argon2 для хеширования паролей
- python-jose для JWT
- email-validator
- Docker и Docker Compose для локального запуска API/frontend/PostgreSQL
- отдельные Docker images для API и frontend
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

## Локальный запуск в Docker Compose

Создать локальный файл окружения:

```bash
cp .env.example .env
```

Основные переменные окружения:

- `DATABASE_URL` — async URL для приложения внутри compose-сети, например `postgresql+asyncpg://charm_user:charm_password@postgres:5432/charm`.
- `JWT_SECRET` — секрет для подписи JWT.
- `DEMO_USER_ENABLED`, `DEMO_EMAIL`, `DEMO_PASSWORD` — опциональный demo-аккаунт,
  который создает seed-скрипт.
- `SYNTHETIC_USERS_ENABLED`, `SYNTHETIC_USERS_COUNT`,
  `SYNTHETIC_USERS_EMAIL_PREFIX`, `SYNTHETIC_USERS_PASSWORD` — опциональные
  синтетические пользователи для наполнения discovery/admin сценариев.
- `STREAMLIT_API_URL` — URL API внутри compose-сети, обычно `http://api:8000`.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT` — настройки локального контейнера PostgreSQL.
- `API_PORT`, `STREAMLIT_PORT` — порты API и Streamlit frontend на хосте.

Настройки приложения с безопасными дефолтами (`APP_NAME`, `DEBUG`,
`JWT_ALGORITHM`, `JWT_TTL_MINUTES`, `BACKEND_CORS_ORIGINS`) задаются в коде и
не передаются в контейнеры через compose.

Локальный `docker-compose.yml` публикует Postgres, API, и Streamlit на `localhost`,
чтобы было удобно пользоваться Swagger UI и проверять БД и frontend. Production
compose для VPS устроен иначе: наружу через Caddy предполагается публиковать
только Streamlit, а БД и API остаются во внутренней Docker-сети.

API и frontend собираются разными Dockerfile:

- `Dockerfile.api` — устанавливает зависимости из optional extra `api` и
  запускает FastAPI/Uvicorn.
- `Dockerfile.frontend` — устанавливает зависимости из optional extra `frontend`
  и запускает Streamlit. Команда запуска frontend находится в Dockerfile, а не
  в compose-файле.

Первый запуск или запуск после изменения миграций:

```bash
docker compose up --build -d postgres
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m app.scripts.seed_data
docker compose up -d api frontend
```

После того как миграции уже применены, можно поднимать все сервисы одной командой:

```bash
docker compose up --build -d
```

`docker compose up` не применяет миграции и seed-данные автоматически. Эти шаги
выполняются отдельными командами, чтобы запуск контейнера не менял схему БД и
данные неявно. Seed-скрипт idempotent: он проверяет существующие email перед
созданием demo/synthetic пользователей.

Проверка health endpoint:

```text
http://127.0.0.1:8000/health
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Streamlit frontend:

```text
http://127.0.0.1:8501
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
frontend/             Streamlit-интерфейс для auth, profile, discovery, matches и admin
alembic/              миграции БД
tests/                интеграционные API-тесты
Dockerfile.api        production/local image для FastAPI
Dockerfile.frontend   production/local image для Streamlit
deploy/ansible/       Ansible-деплой на VPS
```

## Зависимости

Базовые runtime-зависимости минимальные. Зависимости приложения разделены на
optional extras:

- `api` — FastAPI, Uvicorn, SQLAlchemy, драйверы PostgreSQL, Alembic, JWT и
  парольные хеши.
- `frontend` — Streamlit и HTTPX.
- `all` — API и frontend вместе.

Для локальной разработки обычно нужно установить dev-группу и оба runtime-набора:

```bash
uv sync --group dev --extra all
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
uv sync --group dev --extra all
uv run ruff format .
uv run ruff check .
uv run mypy app frontend
ENV_FILE=.env.test uv run pytest
```

CI в GitHub Actions запускает:

- установку зависимостей через `uv sync --group dev --extra all --locked`;
- применение Alembic-миграций к PostgreSQL service;
- `ruff format --check`;
- `ruff check`;
- `mypy app`;
- `pytest`.

## Деплой

Ansible-сценарий для деплоя на VPS лежит в [deploy/ansible](deploy/ansible/README.md).
Он устанавливает Docker, подтягивает готовые API/frontend Docker images из
registry, генерирует production `.env` и compose-файл, запускает PostgreSQL,
применяет Alembic-миграции, запускает seed-скрипт и поднимает API/Streamlit.
В production публичным через Caddy предполагается только Streamlit; API
остается во внутренней Docker-сети и вызывается frontend-ом. Подробные команды
запуска, Vault и схема Caddy описаны в deploy README.

GitHub Actions после успешных проверок на push в `main` собирает два Docker
image, публикует их в GHCR и запускает Ansible-деплой на VPS. Для этого в
GitHub Variables должны быть заданы `VPS_HOST` и `VPS_USER`, а в GitHub Secrets
— `VPS_SSH_KEY`, `POSTGRES_PASSWORD` и `JWT_SECRET`.

## Заметки

- Приложение подключается к БД через `asyncpg`.
- Alembic-миграции подключаются к БД через синхронный `psycopg`.
- Локальные секреты лежат в `.env` и `.env.test`; эти файлы не коммитятся.
- `.env.example` и `.env.test.example` коммитятся как шаблоны.
- `uv.lock` коммитится для воспроизводимой установки зависимостей.
- Тесты используют `httpx.AsyncClient` с `ASGITransport`, поэтому запускать `uvicorn` для тестов не нужно.
- Docker images не запускают миграции и seed-данные автоматически; эти шаги выполняются отдельными командами.

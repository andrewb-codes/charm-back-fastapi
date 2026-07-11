# Charm

Backend и Streamlit-интерфейс приложения знакомств. API реализует регистрацию,
JWT-аутентификацию, управление профилем, discovery, взаимные лайки и
административное управление пользователями.

## Демо

Публичный frontend на production-сервере открывается через домен, настроенный в Caddy:

```text
`https://charm.andrewb.ru`
```

```text
email: demo@example.com
password: demopwd123456!
```

Production seed создает admin, demo и synthetic users, чтобы discovery и
admin-раздел содержали данные сразу после деплоя.

## Возможности

- регистрация и вход по email/password;
- получение, изменение и удаление профиля;
- смена email и пароля;
- discovery с реакциями `like`, `dislike` и `skip`;
- список взаимных лайков;
- поиск профилей и управление ролями и статусами для администратора;
- optimistic locking через поле `version`;
- единый формат ошибок `{"detail": "error.<domain>.<reason>"}`.

Основной стек: Python 3.12-3.14, FastAPI, Streamlit, SQLAlchemy 2 async, PostgreSQL,
Alembic, Docker Compose и uv.

## Архитектура приложения

FastAPI разделен на HTTP-слой, сервисы, репозитории и SQLAlchemy-модели.
Streamlit работает как отдельный клиент API. Оба приложения используют разные
Docker images:

```text
browser
   │
   ▼
Streamlit frontend ── HTTP/JWT ──▶ FastAPI ── SQLAlchemy ──▶ PostgreSQL
```

В локальном и production Compose API и PostgreSQL находятся во внутренней
сети. Публичным сервисом остается только frontend. API и frontend собираются в разные Docker images;
runtime-файлы в images не включаются.

## Локальный запуск

```bash
cp .env.example .env
```

Замените placeholder-значения. Пароль в `DATABASE_URL` должен соответствовать
`POSTGRES_PASSWORD`. Если он содержит зарезервированные URI-символы, его часть внутри URL
необходимо percent-encode; значение `POSTGRES_PASSWORD` остаётся исходным.

Bootstrap admin, demo-профиль и synthetic users управляются группами переменных
`BOOTSTRAP_ADMIN_*`, `DEMO_*` и `SYNTHETIC_USERS_*`.
В production значения задаются через Ansible Vault или GitHub Secrets.

Первый запуск:

```bash
docker compose up --build -d postgres
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m charm.scripts.seed_data
docker compose up -d api frontend
```

При следующих запусках, если миграции и seed не изменялись:

```bash
docker compose up --build -d
```

Streamlit доступен по адресу `http://127.0.0.1:8501`. PostgreSQL публикуется на
порту `POSTGRES_PORT` и хранит данные в volume `charm_postgres_data`.
API не публикуется на хост и доступен контейнерам Compose-сети по адресу `http://api:8000`.

Остановка:

```bash
docker compose down
```

## API

Без JWT доступны `/health`, регистрация и login. Остальные маршруты требуют
`Authorization: Bearer <token>`. Новый профиль получает статус `INACTIVE`;
активировать его может admin.

| Method | Route | Назначение |
|---|---|---|
| `GET` | `/health` | Проверка состояния API |
| `POST` | `/api/v1/registration` | Регистрация |
| `POST` | `/api/v1/auth/login` | Получение JWT |
| `GET/PATCH/DELETE` | `/api/v1/profile` | Просмотр, изменение или удаление профиля |
| `PATCH` | `/api/v1/profile/email` | Смена email |
| `PATCH` | `/api/v1/profile/password` | Смена пароля |
| `GET/POST` | `/api/v1/charm` | Следующий кандидат или реакция |
| `GET` | `/api/v1/matches` | Взаимные лайки |
| `GET` | `/api/v1/admin/profiles` | Поиск профилей; admin |
| `PATCH` | `/api/v1/admin/profiles/{id}/status` | Изменение статуса; admin |
| `PATCH` | `/api/v1/admin/profiles/{id}/role` | Изменение роли; admin |

Health endpoint и Swagger UI внутри Compose-сети:

```text
http://api:8000/health
http://api:8000/docs
```

## Разработка

Установите API, frontend и dev-зависимости:

```bash
uv sync --group dev --extra all
```

Основные директории:

```text
src/charm/api/          FastAPI entrypoint, endpoints и зависимости
src/charm/core/         настройки, security и ошибки
src/charm/db/           SQLAlchemy base/session
src/charm/models/       SQLAlchemy-модели
src/charm/repositories/ запросы к БД
src/charm/services/     бизнес-логика
src/charm/frontend/     Streamlit-интерфейс
src/charm/scripts/      seed и maintenance scripts
alembic/                миграции
tests/                  интеграционные API-тесты
deploy/ansible/         production-деплой
```

Создание и применение миграции:

```bash
uv run alembic revision --autogenerate -m "describe schema change"
uv run alembic upgrade head
```

Миграции нужно проверять вручную перед применением.

## Тесты и проверки

Тесты используют отдельную PostgreSQL-базу `charm_test`.

```bash
cp .env.test.example .env.test
docker compose up -d postgres
docker compose exec postgres psql -U charm_user -d charm \
  -c "CREATE DATABASE charm_test;"
ENV_FILE=.env.test uv run alembic upgrade head
ENV_FILE=.env.test uv run pytest
```

Ошибка `already exists` при повторном создании тестовой базы безопасна.

Статические проверки:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
```

CI выполняет эти проверки для push и pull request.

## Деплой

GitHub Actions при push в `main` собирает API и frontend images, публикует их в
GHCR и запускает Ansible playbook. Production публикует через общую сеть Caddy
только Streamlit; API и PostgreSQL остаются во внутренней сети.

Настройка GitHub Variables, Secrets, Vault, ручной запуск и эксплуатационные
команды описаны в [deploy/ansible/README.md](deploy/ansible/README.md).

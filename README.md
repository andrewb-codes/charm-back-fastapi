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
- единый формат ошибок `{"detail": "error.<domain>.<reason>"}`;
- rate limiting через Redis для public auth endpoints и авторизованных API routes;
- структурированное логирование запросов с `X-Request-ID`.

Основной стек: Python 3.12-3.13, FastAPI, Streamlit, SQLAlchemy 2 async, PostgreSQL,
Redis, Alembic, structlog, Docker Compose и uv.

## Архитектура приложения

FastAPI разделен на HTTP-слой, сервисы, репозитории и SQLAlchemy-модели.
Streamlit работает как отдельный клиент API. Оба приложения используют разные
Docker images:

```text
browser
   │
   ▼
Streamlit frontend ── HTTP/JWT ──▶ FastAPI ── SQLAlchemy ──▶ PostgreSQL
                                      │
                                      └── rate limits ──▶ Redis
```

В локальном и production Compose API, PostgreSQL и Redis находятся во внутренней
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

Логирование управляется переменными `ENVIRONMENT`, `LOG_LEVEL`, `LOG_FORMAT`
и `SQL_LOG_LEVEL`. Для локальной разработки используется `LOG_FORMAT=console`,
для production — `LOG_FORMAT=json`. Логи API пишутся в stdout процесса контейнера.

SQL-запросы по умолчанию не логируются: `SQL_LOG_LEVEL=WARNING`.

Rate limiting управляется переменными `RATE_LIMIT_*`. В Docker Compose он включен
по умолчанию, использует Redis по внутреннему адресу `async+redis://redis:6379/0`
и требует отдельный `RATE_LIMIT_KEY_SECRET` для HMAC-хеширования email/login
идентификаторов.

API, Streamlit frontend и Alembic читают `.env` по умолчанию. Для другого файла окружения
задайте `ENV_FILE`, например `ENV_FILE=.env.test uv run alembic upgrade head`.
`STREAMLIT_API_URL` нужен при запуске frontend вне Docker Compose; в Compose frontend
получает внутренний адрес API `http://api:8000` из `docker-compose.yml`.

Первый запуск:

```bash
docker compose up --build -d postgres redis
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m charm.scripts.seed_data
docker compose up -d api frontend
docker compose logs -f api
```

При следующих запусках, если миграции и seed не изменялись:

```bash
docker compose up --build -d
```

Streamlit доступен по адресу `http://127.0.0.1:8501`.

API и Redis не публикуются на хост и доступны только внутри Compose-сети.
PostgreSQL привязан к localhost на `POSTGRES_PORT` для локальной разработки.

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

### Rate limiting

API использует библиотеку `limits` и Redis storage. Счетчики являются
эфемерными: Redis запускается без persistence, с лимитом памяти `128mb` и policy
`volatile-ttl`. После перезапуска Redis текущие окна лимитов сбрасываются, что
допустимо для счетчиков защиты от частых запросов.

При превышении лимита API возвращает:

```json
{"detail": "error.rate_limit.exceeded"}
```

со статусом `429 Too Many Requests` и заголовком `Retry-After`. Для успешных
limited responses добавляются `X-RateLimit-Limit`, `X-RateLimit-Remaining` и
`X-RateLimit-Reset`.

Начальные лимиты:

| Scope | Route | Key | Limit |
|---|---|---|---|
| `login_global` | `POST /api/v1/auth/login` | global | `60 per minute` |
| `login_account` | failed `POST /api/v1/auth/login` | HMAC normalized email | `5 per minute` |
| `register_global` | `POST /api/v1/registration` | global | `30 per hour` |
| `register_identifier` | `POST /api/v1/registration` | HMAC normalized email | `3 per hour` |
| `profile_read` | `GET /api/v1/profile` | user id | `120 per minute` |
| `profile_write` | profile write/delete routes | user id | `30 per minute` |
| `charm_read` | `GET /api/v1/charm` | user id | `60 per minute` |
| `charm_react` | `POST /api/v1/charm` | user id | `60 per minute` |
| `matches_read` | `GET /api/v1/matches` | user id | `60 per minute` |
| `admin_read` | `GET /api/v1/admin/profiles` | admin user id | `120 per minute` |
| `admin_write` | admin write routes | admin user id | `30 per minute` |

`GET /health` не ограничивается.

Для login account-limit применяется только после неуспешной аутентификации.
Успешный login проверяет только global-limit, чтобы злоумышленник не мог легко
заблокировать чужой аккаунт запросами с неправильным паролем.

## Разработка

Установите API, frontend и dev-зависимости:

```bash
uv sync --group dev --extra all
```

Основные директории:

```text
src/charm/api/          FastAPI entrypoint, endpoints и зависимости
src/charm/core/         настройки, security, logging и ошибки
src/charm/db/           SQLAlchemy base/session
src/charm/middleware/   HTTP middleware
src/charm/models/       SQLAlchemy-модели
src/charm/repositories/ запросы к БД
src/charm/services/     бизнес-логика
src/charm/frontend/     Streamlit-интерфейс
src/charm/scripts/      seed и maintenance scripts
alembic/                миграции
tests/                  unit и интеграционные API-тесты
deploy/ansible/         production-деплой
```

Создание и применение миграции:

```bash
uv run alembic revision --autogenerate -m "describe schema change"
uv run alembic upgrade head
```

Миграции нужно проверять вручную перед применением.

## Тесты и проверки

Тесты используют отдельную PostgreSQL-базу `charm_test` в том же
PostgreSQL-контейнере. Не указывайте в `.env.test` основную БД `anomaly`:
фикстуры тестов очищают таблицы перед каждым тестом. Пользователь, пароль и
порт в `DATABASE_URL` из `.env.test` должны совпадать с `POSTGRES_USER`,
`POSTGRES_PASSWORD` и `POSTGRES_PORT` в `.env`.

В `.env.test` rate limiting выключен через `RATE_LIMIT_ENABLED=false`, чтобы
обычный test suite не зависел от Redis. Rate-limit wiring тестируется отдельно
через FastAPI dependency overrides и fake service.
Для тестов используется `ENVIRONMENT=test` и человекочитаемый `LOG_FORMAT=console`.

```bash
cp .env.test.example .env.test
docker compose up -d postgres
docker compose exec postgres psql -U charm_user -d charm \
  -c "CREATE DATABASE charm_test;"
ENV_FILE=.env.test uv run alembic upgrade head
ENV_FILE=.env.test uv run pytest
```

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
только Streamlit; API, PostgreSQL и Redis остаются во внутренней сети.

Настройка GitHub Variables, Secrets, Vault, ручной запуск и эксплуатационные
команды описаны в [deploy/ansible/README.md](deploy/ansible/README.md).

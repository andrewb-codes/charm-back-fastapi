# Деплой через Ansible

Playbook деплоит приложение на один Ubuntu/Debian VPS. Сервер загружает готовые 
API/frontend images из GHCR и запускает три сервиса через Docker Compose:

- `postgres` — PostgreSQL 17 с volume `charm_postgres_data`;
- `api` — FastAPI во внутренней сети;
- `frontend` — Streamlit во внутренней сети и общей external-сети `web`.

Streamlit обращается к API по адресу `http://api:8000`.
Reverse proxy обращается к frontend по alias `charm-frontend`.
API и PostgreSQL снаружи не публикуются.

## Конфигурация

- `inventory.ini.example` — пример inventory;
- `group_vars/portfolio/main.yml` — несекретные переменные;
- `group_vars/portfolio/vault.yml.example` — шаблон секретов;
- `templates/env.j2` — production `.env`;
- `templates/docker-compose.prod.yml.j2` — production Compose;
- `playbook.yml` — установка Docker, миграции, seed и запуск сервисов.

Production images:

```yaml
api_image: ghcr.io/andrewb-codes/charm-back-fastapi-api
frontend_image: ghcr.io/andrewb-codes/charm-back-fastapi-frontend
app_image_tag: main
```

Seed-скрипт создает включенные в `app_env` сущности:

- bootstrap admin из `BOOTSTRAP_ADMIN_*`;
- demo-профиль из `DEMO_*`;
- synthetic users из `SYNTHETIC_USERS_*`.

Пароли задаются через Ansible Vault или GitHub Secrets. Повторный seed не
создает профили с уже существующими email. Если email bootstrap admin занят
профилем без роли `ADMIN`, deploy завершается с ошибкой.

## Что делает playbook

1. Устанавливает Docker Engine и Compose plugin.
2. Создаёт external-сеть `web` и каталог `/opt/apps/charm`.
3. Рендерит production `.env` и `docker-compose.prod.yml`.
4. Загружает images, запускает Alembic-миграции и seed admin/demo-профилей.
5. Поднимает API и frontend.

Основные настройки находятся в `group_vars/portfolio/main.yml`, 
секреты — в зашифрованном `group_vars/portfolio/vault.yml`.

## Автоматический деплой

Workflow `.github/workflows/ci-cd.yml` запускает deploy после успешных проверок
при push в `main`. Images публикуются с тегами `main` и commit SHA.

GitHub Variables:

```text
VPS_HOST
VPS_USER
```

GitHub Secrets:

```text
VPS_SSH_KEY
POSTGRES_PASSWORD
JWT_SECRET
BOOTSTRAP_ADMIN_PASSWORD
DEMO_PASSWORD
SYNTHETIC_USERS_PASSWORD
```

Публичную часть `VPS_SSH_KEY` должна находиться в `~/.ssh/authorized_keys` 
пользователя `VPS_USER`.

## Ручной запуск

```bash
cd deploy/ansible
cp inventory.ini.example inventory.ini
cp group_vars/portfolio/vault.yml.example group_vars/portfolio/vault.yml

# Заполнить inventory и vault.yml, затем:
ansible-vault encrypt group_vars/portfolio/vault.yml
ansible-playbook playbook.yml --ask-vault-pass
```

Для запуска без интерактивного ввода создайте файл с паролем Vault вне
репозитория:

```bash
mkdir -p ~/.ansible
nano ~/.ansible/charm-vault-pass
chmod 600 ~/.ansible/charm-vault-pass
ansible-playbook playbook.yml \
  --vault-password-file ~/.ansible/charm-vault-pass
```

Ожидаемые поля Vault перечислены в `vault.yml.example`. Application images
должны быть заранее опубликованы в GHCR.

## Диагностика

```bash
cd /opt/apps/charm
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f postgres
docker compose -f docker-compose.prod.yml run --rm api alembic current
docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
docker compose -f docker-compose.prod.yml run --rm api python -m charm.scripts.seed_data
```

## Ротация пароля PostgreSQL

`POSTGRES_PASSWORD` применяется только при первичной инициализации пустого volume.
Для существующей БД сначала измените пароль роли:

```bash
cd /opt/apps/charm
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U charm_user -d charm
```

В `psql`:

```text
\password charm_user
\q
```

Затем обновите `postgres_password` в Ansible Vault или `POSTGRES_PASSWORD` в GitHub
Secrets и повторите deploy. Удаление `charm_postgres_data` приводит к потере данных.

## Caddy

Пример конфигурации для reverse proxy, подключённого к сети `web`:

```caddyfile
charm.example.com {
  reverse_proxy charm-frontend:8501
}
```

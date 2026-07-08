# Деплой через Ansible

Этот сценарий деплоит Charm на один Ubuntu/Debian VPS через Docker Compose.
Сервер не билдит приложение из исходников: playbook подтягивает готовые Docker
images для API и frontend из registry.

Production compose подключает Streamlit к общей Docker-сети `web`. Caddy можно
держать отдельным compose-проектом и проксировать публичные запросы к alias-у
`charm-frontend`. FastAPI остается во внутренней сети проекта и доступен
Streamlit по адресу `http://api:8000`.

## Файлы

- `inventory.ini.example` — пример inventory; скопировать в `inventory.ini` и
  указать адрес VPS.
- `group_vars/portfolio/main.yml` — несекретные настройки деплоя для общего
  portfolio VPS.
- `group_vars/portfolio/vault.yml.example` — пример секретов; скопировать в
  `group_vars/portfolio/vault.yml` и зашифровать через Ansible Vault.
- `templates/env.j2` — шаблон production `.env`.
- `templates/docker-compose.prod.yml.j2` — шаблон production compose-файла.
- `playbook.yml` — устанавливает Docker, создает общую Docker-сеть `web`,
  деплоит приложение, запускает Alembic миграции и seed-скрипт.

## Seed-данные

После миграций playbook запускает:

```bash
docker compose -f docker-compose.prod.yml run --rm api python -m app.scripts.seed_data
```

Seed-скрипт создает данные только если соответствующие переменные включены в
production `.env` через `app_env`:

```yaml
app_env:
  DEMO_USER_ENABLED: "true"
  DEMO_EMAIL: demo@example.com
  DEMO_PASSWORD: "{{ demo_password }}"
  SYNTHETIC_USERS_ENABLED: "true"
  SYNTHETIC_USERS_COUNT: "100"
  SYNTHETIC_USERS_EMAIL_PREFIX: synthetic
  SYNTHETIC_USERS_PASSWORD: "{{ synthetic_users_password }}"
```

`DEMO_PASSWORD` и `SYNTHETIC_USERS_PASSWORD` лучше хранить в
`group_vars/portfolio/vault.yml` для ручного запуска и в GitHub Secrets для
автоматического деплоя. Если флаги выключены или переменные не заданы,
seed-скрипт не создает соответствующие данные.

## Docker images

Production compose использует images из `group_vars/portfolio/main.yml`:

```yaml
api_image: ghcr.io/andrewb-codes/charm-back-fastapi-api
frontend_image: ghcr.io/andrewb-codes/charm-back-fastapi-frontend
app_image_tag: main

api_image_ref: "{{ api_image }}:{{ app_image_tag }}"
frontend_image_ref: "{{ frontend_image }}:{{ app_image_tag }}"
```

При автоматическом деплое GitHub Actions сам собирает два image:

- `Dockerfile.api` -> `ghcr.io/<owner>/<repo>-api`;
- `Dockerfile.frontend` -> `ghcr.io/<owner>/<repo>-frontend`.

Оба image публикуются в GHCR с тегами `main` и commit SHA. Затем workflow
запускает этот playbook с тегом текущего коммита, а VPS получает готовые images
через `docker compose pull`.

## Автоматический деплой из GitHub Actions

Workflow `.github/workflows/ci.yml` запускает деплой после успешных проверок
только при push в `main`.

Нужно добавить GitHub Variables:

```text
VPS_HOST
VPS_USER
```

И GitHub Secrets:

```text
VPS_SSH_KEY
POSTGRES_PASSWORD
JWT_SECRET
DEMO_PASSWORD
SYNTHETIC_USERS_PASSWORD
```

`VPS_SSH_KEY` — приватный SSH-ключ, которым GitHub Actions подключается к VPS.
Публичная часть ключа должна быть добавлена на сервер в
`~/.ssh/authorized_keys` для пользователя `VPS_USER`.

## Ручной запуск без GitHub Actions

Перед ручным запуском Ansible нужные API/frontend images уже должны быть
опубликованы в GHCR. Обычно это делает GitHub Actions после push в `main`.

```bash
cd deploy/ansible
cp inventory.ini.example inventory.ini
cp group_vars/portfolio/vault.yml.example group_vars/portfolio/vault.yml
ansible-vault encrypt group_vars/portfolio/vault.yml
ansible-playbook playbook.yml --ask-vault-pass
```

Для ручного запуска `group_vars/portfolio/vault.yml` должен содержать секреты,
которые используются в `group_vars/portfolio/main.yml`:

```yaml
postgres_password: replace-with-a-long-random-password
jwt_secret: replace-with-a-long-random-secret
demo_password: replace-with-demo-password
synthetic_users_password: replace-with-synthetic-users-password
```

По умолчанию ручной запуск использует image-тег `main` из
`group_vars/portfolio/main.yml`. Если нужно задеплоить конкретный тег, передайте
его явно:

```bash
ansible-playbook playbook.yml \
  --extra-vars "app_image_tag=<commit-sha-or-tag>" \
  --ask-vault-pass
```

Чтобы не вводить пароль Vault вручную при каждом запуске, можно хранить его
вне репозитория:

```bash
mkdir -p ~/.ansible
nano ~/.ansible/charm-vault-pass
chmod 600 ~/.ansible/charm-vault-pass
```

В файле `~/.ansible/charm-vault-pass` должна быть одна строка: пароль от
Ansible Vault без кавычек. Проверить расшифровку:

```bash
ansible-vault view group_vars/portfolio/vault.yml --vault-password-file ~/.ansible/charm-vault-pass
```

Запуск playbook с файлом пароля:

```bash
ansible-playbook playbook.yml --vault-password-file ~/.ansible/charm-vault-pass
```

## Полезные команды на VPS

```bash
cd /opt/apps/charm
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml run --rm api alembic current
docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
docker compose -f docker-compose.prod.yml run --rm api python -m app.scripts.seed_data
```

## Caddy и общая Docker-сеть

Playbook создает external Docker network `web`. Это общая сеть для reverse proxy
и всех публичных приложений на VPS.

Charm подключает к этой сети только публичный frontend:

- `charm-frontend` — Streamlit на порту `8501`;

FastAPI и PostgreSQL к `web` не подключаются и остаются только во внутренней
`default`-сети проекта. Streamlit ходит в API внутри этой сети по адресу
`http://api:8000`.

Пример Caddyfile для отдельного proxy compose-проекта:

```caddyfile
charm.example.com {
  reverse_proxy charm-frontend:8501
}
```

Когда на сервер добавятся другие приложения, они тоже должны подключать свои
публичные сервисы к сети `web` со своими alias-ами, например
`anomaly-frontend`, `rag-frontend`.

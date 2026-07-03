# Деплой через Ansible

Этот сценарий деплоит Charm на один Ubuntu/Debian VPS через Docker Compose.
Сервер не билдит приложение из исходников: playbook подтягивает готовый Docker
image из registry.

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
  деплоит приложение и запускает Alembic миграции.

## Docker image

Production compose использует image из `group_vars/portfolio/main.yml`:

```yaml
app_image: ghcr.io/andrewb-codes/charm-back-fastapi
app_image_tag: main
```

При автоматическом деплое GitHub Actions сам собирает image, публикует его в
GHCR с тегами `main` и commit SHA, а затем запускает этот playbook с тегом
текущего коммита. VPS получает готовый image через `docker compose pull`.

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
```

`VPS_SSH_KEY` — приватный SSH-ключ, которым GitHub Actions подключается к VPS.
Публичная часть ключа должна быть добавлена на сервер в
`~/.ssh/authorized_keys` для пользователя `VPS_USER`.

## Ручной запуск без GitHub Actions

Перед ручным запуском Ansible нужный image уже должен быть опубликован в GHCR.
Обычно это делает GitHub Actions после push в `main`.

```bash
cd deploy/ansible
cp inventory.ini.example inventory.ini
cp group_vars/portfolio/vault.yml.example group_vars/portfolio/vault.yml
ansible-vault encrypt group_vars/portfolio/vault.yml
ansible-playbook playbook.yml --ask-vault-pass
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
docker compose -f docker-compose.prod.yml run --rm api uv run alembic current
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

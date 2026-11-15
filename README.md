# Фудграм

«Фудграм» — сайт, на котором пользователи публикуют рецепты, добавляют чужие
рецепты в избранное и подписываются на авторов. Зарегистрированным
пользователям доступен «Список покупок»: он собирает ингредиенты выбранных
рецептов и позволяет скачать их одним файлом (одинаковые ингредиенты
суммируются).

**Стек:** Python 3.12, Django 4.2, Django REST Framework, Djoser (токены),
django-filter, PostgreSQL, Gunicorn, Nginx, Docker / Docker Compose,
GitHub Actions, React (готовый фронтенд).

## Структура

```
backend/      Django-проект (приложения users, recipes, api)
frontend/     React SPA (контейнер только собирает статику)
infra/        nginx.conf, Dockerfile шлюза, docker-compose (dev и production)
data/         ингредиенты (JSON/CSV)
docs/         спецификация API (Redoc) — /api/docs/
.github/      CI/CD: flake8 → сборка образов → Docker Hub → деплой
```

## Запуск в Docker (локально)

```bash
git clone <ссылка на репозиторий> && cd foodgram-st
cp .env.example .env          # заполните значения
cd infra
docker compose up --build -d
docker compose exec backend python manage.py load_ingredients
docker compose exec backend python manage.py load_test_data
docker compose exec backend python manage.py createsuperuser   # по желанию
```

- Сайт: http://localhost
- Документация API: http://localhost/api/docs/
- Админка: http://localhost/admin/

При старте контейнер backend сам выполняет миграции и `collectstatic`.

## Запуск без Docker (SQLite)

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export USE_SQLITE=true DEBUG=true
python manage.py migrate
python manage.py load_ingredients
python manage.py load_test_data
python manage.py runserver
```

## Тестовые данные

`python manage.py load_test_data` создаёт пользователей и по рецепту от каждого:

| Логин (email) | Права | Пароль |
|---|---|---|
| admin@foodgram.ru | администратор | Foodgram2025! |
| chef@foodgram.ru | пользователь | Foodgram2025! |
| cook@foodgram.ru | пользователь | Foodgram2025! |

## Переменные окружения (.env)

См. `.env.example`: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`,
`CSRF_TRUSTED_ORIGINS`, `USE_SQLITE`, `POSTGRES_DB`, `POSTGRES_USER`,
`POSTGRES_PASSWORD`, `DB_HOST`, `DB_PORT`.

## CI/CD

Workflow `.github/workflows/main.yml` при пуше в `main`:
1. проверяет код flake8 и миграции на PostgreSQL;
2. собирает образы `foodgram_backend`, `foodgram_frontend`, `foodgram_gateway` и пушит их на Docker Hub;
3. копирует `docker-compose.production.yml` на сервер и перезапускает контейнеры.

Секреты репозитория: `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `HOST`, `USER`,
`SSH_KEY`, `SSH_PASSPHRASE`. На сервере в папке `~/foodgram/` должен лежать `.env`.
Внешний nginx сервера проксирует домен на порт `8000` контейнера-шлюза
(`proxy_pass http://127.0.0.1:8000;`), HTTPS — через certbot.

## Примеры запросов

```
POST /api/users/                 регистрация
POST /api/auth/token/login/      {"email": "...", "password": "..."} → {"auth_token": "..."}
GET  /api/recipes/?page=1&limit=6&is_favorited=1&author=2
POST /api/recipes/               (Authorization: Token <токен>)
POST /api/recipes/{id}/favorite/
POST /api/recipes/{id}/shopping_cart/
GET  /api/recipes/download_shopping_cart/
GET  /api/recipes/{id}/get-link/ → {"short-link": "https://.../s/1a/"}
POST /api/users/{id}/subscribe/?recipes_limit=3
GET  /api/ingredients/?name=мол
```

## Автор

<Ваше имя> — <ссылка на GitHub>

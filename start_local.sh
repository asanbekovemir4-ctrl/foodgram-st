#!/bin/bash
# Локальный запуск Фудграма в Docker (4 контейнера: db, backend, frontend, nginx).
# Нужен запущенный Docker Desktop и файл .env в корне (см. .env.example).
# Сайт: http://localhost   API-документация: http://localhost/api/docs/   Админка: http://localhost/admin/
# Остановка: cd infra && docker compose down
set -e
cd "$(dirname "$0")/infra"

docker compose up --build -d

echo "Жду, пока backend применит миграции..."
until docker compose exec -T backend python manage.py showmigrations --plan >/dev/null 2>&1 \
      && curl -s -o /dev/null http://localhost/api/ingredients/; do
    sleep 2
done

docker compose exec -T backend python manage.py load_ingredients
docker compose exec -T backend python manage.py load_test_data

echo "Фудграм запущен: http://localhost"

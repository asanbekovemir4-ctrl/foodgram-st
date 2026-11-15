FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# При старте: миграции, сборка статики в общий volume, запуск Gunicorn.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && cp -r /app/collected_static/. /backend_static/ && gunicorn --bind 0.0.0.0:8000 foodgram.wsgi"]

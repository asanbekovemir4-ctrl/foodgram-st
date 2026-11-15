import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient

# Файл лежит в backend/data/ (попадает в Docker-образ) и в <repo>/data/.
CANDIDATES = (
    Path(settings.BASE_DIR) / 'data' / 'ingredients.json',
    Path(settings.BASE_DIR).parent / 'data' / 'ingredients.json',
)
DEFAULT_PATH = next((p for p in CANDIDATES if p.exists()), CANDIDATES[-1])


class Command(BaseCommand):
    help = 'Загружает ингредиенты из JSON-файла (data/ingredients.json).'

    def add_arguments(self, parser):
        parser.add_argument('--path', default=str(DEFAULT_PATH))

    def handle(self, *args, **options):
        with open(options['path'], encoding='utf-8') as file:
            data = json.load(file)
        created = Ingredient.objects.bulk_create(
            (Ingredient(**item) for item in data), ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(
            f'Обработано ингредиентов: {len(created)}.'))

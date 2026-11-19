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
        # Названия приводим к нижнему регистру: в исходных данных
        # встречаются единичные записи с заглавной буквы («Буррата»).
        created = Ingredient.objects.bulk_create(
            (
                Ingredient(
                    name=item['name'].strip().lower(),
                    measurement_unit=item['measurement_unit'],
                )
                for item in data
            ),
            ignore_conflicts=True,
        )
        self._normalize_existing()
        self.stdout.write(self.style.SUCCESS(
            f'Обработано ингредиентов: {len(created)}.'))

    @staticmethod
    def _normalize_existing():
        """Исправляет ранее загруженные названия с заглавной буквы."""
        for ingredient in Ingredient.objects.all():
            lower = ingredient.name.lower()
            if ingredient.name == lower:
                continue
            duplicate = Ingredient.objects.filter(
                name=lower,
                measurement_unit=ingredient.measurement_unit,
            ).first()
            if duplicate is None:
                ingredient.name = lower
                ingredient.save(update_fields=('name',))
            elif not ingredient.recipe_ingredients.exists():
                ingredient.delete()

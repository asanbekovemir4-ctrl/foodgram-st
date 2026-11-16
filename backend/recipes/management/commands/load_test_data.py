from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Recipe, RecipeIngredient

User = get_user_model()

# Фото блюд с Wikimedia Commons, авторы и лицензии — в data/images/CREDITS.md
IMAGES_DIR = Path(settings.BASE_DIR) / 'data' / 'images'

USERS = (
    # (username, email, first_name, last_name, is_staff)
    ('admin', 'admin@foodgram.ru', 'Админ', 'Админов', True),
    ('chef', 'chef@foodgram.ru', 'Иван', 'Поваров', False),
    ('cook', 'cook@foodgram.ru', 'Мария', 'Кулинарова', False),
)
PASSWORD = 'Foodgram2025!'

RECIPES = (
    # (название, описание, время, фото, ингредиенты)
    ('Блины на молоке', 'Смешать всё, жарить на сковороде.', 30, 'blini.jpg',
     (('молоко', 500), ('мука пшеничная', 200), ('яйца куриные', 2))),
    ('Омлет', 'Взбить яйца с молоком и запечь.', 15, 'omelette.jpg',
     (('яйца куриные', 3), ('молоко', 100))),
    ('Гречка с маслом', 'Отварить гречку, добавить масло.', 25,
     'buckwheat.jpg',
     (('гречневая крупа', 200), ('сливочное масло', 30))),
)


def set_image(recipe, filename):
    with open(IMAGES_DIR / filename, 'rb') as file:
        recipe.image.save(filename, File(file), save=True)


class Command(BaseCommand):
    help = 'Создаёт тестовых пользователей (admin/обычные) и рецепты с фото.'

    def handle(self, *args, **options):
        users = []
        for username, email, first, last, is_staff in USERS:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'username': username, 'first_name': first,
                          'last_name': last, 'is_staff': is_staff,
                          'is_superuser': is_staff})
            if created:
                user.set_password(PASSWORD)
                user.save()
            users.append(user)

        for user, (name, text, time, image, items) in zip(users, RECIPES):
            recipe = Recipe.objects.filter(author=user, name=name).first()
            if recipe:
                # Заменяем старую однотонную заглушку на фото блюда.
                if Path(recipe.image.name).stem.startswith('test'):
                    recipe.image.delete(save=False)
                    set_image(recipe, image)
                continue
            recipe = Recipe(
                author=user, name=name, text=text, cooking_time=time)
            set_image(recipe, image)
            for ingredient_name, amount in items:
                ingredient = Ingredient.objects.filter(
                    name__istartswith=ingredient_name).first()
                if ingredient:
                    RecipeIngredient.objects.get_or_create(
                        recipe=recipe, ingredient=ingredient,
                        defaults={'amount': amount})
        self.stdout.write(self.style.SUCCESS(
            f'Тестовые данные загружены. Пароль у всех: {PASSWORD}'))

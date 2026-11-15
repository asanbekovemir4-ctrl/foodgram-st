import io
import random

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image

from recipes.models import Ingredient, Recipe, RecipeIngredient

User = get_user_model()

USERS = (
    # (username, email, first_name, last_name, is_staff)
    ('admin', 'admin@foodgram.ru', 'Админ', 'Админов', True),
    ('chef', 'chef@foodgram.ru', 'Иван', 'Поваров', False),
    ('cook', 'cook@foodgram.ru', 'Мария', 'Кулинарова', False),
)
PASSWORD = 'Foodgram2025!'

RECIPES = (
    ('Блины на молоке', 'Смешать всё, жарить на сковороде.', 30,
     (('молоко', 500), ('мука пшеничная', 200), ('яйца куриные', 2))),
    ('Омлет', 'Взбить яйца с молоком и запечь.', 15,
     (('яйца куриные', 3), ('молоко', 100))),
    ('Гречка с маслом', 'Отварить гречку, добавить масло.', 25,
     (('гречневая крупа', 200), ('сливочное масло', 30))),
)


def make_image(color):
    buffer = io.BytesIO()
    Image.new('RGB', (600, 400), color=color).save(buffer, format='PNG')
    return ContentFile(buffer.getvalue(), name='test.png')


class Command(BaseCommand):
    help = 'Создаёт тестовых пользователей (admin/обычные) и рецепты.'

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

        for user, (name, text, time, items) in zip(users, RECIPES):
            if Recipe.objects.filter(author=user, name=name).exists():
                continue
            recipe = Recipe.objects.create(
                author=user, name=name, text=text, cooking_time=time,
                image=make_image(tuple(random.randint(80, 220)
                                       for _ in range(3))))
            for ingredient_name, amount in items:
                ingredient = Ingredient.objects.filter(
                    name__istartswith=ingredient_name).first()
                if ingredient:
                    RecipeIngredient.objects.get_or_create(
                        recipe=recipe, ingredient=ingredient,
                        defaults={'amount': amount})
        self.stdout.write(self.style.SUCCESS(
            f'Тестовые данные загружены. Пароль у всех: {PASSWORD}'))

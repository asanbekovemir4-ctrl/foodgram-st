from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserCreateSerializer as BaseUserCreate
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers

from recipes.constants import MIN_AMOUNT, MIN_COOKING_TIME
from recipes.models import Ingredient, Recipe, RecipeIngredient
from .fields import Base64ImageField

User = get_user_model()


# ---------- Пользователи ----------

class UserCreateSerializer(BaseUserCreate):

    class Meta(BaseUserCreate.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'password')


class UserSerializer(BaseUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(read_only=True)

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'avatar')

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and request.user.subscriptions.filter(author=author).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Короткая карточка рецепта (избранное, покупки, подписки)."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, author):
        recipes = author.recipes.all()
        limit = self.context['request'].query_params.get('recipes_limit')
        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]
        return RecipeMinifiedSerializer(
            recipes, many=True, context=self.context).data


# ---------- Ингредиенты и рецепты ----------

class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_AMOUNT)


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source='recipe_ingredients', many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    def _check_relation(self, recipe, related_name):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and getattr(recipe, related_name).filter(
                user=request.user).exists()
        )

    def get_is_favorited(self, recipe):
        return self._check_relation(recipe, 'favorites')

    def get_is_in_shopping_cart(self, recipe):
        return self._check_relation(recipe, 'shopping_carts')


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'image', 'name', 'text',
                  'cooking_time')

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Нужно указать хотя бы один ингредиент.')
        ids = [item['id'].id for item in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.')
        return ingredients

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError('Нужна картинка.')
        return image

    def validate(self, attrs):
        # При PATCH поле ingredients тоже обязательно (по спецификации).
        if 'ingredients' not in attrs:
            raise serializers.ValidationError(
                {'ingredients': 'Обязательное поле.'})
        return attrs

    @staticmethod
    def _save_ingredients(recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount'],
            ) for item in ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self._save_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe.recipe_ingredients.all().delete()
        self._save_ingredients(recipe, ingredients)
        return super().update(recipe, validated_data)

    def to_representation(self, recipe):
        return RecipeReadSerializer(recipe, context=self.context).data

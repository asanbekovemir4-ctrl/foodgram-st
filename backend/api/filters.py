from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe


class IngredientFilter(filters.FilterSet):
    """Поиск ингредиента по началу названия без учёта регистра."""

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'is_favorited', 'is_in_shopping_cart')

    def _filter_by_user_relation(self, queryset, related_name, value):
        user = self.request.user
        if not value:
            return queryset
        if user.is_anonymous:
            return queryset.none()
        return queryset.filter(**{f'{related_name}__user': user})

    def filter_is_favorited(self, queryset, name, value):
        return self._filter_by_user_relation(queryset, 'favorites', value)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        return self._filter_by_user_relation(
            queryset, 'shopping_carts', value)

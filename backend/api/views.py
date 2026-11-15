from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart)
from users.models import Subscription
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, IngredientSerializer,
                          RecipeMinifiedSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer, UserWithRecipesSerializer)

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    """Пользователи (на базе Djoser) + аватар и подписки."""

    @action(
        detail=False, methods=('get',),
        permission_classes=(permissions.IsAuthenticated,))
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        detail=False, methods=('put',), url_path='me/avatar',
        permission_classes=(permissions.IsAuthenticated,))
    def avatar(self, request):
        serializer = AvatarSerializer(
            request.user, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=('get',),
        permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request):
        authors = User.objects.filter(subscribers__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = UserWithRecipesSerializer(
            page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True, methods=('post',),
        permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, pk=id)
        if author == request.user:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST)
        _, created = Subscription.objects.get_or_create(
            user=request.user, author=author)
        if not created:
            return Response(
                {'errors': f'Вы уже подписаны на {author.username}.'},
                status=status.HTTP_400_BAD_REQUEST)
        serializer = UserWithRecipesSerializer(
            author, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        author = get_object_or_404(User, pk=id)
        deleted, _ = Subscription.objects.filter(
            user=request.user, author=author).delete()
        if not deleted:
            return Response(
                {'errors': 'Вы не были подписаны на этого автора.'},
                status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'recipe_ingredients__ingredient')
    permission_classes = (IsAuthorOrReadOnly,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    # --- общие методы для «Избранного» и «Списка покупок» ---

    def _add_relation(self, model, pk, error_text):
        recipe = get_object_or_404(Recipe, pk=pk)
        _, created = model.objects.get_or_create(
            user=self.request.user, recipe=recipe)
        if not created:
            return Response(
                {'errors': error_text}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            RecipeMinifiedSerializer(
                recipe, context={'request': self.request}).data,
            status=status.HTTP_201_CREATED)

    def _remove_relation(self, model, pk, error_text):
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted, _ = model.objects.filter(
            user=self.request.user, recipe=recipe).delete()
        if not deleted:
            return Response(
                {'errors': error_text}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=('post',),
        permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, pk=None):
        return self._add_relation(Favorite, pk, 'Рецепт уже в избранном.')

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        return self._remove_relation(Favorite, pk, 'Рецепта нет в избранном.')

    @action(
        detail=True, methods=('post',),
        permission_classes=(permissions.IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        return self._add_relation(
            ShoppingCart, pk, 'Рецепт уже в списке покупок.')

    @shopping_cart.mapping.delete
    def remove_shopping_cart(self, request, pk=None):
        return self._remove_relation(
            ShoppingCart, pk, 'Рецепта нет в списке покупок.')

    @action(
        detail=False, methods=('get',),
        permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_carts__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total=Sum('amount'))
            .order_by('ingredient__name')
        )
        lines = ['Список покупок «Фудграм»', '']
        lines += [
            f'{number}. {item["ingredient__name"].capitalize()} '
            f'({item["ingredient__measurement_unit"]}) — {item["total"]}'
            for number, item in enumerate(ingredients, start=1)
        ]
        response = HttpResponse(
            '\n'.join(lines), content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"')
        return response

    @action(detail=True, methods=('get',), url_path='get-link',
            permission_classes=(permissions.AllowAny,))
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        url = request.build_absolute_uri(
            reverse('short-link', args=(format(recipe.pk, 'x'),)))
        return Response({'short-link': url})

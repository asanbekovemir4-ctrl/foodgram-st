from django.shortcuts import get_object_or_404, redirect

from .models import Recipe


def short_link_redirect(request, code):
    """Перенаправляет короткую ссылку /s/<код>/ на страницу рецепта."""
    try:
        recipe_id = int(code, 16)
    except ValueError:
        recipe_id = None
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    return redirect(f'/recipes/{recipe.pk}/')

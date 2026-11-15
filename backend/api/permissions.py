from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """Читать могут все, создавать — авторизованные, менять — только автор."""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )


class IsCurrentUserOrReadOnly(permissions.BasePermission):
    """Профиль смотреть могут все, менять — только сам пользователь."""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj == request.user
        )

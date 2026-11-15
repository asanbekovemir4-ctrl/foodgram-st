from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """Стандартная постраничная пагинация, размер страницы — ?limit=."""

    page_size_query_param = 'limit'

import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Картинка, переданная строкой вида data:image/png;base64,<данные>."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            header, imgstr = data.split(';base64,')
            ext = header.split('/')[-1]
            try:
                decoded = base64.b64decode(imgstr)
            except (TypeError, ValueError):
                raise serializers.ValidationError('Некорректная картинка.')
            data = ContentFile(decoded, name=f'{uuid.uuid4().hex}.{ext}')
        return super().to_internal_value(data)

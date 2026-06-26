from rest_framework import serializers
from products.models import Product


class SuggestSerializer(serializers.Serializer):
    """Serializer for autocomplete suggestions"""
    id = serializers.IntegerField()
    title = serializers.CharField()

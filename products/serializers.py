from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'price', 'category', 'category_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing products"""
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'title', 'price', 'category_name']


class ProductSearchSerializer(serializers.ModelSerializer):
    """Serializer for product search with optional inventory info"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    inventory_quantity = serializers.SerializerMethodField()

    def get_inventory_quantity(self, obj):
        request = self.context.get('request')
        store_id = request.query_params.get('store_id') if request else None
        if store_id:
            try:
                inventory = obj.inventory.get(store_id=store_id)
                return inventory.quantity
            except:
                return 0
        return None

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'price', 'category_name', 'inventory_quantity']

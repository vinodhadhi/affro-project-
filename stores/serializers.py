from rest_framework import serializers
from .models import Store, Inventory
from products.models import Product


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ['id', 'name', 'location', 'created_at']
        read_only_fields = ['id', 'created_at']


class InventoryItemSerializer(serializers.ModelSerializer):
    """Serializer for inventory listing endpoint"""
    product_title = serializers.CharField(source='product.title', read_only=True)
    price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    category_name = serializers.CharField(source='product.category.name', read_only=True)

    class Meta:
        model = Inventory
        fields = ['id', 'product_title', 'price', 'category_name', 'quantity']
        read_only_fields = ['id', 'product_title', 'price', 'category_name', 'quantity']


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['id', 'store', 'product', 'quantity', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class StoreDetailSerializer(serializers.ModelSerializer):
    """Detailed store serializer with inventory counts"""
    inventory_count = serializers.SerializerMethodField()

    def get_inventory_count(self, obj):
        return obj.inventory.filter(quantity__gt=0).count()

    class Meta:
        model = Store
        fields = ['id', 'name', 'location', 'created_at', 'inventory_count']
        read_only_fields = ['id', 'created_at']

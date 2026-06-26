from rest_framework import serializers
from django.db.models import Sum
from .models import Order, OrderItem
from products.serializers import ProductListSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity_requested']
        read_only_fields = ['id']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'store', 'status', 'created_at', 'updated_at', 'items']
        read_only_fields = ['id', 'status', 'created_at', 'updated_at', 'items']


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating orders"""
    store_id = serializers.IntegerField()
    items = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),
            allow_empty=False
        )
    )

    def validate_items(self, value):
        """Validate items format"""
        if not value:
            raise serializers.ValidationError("At least one item is required")
        for item in value:
            if 'product_id' not in item or 'quantity_requested' not in item:
                raise serializers.ValidationError(
                    "Each item must have 'product_id' and 'quantity_requested'"
                )
            if item['quantity_requested'] <= 0:
                raise serializers.ValidationError(
                    "Quantity must be greater than 0"
                )
        return value


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer for listing orders"""
    total_items = serializers.SerializerMethodField()

    def get_total_items(self, obj):
        return obj.items.aggregate(total=Sum('quantity_requested'))['total'] or 0

    class Meta:
        model = Order
        fields = ['id', 'status', 'created_at', 'total_items']
        read_only_fields = ['id', 'status', 'created_at', 'total_items']


class OrderDetailSerializer(serializers.ModelSerializer):
    """Detailed order serializer"""
    items = OrderItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()

    def get_total_items(self, obj):
        return obj.items.count()

    class Meta:
        model = Order
        fields = ['id', 'store', 'status', 'created_at', 'updated_at', 'total_items', 'items']
        read_only_fields = ['id', 'store', 'status', 'created_at', 'updated_at', 'items']

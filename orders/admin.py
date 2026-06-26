from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity_requested']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'store', 'status', 'created_at', 'item_count']
    search_fields = ['store__name', 'id']
    list_filter = ['status', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OrderItemInline]

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'quantity_requested']
    search_fields = ['order__id', 'product__title']
    list_filter = ['order__status']
    readonly_fields = ['order', 'product', 'quantity_requested']
    can_delete = False

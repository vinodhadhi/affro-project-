from django.contrib import admin
from .models import Store, Inventory


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'location', 'created_at']
    search_fields = ['name', 'location']
    readonly_fields = ['created_at']


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'store', 'product', 'quantity', 'updated_at']
    search_fields = ['store__name', 'product__title']
    list_filter = ['store', 'updated_at']
    readonly_fields = ['updated_at']

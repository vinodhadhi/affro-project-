from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import F
from .models import Store, Inventory
from .serializers import StoreSerializer, StoreDetailSerializer, InventoryItemSerializer


class StoreViewSet(viewsets.ModelViewSet):
    """ViewSet for Store model"""
    queryset = Store.objects.all()
    serializer_class = StoreSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StoreDetailSerializer
        return StoreSerializer


@api_view(['GET'])
def inventory_listing(request, store_id):
    """
    Inventory Listing API
    Returns inventory items for a specific store
    Includes: product title, price, category name, quantity
    Sorted alphabetically by product title
    """
    try:
        store = Store.objects.get(id=store_id)
    except Store.DoesNotExist:
        return Response({
            'error': 'Store not found'
        }, status=status.HTTP_404_NOT_FOUND)

    # Get inventory items sorted by product title
    inventory_items = Inventory.objects.filter(
        store_id=store_id
    ).select_related('product', 'product__category').order_by('product__title')

    serializer = InventoryItemSerializer(inventory_items, many=True)

    return Response({
        'store_id': store_id,
        'store_name': store.name,
        'location': store.location,
        'inventory': serializer.data,
        'total_items': len(serializer.data)
    })

from django.db import transaction
from django.db.models import Count, F, Sum
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Order, OrderItem
from stores.models import Store, Inventory
from products.models import Product
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    OrderItemSerializer
)
from project.tasks import send_order_confirmation


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Order model"""
    queryset = Order.objects.prefetch_related('items').all()
    serializer_class = OrderSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'list':
            return OrderListSerializer
        elif self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        return create_order_response(request)


@api_view(['POST'])
def create_order(request):
    """
    Order Creation API
    POST /orders/
    
    Input:
    {
        "store_id": 1,
        "items": [
            {"product_id": 1, "quantity_requested": 5},
            {"product_id": 2, "quantity_requested": 3}
        ]
    }
    
    Rules:
    1. Validate product availability for the requested store
    2. If any product has insufficient stock:
       - Order created with REJECTED status
       - No stock deducted
    3. If all items have sufficient stock:
       - Deduct quantities
       - Mark order as CONFIRMED
    4. Use transaction.atomic() to guarantee consistency
    """
    return create_order_response(request)


def create_order_response(request):
    serializer = OrderCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    store_id = serializer.validated_data['store_id']
    items_data = serializer.validated_data['items']

    # Validate store exists
    try:
        store = Store.objects.get(id=store_id)
    except Store.DoesNotExist:
        return Response({
            'error': 'Store not found'
        }, status=status.HTTP_404_NOT_FOUND)

    # Start transaction
    with transaction.atomic():
        # Check product availability
        all_available = True
        inventory_checks = {}

        for item in items_data:
            product_id = item['product_id']
            quantity_requested = item['quantity_requested']

            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response({
                    'error': f'Product {product_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)

            try:
                inventory = Inventory.objects.get(store_id=store_id, product_id=product_id)
                inventory_checks[product_id] = {
                    'inventory': inventory,
                    'requested': quantity_requested,
                    'available': inventory.quantity
                }

                if inventory.quantity < quantity_requested:
                    all_available = False
            except Inventory.DoesNotExist:
                # No inventory record means 0 stock
                inventory_checks[product_id] = {
                    'inventory': None,
                    'requested': quantity_requested,
                    'available': 0
                }
                all_available = False

        # Create order
        order_status = 'CONFIRMED' if all_available else 'REJECTED'
        order = Order.objects.create(store=store, status=order_status)

        # Create order items
        order_items = []
        for item in items_data:
            product_id = item['product_id']
            product = Product.objects.get(id=product_id)
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity_requested=item['quantity_requested']
            )
            order_items.append(order_item)

        # Deduct inventory if confirmed
        if all_available:
            for item in items_data:
                product_id = item['product_id']
                quantity_requested = item['quantity_requested']
                inventory = inventory_checks[product_id]['inventory']
                inventory.quantity -= quantity_requested
                inventory.save()

        # Trigger async task for order confirmation
        send_order_confirmation.delay(order.id)

    # Prepare response
    order_serializer = OrderDetailSerializer(order)
    response_data = {
        'status': order.status,
        'message': 'Order confirmed' if order_status == 'CONFIRMED' else 'Order rejected - insufficient stock',
        'order': order_serializer.data
    }

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def order_listing(request, store_id):
    """
    Order Listing API
    GET /stores/<store_id>/orders/
    
    Returns:
    - order ID
    - status
    - created_at
    - total number of items
    
    Sorted by newest first
    """
    try:
        store = Store.objects.get(id=store_id)
    except Store.DoesNotExist:
        return Response({
            'error': 'Store not found'
        }, status=status.HTTP_404_NOT_FOUND)

    # Get orders with item counts
    orders = Order.objects.filter(
        store_id=store_id
    ).annotate(
        item_count=Count('items')
    ).order_by('-created_at')

    page = int(request.query_params.get('page', 1))
    page_size = 20
    start = (page - 1) * page_size
    end = start + page_size

    paginated_orders = orders[start:end]
    total_count = orders.count()

    results = []
    for order in paginated_orders:
        results.append({
            'id': order.id,
            'status': order.status,
            'created_at': order.created_at,
            'total_items': order.item_count
        })

    return Response({
        'store_id': store_id,
        'store_name': store.name,
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size,
        'results': results
    })

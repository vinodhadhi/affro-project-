from django.core.cache import cache
from django.db.models import Q, F, Count
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductListSerializer,
    ProductSearchSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Category model"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product model"""
    queryset = Product.objects.select_related('category')
    serializer_class = ProductSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer


@api_view(['GET'])
def search_products(request):
    """
    Product Search API with keyword and filters
    Query params:
    - q: keyword search
    - category: category id or name
    - price_min, price_max: price range
    - store_id: store id (includes inventory quantity)
    - in_stock: true/false
    - sort: price, newest, relevance (default: relevance)
    - page: page number (default: 1)
    """
    # Get search query from cache key
    query = request.query_params.get('q', '').strip()
    category_filter = request.query_params.get('category', '').strip()
    price_min = request.query_params.get('price_min')
    price_max = request.query_params.get('price_max')
    store_id = request.query_params.get('store_id')
    in_stock = request.query_params.get('in_stock', '').lower() == 'true'
    sort_by = request.query_params.get('sort', 'relevance')
    page = int(request.query_params.get('page', 1))

    # Create cache key
    cache_key = f"search:{query}:{category_filter}:{price_min}:{price_max}:{store_id}:{in_stock}:{sort_by}:{page}"
    
    # Try to get from cache
    cached_result = cache.get(cache_key)
    if cached_result:
        return Response(cached_result)

    # Build query
    products = Product.objects.select_related('category').all()

    # Keyword search
    if query:
        products = products.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Category filter
    if category_filter:
        try:
            category_id = int(category_filter)
            products = products.filter(category_id=category_id)
        except ValueError:
            products = products.filter(category__name__icontains=category_filter)

    # Price range filter
    if price_min:
        products = products.filter(price__gte=float(price_min))
    if price_max:
        products = products.filter(price__lte=float(price_max))

    # In stock filter
    if in_stock and store_id:
        products = products.filter(inventory__store_id=store_id, inventory__quantity__gt=0).distinct()

    # Sorting
    if sort_by == 'price':
        products = products.order_by('price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    # relevance is default (no additional ordering)

    # Pagination
    page_size = 20
    start = (page - 1) * page_size
    end = start + page_size
    total_count = products.count()

    paginated_products = products[start:end]

    serializer = ProductSearchSerializer(
        paginated_products,
        many=True,
        context={'request': request}
    )

    response_data = {
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size,
        'results': serializer.data
    }

    # Cache for 5 minutes
    cache.set(cache_key, response_data, 300)

    return Response(response_data)


class SuggestRateThrottle(UserRateThrottle):
    """Rate throttle for autocomplete: 20 requests per minute"""
    scope = 'suggest'
    rate = '20/m'


@api_view(['GET'])
@throttle_classes([SuggestRateThrottle])
def autocomplete_suggest(request):
    """
    Autocomplete API for product titles
    Query params:
    - q: search query (minimum 3 characters)
    Returns up to 10 suggestions
    """
    query = request.query_params.get('q', '').strip()

    # Validate minimum length
    if len(query) < 3:
        return Response({
            'error': 'Minimum 3 characters required'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Create cache key
    cache_key = f"autocomplete:{query}"

    # Try to get from cache
    cached_result = cache.get(cache_key)
    if cached_result:
        return Response({'suggestions': cached_result})

    # Prefix matches (appear first)
    prefix_matches = Product.objects.filter(
        title__istartswith=query
    ).values('id', 'title')[:5]

    # General matches
    general_matches = Product.objects.filter(
        title__icontains=query
    ).exclude(
        title__istartswith=query
    ).values('id', 'title')[:5]

    # Combine results (up to 10 total)
    suggestions_dict = {}
    for item in prefix_matches:
        suggestions_dict[item['id']] = item['title']
    for item in general_matches:
        if item['id'] not in suggestions_dict:
            suggestions_dict[item['id']] = item['title']

    suggestions = [{'id': id, 'title': title} for id, title in suggestions_dict.items()]

    # Cache for 10 minutes
    cache.set(cache_key, suggestions, 600)

    return Response({'suggestions': suggestions})

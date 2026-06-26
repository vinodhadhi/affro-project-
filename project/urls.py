"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from products.views import CategoryViewSet, ProductViewSet, search_products, autocomplete_suggest
from stores.views import StoreViewSet, inventory_listing
from orders.views import OrderViewSet, create_order, order_listing

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'stores', StoreViewSet, basename='store')
router.register(r'orders', OrderViewSet, basename='order')

schema_view = get_schema_view(
    openapi.Info(
        title="Aforro Backend API",
        default_version='v1',
        description="API documentation for products, stores, inventory, orders, search, and autocomplete.",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('swagger<str:format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/', include(router.urls)),
    
    # Order endpoints
    path('api/orders/', create_order, name='create_order'),
    path('api/stores/<int:store_id>/orders/', order_listing, name='order_listing'),
    
    # Store inventory endpoint
    path('api/stores/<int:store_id>/inventory/', inventory_listing, name='inventory_listing'),
    
    # Search endpoints
    path('api/search/products/', search_products, name='search_products'),
    path('api/search/suggest/', autocomplete_suggest, name='autocomplete_suggest'),
    
    # API authentication
    path('api-auth/', include('rest_framework.urls')),
]

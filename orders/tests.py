from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from products.models import Category, Product
from stores.models import Store, Inventory
from orders.models import Order, OrderItem
import json


class OrderCreationTestCase(APITestCase):
    """Test order creation with stock validation"""
    
    def setUp(self):
        """Setup test data"""
        self.client = APIClient()
        
        # Create category
        self.category = Category.objects.create(name='Electronics')
        
        # Create products
        self.product1 = Product.objects.create(
            title='Laptop',
            price=999.99,
            category=self.category
        )
        self.product2 = Product.objects.create(
            title='Mouse',
            price=29.99,
            category=self.category
        )
        
        # Create store
        self.store = Store.objects.create(name='Store 1', location='New York')
        
        # Create inventory
        self.inv1 = Inventory.objects.create(
            store=self.store,
            product=self.product1,
            quantity=10
        )
        self.inv2 = Inventory.objects.create(
            store=self.store,
            product=self.product2,
            quantity=5
        )

    def test_order_creation_with_sufficient_stock(self):
        """Test order creation when all items are in stock"""
        url = reverse('create_order')
        data = {
            'store_id': self.store.id,
            'items': [
                {'product_id': self.product1.id, 'quantity_requested': 2},
                {'product_id': self.product2.id, 'quantity_requested': 1}
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'CONFIRMED')
        self.assertEqual(Order.objects.count(), 1)
        
        # Verify inventory was deducted
        self.inv1.refresh_from_db()
        self.inv2.refresh_from_db()
        self.assertEqual(self.inv1.quantity, 8)
        self.assertEqual(self.inv2.quantity, 4)

    def test_order_creation_with_insufficient_stock(self):
        """Test order creation when items are out of stock"""
        url = reverse('create_order')
        data = {
            'store_id': self.store.id,
            'items': [
                {'product_id': self.product1.id, 'quantity_requested': 15},  # Only 10 available
                {'product_id': self.product2.id, 'quantity_requested': 1}
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'REJECTED')
        self.assertEqual(Order.objects.count(), 1)
        
        # Verify inventory was NOT deducted
        self.inv1.refresh_from_db()
        self.inv2.refresh_from_db()
        self.assertEqual(self.inv1.quantity, 10)
        self.assertEqual(self.inv2.quantity, 5)

    def test_order_creation_invalid_store(self):
        """Test order creation with non-existent store"""
        url = reverse('create_order')
        data = {
            'store_id': 9999,
            'items': [
                {'product_id': self.product1.id, 'quantity_requested': 1}
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_order_listing(self):
        """Test getting orders for a store"""
        # Create an order
        Order.objects.create(store=self.store, status='CONFIRMED')
        
        url = reverse('order_listing', kwargs={'store_id': self.store.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)


class ProductSearchTestCase(APITestCase):
    """Test product search functionality"""
    
    def setUp(self):
        """Setup test data"""
        self.client = APIClient()
        
        self.category = Category.objects.create(name='Electronics')
        self.product1 = Product.objects.create(
            title='Gaming Laptop',
            description='High performance laptop for gaming',
            price=1500.00,
            category=self.category
        )
        self.product2 = Product.objects.create(
            title='Office Laptop',
            description='Lightweight laptop for office work',
            price=800.00,
            category=self.category
        )

    def test_search_by_keyword(self):
        """Test searching products by keyword"""
        url = reverse('search_products')
        response = self.client.get(url, {'q': 'gaming'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Gaming Laptop')

    def test_search_by_price_range(self):
        """Test searching products by price range"""
        url = reverse('search_products')
        response = self.client.get(url, {'price_min': 900, 'price_max': 1600})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['price'], '1500.00')

    def test_autocomplete_minimum_chars(self):
        """Test autocomplete requires minimum 3 characters"""
        url = reverse('autocomplete_suggest')
        response = self.client.get(url, {'q': 'ga'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_autocomplete_valid_query(self):
        """Test autocomplete with valid query"""
        url = reverse('autocomplete_suggest')
        response = self.client.get(url, {'q': 'gam'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['suggestions']) > 0)


class InventoryListingTestCase(APITestCase):
    """Test inventory listing"""
    
    def setUp(self):
        """Setup test data"""
        self.client = APIClient()
        
        self.category = Category.objects.create(name='Electronics')
        self.product1 = Product.objects.create(
            title='Laptop',
            price=999.99,
            category=self.category
        )
        self.product2 = Product.objects.create(
            title='Mouse',
            price=29.99,
            category=self.category
        )
        
        self.store = Store.objects.create(name='Store 1', location='NYC')
        
        Inventory.objects.create(
            store=self.store,
            product=self.product1,
            quantity=10
        )
        Inventory.objects.create(
            store=self.store,
            product=self.product2,
            quantity=50
        )

    def test_inventory_listing(self):
        """Test getting inventory for a store"""
        url = reverse('inventory_listing', kwargs={'store_id': self.store.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['inventory']), 2)
        # Should be sorted by product title
        self.assertEqual(response.data['inventory'][0]['product_title'], 'Laptop')
        self.assertEqual(response.data['inventory'][1]['product_title'], 'Mouse')

    def test_inventory_listing_invalid_store(self):
        """Test inventory listing with invalid store"""
        url = reverse('inventory_listing', kwargs={'store_id': 9999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker
from products.models import Category, Product
from stores.models import Store, Inventory
import random

fake = Faker()


class Command(BaseCommand):
    help = 'Seed database with dummy data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data seed...'))

        with transaction.atomic():
            # Create categories
            self.stdout.write('Creating categories...')
            categories = []
            category_names = [
                'Electronics', 'Clothing', 'Books', 'Home & Garden',
                'Sports', 'Beauty', 'Toys', 'Food & Beverages',
                'Office Supplies', 'Furniture', 'Automotive', 'Pet Supplies'
            ]
            
            for name in category_names:
                cat, created = Category.objects.get_or_create(name=name)
                categories.append(cat)
                if created:
                    self.stdout.write(f'  Created category: {name}')

            # Create stores
            self.stdout.write('Creating stores...')
            stores = []
            for i in range(20):
                store, created = Store.objects.get_or_create(
                    name=f'Store {i+1}',
                    location=fake.city()
                )
                stores.append(store)
                if created:
                    self.stdout.write(f'  Created store: {store.name}')

            # Create products
            self.stdout.write('Creating products...')
            products = []
            for i in range(1000):
                product, created = Product.objects.get_or_create(
                    title=f'{fake.word().capitalize()} {fake.word().capitalize()} {i+1}',
                    defaults={
                        'description': fake.sentence(nb_words=10),
                        'price': round(random.uniform(10, 999), 2),
                        'category': random.choice(categories)
                    }
                )
                products.append(product)
                if (i + 1) % 100 == 0:
                    self.stdout.write(f'  Created {i+1} products...')

            # Create inventory
            self.stdout.write('Creating inventory...')
            inventory_count = 0
            for store in stores:
                # Each store gets at least 300 products
                selected_products = random.sample(products, min(300, len(products)))
                
                for product in selected_products:
                    inventory, created = Inventory.objects.get_or_create(
                        store=store,
                        product=product,
                        defaults={
                            'quantity': random.randint(0, 100)
                        }
                    )
                    if created:
                        inventory_count += 1

            self.stdout.write(self.style.SUCCESS(f'Successfully created inventory records: {inventory_count}'))

        self.stdout.write(self.style.SUCCESS('Data seed completed successfully!'))
        self.stdout.write(f'Categories: {Category.objects.count()}')
        self.stdout.write(f'Products: {Product.objects.count()}')
        self.stdout.write(f'Stores: {Store.objects.count()}')
        self.stdout.write(f'Inventory records: {Inventory.objects.count()}')

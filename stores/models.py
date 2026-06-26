from django.db import models
from products.models import Product


class Store(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'location']

    def __str__(self):
        return f"{self.name} - {self.location}"


class Inventory(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='inventory')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['store', 'product']
        indexes = [
            models.Index(fields=['store', 'product']),
        ]

    def __str__(self):
        return f"{self.store.name} - {self.product.title}: {self.quantity}"

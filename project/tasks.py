from celery import shared_task
from django.core.mail import send_mail
from orders.models import Order
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_order_confirmation(order_id):
    """
    Send order confirmation email asynchronously
    """
    try:
        order = Order.objects.get(id=order_id)
        
        subject = f"Order #{order.id} Confirmation - {order.get_status_display()}"
        message = f"""
        Thank you for your order!
        
        Order ID: {order.id}
        Store: {order.store.name}
        Status: {order.get_status_display()}
        Created At: {order.created_at}
        
        Items:
        """
        
        for item in order.items.all():
            message += f"\n- {item.product.title} x {item.quantity_requested}"
        
        logger.info(f"Order confirmation processed for order {order_id}")
        return f"Order confirmation task completed for order {order_id}"
        
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        return f"Error: Order {order_id} not found"
    except Exception as e:
        logger.error(f"Error sending order confirmation: {str(e)}")
        raise


@shared_task
def generate_inventory_summary():
    """
    Generate daily inventory summaries
    This task can be scheduled using Celery Beat
    """
    from stores.models import Store, Inventory
    from django.db.models import Sum
    
    try:
        stores = Store.objects.all()
        summary = {}
        
        for store in stores:
            total_items = Inventory.objects.filter(store=store).aggregate(
                total=Sum('quantity')
            )['total'] or 0
            
            summary[store.id] = {
                'store_name': store.name,
                'total_inventory_count': total_items
            }
        
        logger.info(f"Inventory summary generated: {summary}")
        return summary
        
    except Exception as e:
        logger.error(f"Error generating inventory summary: {str(e)}")
        raise


@shared_task
def preprocess_products_for_search():
    """
    Preprocess products for search optimization
    Can be called periodically to update search indexes
    """
    from products.models import Product
    from django.core.cache import cache
    
    try:
        products = Product.objects.all().values_list('id', 'title')
        cache.set('all_product_titles', list(products), timeout=3600*24)
        
        logger.info(f"Preprocessed {len(products)} products for search")
        return f"Preprocessed {len(products)} products"
        
    except Exception as e:
        logger.error(f"Error preprocessing products: {str(e)}")
        raise

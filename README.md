# Aforro Backend API

A comprehensive Django REST API backend for managing orders, products, stores, and inventory with Redis caching, Celery async tasks, and Docker containerization.

## Features

- **Product Management**: Full CRUD operations for categories, products
- **Store & Inventory Management**: Manage stores and track inventory across multiple stores
- **Order Processing**: Create, track, and manage orders with stock validation
- **Advanced Search**: Full-text search with filters and sorting
- **Autocomplete API**: Fast product autocomplete with rate limiting (20 requests/min)
- **Caching**: Redis-backed caching for search queries and autocomplete
- **Async Tasks**: Celery integration for order confirmations and inventory summaries
- **Rate Limiting**: Protect APIs from abuse
- **Docker Support**: Complete Docker and Docker Compose setup

## Architecture

```
project/
├── products/          # Product and category management
├── stores/            # Store and inventory management
├── orders/            # Order processing
├── search/            # Search functionality
├── project/           # Main project configuration
│   ├── settings.py    # Django settings
│   ├── celery.py      # Celery configuration
│   ├── tasks.py       # Async tasks
│   └── urls.py        # URL routing
├── Dockerfile         # Docker container configuration
├── docker-compose.yml # Multi-container orchestration
└── requirements.txt   # Python dependencies
```

## Setup Instructions

### Local Development (Without Docker)

1. **Create and activate virtual environment**
   ```bash
   python -m venv virtual
   source virtual/Scripts/activate  # Windows
   # or
   source virtual/bin/activate  # Linux/Mac
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install and run Redis**
   - On Windows: Download from https://github.com/microsoftarchive/redis/releases
   - On Linux/Mac: `brew install redis` or `apt-get install redis-server`
   - Start Redis: `redis-server`

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Seed dummy data**
   ```bash
   python manage.py seed_data
   ```
   This creates:
   - 12+ categories
   - 1000+ products
   - 20+ stores
   - 300+ inventory items per store

6. **Start Django development server**
   ```bash
   python manage.py runserver
   ```

7. **Start Celery worker** (in another terminal)
   ```bash
   celery -A project worker -l info
   ```

### Docker Setup

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **View logs**
   ```bash
   docker-compose logs -f web
   ```

3. **Access the API**
   - API: http://localhost:8000/api/
   - Admin: http://localhost:8000/admin/

4. **Stop containers**
   ```bash
   docker-compose down
   ```

## API Endpoints

### Authentication
- `GET /api-auth/` - DRF authentication

### Categories
- `GET /api/categories/` - List all categories
- `POST /api/categories/` - Create category
- `GET /api/categories/{id}/` - Get category details
- `PUT /api/categories/{id}/` - Update category
- `DELETE /api/categories/{id}/` - Delete category

### Products
- `GET /api/products/` - List all products (paginated)
- `POST /api/products/` - Create product
- `GET /api/products/{id}/` - Get product details
- `PUT /api/products/{id}/` - Update product
- `DELETE /api/products/{id}/` - Delete product

### Stores
- `GET /api/stores/` - List all stores
- `POST /api/stores/` - Create store
- `GET /api/stores/{id}/` - Get store details
- `GET /api/stores/{store_id}/inventory/` - Get store inventory (sorted by product title)
- `GET /api/stores/{store_id}/orders/` - Get store orders (newest first)

### Orders
- `POST /api/orders/` - Create order
  ```json
  {
    "store_id": 1,
    "items": [
      {"product_id": 1, "quantity_requested": 5},
      {"product_id": 2, "quantity_requested": 3}
    ]
  }
  ```
- `GET /api/orders/` - List all orders
- `GET /api/orders/{id}/` - Get order details
- `GET /api/stores/{store_id}/orders/` - List store orders (with pagination)

### Search & Autocomplete
- `GET /api/search/products/` - Search products with filters
  ```
  Query params:
  - q: keyword search
  - category: category id or name
  - price_min, price_max: price range
  - store_id: include inventory for this store
  - in_stock: true/false
  - sort: price, newest, relevance
  - page: page number (default: 1)
  ```
  Example: `/api/search/products/?q=laptop&price_max=1000&sort=price`

- `GET /api/search/suggest/?q=xxx` - Autocomplete (min 3 chars, rate limited to 20/min)
  ```
  Returns: {"suggestions": [{"id": 1, "title": "Product Title"}, ...]}
  ```

## Sample API Requests

### Create a Category
```bash
curl -X POST http://localhost:8000/api/categories/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Electronics"}'
```

### Create a Product
```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Laptop",
    "description": "High performance laptop",
    "price": "999.99",
    "category_id": 1
  }'
```

### Create an Order
```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": 1,
    "items": [
      {"product_id": 1, "quantity_requested": 2},
      {"product_id": 2, "quantity_requested": 1}
    ]
  }'
```

### Search Products
```bash
curl "http://localhost:8000/api/search/products/?q=laptop&price_max=1500&sort=price"
```

### Autocomplete
```bash
curl "http://localhost:8000/api/search/suggest/?q=lap"
```

### Get Store Inventory
```bash
curl "http://localhost:8000/api/stores/1/inventory/"
```

### Get Store Orders
```bash
curl "http://localhost:8000/api/stores/1/orders/?page=1"
```

## Caching & Async Logic

### Redis Caching
- **Search API**: Results cached for 5 minutes
- **Autocomplete API**: Suggestions cached for 10 minutes
- Cache keys invalidated on product/category updates

### Rate Limiting
- **Autocomplete**: 20 requests per minute per user/IP
- **Global**: 100 requests/hour for anonymous users, 1000/hour for authenticated

### Celery Tasks

1. **Order Confirmation** (automatic on order creation)
   ```
   Task: send_order_confirmation(order_id)
   Process: Logs order confirmation details
   ```

2. **Inventory Summary** (can be scheduled)
   ```
   Task: generate_inventory_summary()
   Process: Aggregates inventory across stores
   ```

3. **Search Preprocessing** (optional periodic task)
   ```
   Task: preprocess_products_for_search()
   Process: Updates search indexes
   ```

### Running Celery Worker
```bash
# Local development
celery -A project worker -l info

# Docker
docker-compose up celery
```

### Optional: Celery Beat (Scheduled Tasks)
```bash
# Local
celery -A project beat -l info

# Docker (already included in docker-compose.yml)
docker-compose up celery_beat
```

## Database Consistency

### Transaction Support
- Order creation wrapped in `transaction.atomic()` ensures:
  - All items validated before any stock deduction
  - Either all succeed or all rollback
  - Prevents partial orders and stock inconsistencies

### Indexes
- Product: `title`, `category`
- Order: `store + created_at`, `status`
- Inventory: `store + product` (unique constraint)

## Performance Optimizations

1. **Query Optimization**
   - `select_related()` for foreign keys
   - `prefetch_related()` for reverse relations
   - Database indexes on frequently filtered fields

2. **Caching Strategy**
   - Search results: 5 minutes
   - Autocomplete: 10 minutes
   - Cache invalidation on data changes

3. **Pagination**
   - Page size: 20 items per page
   - Reduces memory usage and response times

4. **Async Processing**
   - Non-blocking order confirmations
   - Background inventory aggregation

## Scalability Considerations

### Current Architecture
- Single Django instance
- Redis for caching and message queue
- PostgreSQL for persistence
- Celery workers for async tasks

### Scaling Recommendations

1. **Horizontal Scaling**
   - Deploy multiple Django instances behind load balancer
   - Use AWS ALB or Nginx reverse proxy
   - Ensure stateless design (✓ - already implemented)

2. **Database Scaling**
   - Add read replicas for search queries
   - Master-slave replication for resilience
   - Connection pooling (PgBouncer)

3. **Caching Layer**
   - Redis Cluster for high availability
   - Cache warming for popular searches
   - CDN for static content

4. **Async Processing**
   - Multiple Celery workers on separate machines
   - Task priority queues
   - Monitoring with Flower

5. **Search Optimization**
   - Elasticsearch for full-text search at scale
   - Denormalized search tables
   - Incremental indexing

### Rate Limiting
Current implementation: Per-user/IP limits (20/min for autocomplete)

Recommendations:
- Token bucket algorithm for precise control
- Redis-backed distributed rate limiting
- Different tiers for different endpoints

## Testing

Run tests:
```bash
python manage.py test
```

### Test Coverage
- Model creation and relationships
- Order creation with stock validation
- Search and autocomplete functionality
- Inventory management
- API endpoint responses

## Troubleshooting

### Redis Connection Issues
```bash
# Check if Redis is running
redis-cli ping  # Should return PONG

# Verify Redis configuration in settings.py
REDIS_URL = 'redis://127.0.0.1:6379/1'
```

### Celery Worker Not Processing Tasks
```bash
# Check Celery worker logs
celery -A project worker -l debug

# Verify broker connection
celery -A project inspect active
```

### Database Migration Issues
```bash
# Reset database (development only!)
python manage.py flush

# Reapply migrations
python manage.py migrate
```

## Environment Variables

For production, use `.env` file:
```
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://host:6379/1
CELERY_BROKER_URL=redis://host:6379/0
```

## Security Considerations

1. **CSRF Protection**: Enabled (Django middleware)
2. **SQL Injection**: Protected via ORM parameterized queries
3. **Rate Limiting**: Implemented for sensitive endpoints
4. **Authentication**: DRF token-based (can be enhanced)
5. **CORS**: Configure for production deployment
6. **HTTPS**: Use in production with SSL certificates

## License

This project is part of the Aforro Backend Developer Assignment (Round-2).

## Support

For issues or questions, refer to the assignment documentation or contact the development team.

# VortexServer

An extensible FastAPI-based server with SQLAlchemy, SQLAdmin, DAO pattern, asyncpg, and cache support.

## Features

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy 2.0**: Async ORM with declarative models
- **AsyncPG**: High-performance async PostgreSQL driver
- **SQLAdmin**: Web-based admin interface for database management
- **DAO Pattern**: Data Access Object pattern for clean database operations
- **Redis Cache**: Async caching support with Redis
- **Pydantic Settings**: Type-safe configuration management
- **Extensible Architecture**: Well-structured, modular design

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd VortexServer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start development services:
```bash
docker-compose up -d
```

5. Run the application:
```bash
python -m app.main
```

### Development with Auto-reload

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Project Structure

```
app/
├── __init__.py
├── main.py                 # FastAPI app entry point
├── config/
│   ├── __init__.py
│   └── settings.py         # Pydantic settings
├── models/
│   ├── __init__.py
│   ├── base.py            # Base model classes
│   └── user.py            # Example user model
├── dao/
│   ├── __init__.py
│   └── base.py            # Base DAO pattern
├── api/
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       ├── router.py      # API v1 router
│       └── endpoints/
│           ├── __init__.py
│           └── users.py   # Example user endpoints
├── core/
│   ├── __init__.py
│   ├── database.py        # Database setup
│   └── cache.py           # Cache manager
└── admin/
    ├── __init__.py
    └── views.py           # SQLAdmin views
```

## Usage

### API Endpoints

- **GET** `/` - Root endpoint with API information
- **GET** `/api/v1/health` - Health check
- **GET** `/api/v1/users` - List users
- **GET** `/api/v1/users/{id}` - Get user by ID
- **GET** `/api/v1/users/by-username/{username}` - Get user by username
- **GET** `/api/v1/users/by-email/{email}` - Get user by email
- **POST** `/api/v1/users` - Create user
- **GET** `/docs` - API documentation (Swagger UI)
- **GET** `/admin` - Admin interface

### Adding New Models

1. Create a model in `app/models/`:
```python
from app.models.base import BaseModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

class Product(BaseModel):
    __tablename__ = "products"
    
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[float]
```

2. Import the model in `app/core/database.py`:
```python
from app.models.product import Product  # Add to imports
```

3. Create admin view in `app/admin/views.py`:
```python
class ProductAdmin(ModelView, model=Product):
    column_list = [Product.id, Product.name, Product.price]

# Add to create_admin function:
admin.add_view(ProductAdmin)
```

### Using the DAO Pattern

#### Generic DAO
```python
from app.dao.base import get_dao
from app.models.user import User

# In your endpoint or service
async def get_user_service(user_id: int, session: AsyncSession):
    dao = get_dao(User, session)
    return await dao.get_by_id(user_id)
```

#### Model-specific DAO with Special Methods
```python
from app.dao.user import UserDAO

# In your endpoint or service  
async def get_user_by_username_service(username: str, session: AsyncSession):
    dao = UserDAO(session)
    return await dao.get_by_username(username)

# Other special methods available:
# dao.get_by_email(email)
# dao.search_by_name(pattern) 
# dao.get_users_by_domain(domain)
# dao.username_exists(username)
# dao.email_exists(email)
```

### Using Cache with Endpoints

The user endpoints now include Redis caching with cache-first strategy:

```python
from app.core.cache import cache_manager
from app.core.cache_keys import get_user_cache_key

# Cache is automatically handled in endpoints, but you can use it manually:

# Set cache
await cache_manager.set("key", {"data": "value"}, expire=3600)

# Get cache
data = await cache_manager.get("key")

# Cache keys for users
user_key = get_user_cache_key(123)  # "user:123"
```

## Configuration

All configuration is managed through `app/config/settings.py` using pydantic-settings. You can override settings using environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `DEBUG`: Enable debug mode
- `LOG_LEVEL`: Logging level
- `SECRET_KEY`: Application secret key
- `ADMIN_SECRET_KEY`: Admin interface secret key

## Development

### Running Tests

```bash
pytest
```

### Code Style

The project follows Python best practices and uses type hints throughout.

## License

MIT License
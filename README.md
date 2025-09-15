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

```python
from app.dao.base import get_dao
from app.models.user import User

# In your endpoint or service
async def get_user_service(user_id: int, session: AsyncSession):
    dao = get_dao(User, session)
    return await dao.get_by_id(user_id)
```

### Using Cache

```python
from app.core.cache import cache_manager

# Set cache
await cache_manager.set("key", {"data": "value"}, expire=3600)

# Get cache
data = await cache_manager.get("key")
```

## Configuration

All configuration is managed through `app/config/settings.py` using pydantic-settings. You can override settings using environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `DEBUG`: Enable debug mode
- `LOG_LEVEL`: Logging level
- `SECRET_KEY`: Application secret key
- `ADMIN_SECRET_KEY`: Admin interface secret key

## Database Migrations (Alembic)

Проект использует Alembic для управления схемой БД.

### Инициализация (уже сделано)
Структура находится в каталоге `alembic/`, конфиг — `alembic.ini`.

### Создание новой ревизии
```bash
alembic revision --autogenerate -m "add something"
```

### Применение миграций
```bash
alembic upgrade head
```

### Откат на предыдущую ревизию
```bash
alembic downgrade -1
```

### Важно
- Старый вызов `create_db_and_tables()` можно использовать ТОЛЬКО один раз при чистой БД. Для дальнейших изменений — только миграции.
- При переходе с JSON-поля `cases.gifts` на связь many-to-many была добавлена ассоциативная таблица `case_gifts` и удалён столбец `gifts`.
- Если у вас ещё есть столбец `cases.gifts` и он NOT NULL — выполните: `ALTER TABLE cases DROP COLUMN gifts;` или примените миграцию.

### Troubleshooting
- Если Alembic не видит модели — убедитесь, что они импортированы в `alembic/env.py`.
- Для async URL SQLAlchemy: используйте обычный sync DSN в alembic.ini (без `+asyncpg`).

## Development

### Running Tests

```bash
pytest
```

### Code Style

The project follows Python best practices and uses type hints throughout.

## License

MIT License
# HoneyBiz Backend API

FastAPI backend for the e-commerce candle website.

## Quick Start

### 1. Set up virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up PostgreSQL

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib  # Ubuntu/Debian
# or
brew install postgresql@14  # macOS

# Create database
sudo -u postgres psql
CREATE DATABASE honeybiz;
CREATE USER postgres WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE honeybiz TO postgres;
\q
```

### 4. Configure environment

```bash
# Copy env.example to .env
cp env.example .env

# Edit .env with your configuration
nano .env
```

**Important:** Update these values in `.env`:
- `DATABASE_URL` - Your PostgreSQL connection string
- `SECRET_KEY` - Generate a secure random key (min 32 characters)
- Email settings for notifications
- M-Pesa credentials (for payment integration)

### 5. Run database migrations

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Run migrations
alembic upgrade head
```

### 6. Create admin user

```bash
# Run Python shell
python3

# In Python shell:
from app.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
admin = User(
    email="admin@honeybiz.com",
    password_hash=get_password_hash("admin123"),
    role="admin"
)
db.add(admin)
db.commit()
exit()
```

### 7. Start the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 8. Access the API

- **API Docs:** http://localhost:8000/v1/docs
- **ReDoc:** http://localhost:8000/v1/redoc
- **Health Check:** http://localhost:8000/health

## Project Structure

```
backend/
├── app/
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── api/v1/          # API routes
│   ├── services/        # Business logic
│   ├── core/            # Core utilities (security, etc.)
│   ├── config.py        # Configuration
│   ├── database.py      # Database connection
│   └── main.py          # FastAPI app
├── alembic/             # Database migrations
├── tests/               # Test files
├── requirements.txt     # Python dependencies
└── env.example          # Environment template
```

## API Endpoints

### Public Endpoints
- `GET /v1/products` - Get all products
- `GET /v1/products/{id}` - Get single product
- `POST /v1/products/{id}/reviews` - Submit review
- `POST /v1/orders` - Create order
- `POST /v1/newsletter/subscribe` - Subscribe to newsletter

### Admin Endpoints (require authentication)
- `POST /v1/auth/login` - Admin login
- `POST /v1/products` - Create product
- `PUT /v1/products/{id}` - Update product
- `DELETE /v1/products/{id}` - Delete product
- `GET /v1/analytics/dashboard` - Get analytics

## Documentation

See the parent directory for complete documentation:
- **FASTAPI_SETUP_GUIDE.md** - Detailed setup instructions
- **FASTAPI_ROUTES_EXAMPLES.md** - Complete route implementations
- **FASTAPI_SCHEMAS.md** - Pydantic schema examples
- **BACKEND_DOCUMENTATION.md** - Full API specification
- **DATABASE_SCHEMA.md** - Database setup and schemas

## Development

### Run tests

```bash
pytest tests/ -v
```

### Format code

```bash
black app/
```

### Lint code

```bash
flake8 app/
```

## Production Deployment

### 1. Update environment variables

Set `DEBUG=False` and update all production credentials in `.env`.

### 2. Use production server

```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 3. Set up reverse proxy (Nginx)

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Database connection error
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify DATABASE_URL in `.env`
- Ensure database and user exist

### Import errors
- Activate virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### Migration errors
- Drop and recreate database if needed
- Delete `alembic/versions/*.py` files
- Run `alembic revision --autogenerate -m "Initial"` again

## Support

For questions or issues, refer to the documentation files in the parent directory.

---

**Version:** 1.0.0  
**Last Updated:** January 2026

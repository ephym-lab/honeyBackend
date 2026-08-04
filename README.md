# HoneyBiz Backend API

FastAPI backend for the e-commerce candle website.

## 🚀 Quick Start for Beginners (Docker Edition)

Welcome! We use **Docker** to make running this backend incredibly easy. You won't need to manually install PostgreSQL, Python, or configure complex database settings yourself.

### 1. Install Docker
If you don't have it already, download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/). Make sure it is running before you continue.

### 2. Configure Your Environment Variables
The backend needs some basic settings to run.

1. In the root folder of this project, duplicate the file named `env.example`.
2. Rename the duplicated file to exactly `.env` (don't forget the dot!).
   *(You don't even need to edit the database URL inside it—Docker handles the database connection automatically!)*

### 3. Start the Server
Open your terminal in this project's folder and run:

```bash
docker compose up --build -d
```
*(This command downloads everything needed, sets up the database, and starts the server in the background. It might take a minute or two the first time).*

### 4. Create the Database Tables
Now we tell our newly running backend to create all the necessary tables in the database. 

```bash
docker compose exec app alembic upgrade head
```

### 5. Create Your Admin Account
To log into the admin dashboard later, you'll need an admin account. We have a handy script to do this for you! Run:

```bash
docker compose exec app python create_admin.py
```
*(You should see a message saying "✅ Admin created successfully!")*

### 6. Access the API
You're all set! Open your web browser and go to:
- **Interactive Documentation (Swagger UI):** [http://localhost:8000/v1/docs](http://localhost:8000/v1/docs)  
  *(This is the easiest way to see and test all our API endpoints!)*
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---
**To stop the server later:**
```bash
docker compose down
```

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

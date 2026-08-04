#!/bin/bash
echo "🚀 Starting backend and database..."
docker compose up -d --build

echo "⏳ Waiting for database to be ready (5 seconds)..."
sleep 5

echo "📦 Running database migrations..."
docker compose exec app alembic upgrade head

echo "👤 Creating default admin user..."
docker compose exec app python create_admin.py

echo "✅ Setup complete! Your API is running."
echo "🔗 View the documentation here: http://localhost:8000/v1/docs"

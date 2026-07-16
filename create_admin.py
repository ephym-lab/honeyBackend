from app.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy.exc import IntegrityError

db = SessionLocal()
try:
    admin = User(
        email="admin@honeybiz.com",
        password_hash=get_password_hash("admin123"),
        role="admin"
    )
    db.add(admin)
    db.commit()
    print("Admin user created successfully.")
except IntegrityError:
    db.rollback()
    print("Admin user already exists.")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()

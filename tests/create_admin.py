from app.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def create_admin_user():
    db = SessionLocal()
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.email == "admin@luxcandles.com").first()
        if existing_admin:
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin = User(
            email="admin@luxcandles.com",
            password_hash=get_password_hash("admin123"),
            full_name="Admin User",
            role="admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"✓ Admin user created successfully!")
        print(f"  Email: {admin.email}")
        print(f"  Role: {admin.role}")
        print(f"  ID: {admin.id}")
    except Exception as e:
        db.rollback()
        print(f"✗ Error creating admin user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()

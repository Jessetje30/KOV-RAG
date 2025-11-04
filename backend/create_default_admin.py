#!/usr/bin/env python3
"""
Create Default Admin User - Direct bcrypt implementation
Uses bcrypt directly to avoid passlib compatibility issues.
"""
import sys
import os
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from db.base import SessionLocal, engine, Base
from db.models import UserDB, UserRole
import bcrypt

# Default admin credentials
DEFAULT_ADMIN_EMAIL = "admin@kov-rag.nl"
DEFAULT_ADMIN_PASSWORD = "Admin123!ChangeMe"
DEFAULT_ADMIN_USERNAME = "admin"


def hash_password_direct(password: str) -> str:
    """Hash password using bcrypt directly - no passlib."""
    # Encode password and truncate to 72 bytes
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Return as string (with bcrypt prefix $2b$)
    return hashed.decode('utf-8')


def create_default_admin():
    """Create default admin user."""
    print("\n" + "="*60)
    print("Creating Default Admin User")
    print("="*60 + "\n")

    # Create tables if they don't exist
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database initialized\n")

    db = SessionLocal()
    try:
        # Check if admin already exists
        existing_user = db.query(UserDB).filter(
            UserDB.email == DEFAULT_ADMIN_EMAIL
        ).first()

        if existing_user:
            print(f"✓ Admin user already exists: {DEFAULT_ADMIN_EMAIL}")

            # Make sure they have admin role
            if existing_user.role != UserRole.ADMIN:
                print(f"  Promoting user to admin role...")
                existing_user.role = UserRole.ADMIN
                db.commit()
                print(f"  ✓ User promoted to admin")
            else:
                print(f"  User already has admin role")
        else:
            # Hash password with direct bcrypt
            print(f"Creating new admin user: {DEFAULT_ADMIN_EMAIL}")
            hashed_password = hash_password_direct(DEFAULT_ADMIN_PASSWORD)

            # Create admin user
            admin_user = UserDB(
                username=DEFAULT_ADMIN_USERNAME,
                email=DEFAULT_ADMIN_EMAIL,
                hashed_password=hashed_password,
                role=UserRole.ADMIN,
                is_active=True
            )

            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

            print(f"✓ Admin user created successfully!")

        print("\n" + "="*60)
        print("LOGIN CREDENTIALS")
        print("="*60)
        print(f"Email:    {DEFAULT_ADMIN_EMAIL}")
        print(f"Password: {DEFAULT_ADMIN_PASSWORD}")
        print("="*60)
        print("\n⚠️  IMPORTANT: Change this password after first login!")
        print("="*60 + "\n")

        return True

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error creating admin user: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    try:
        success = create_default_admin()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

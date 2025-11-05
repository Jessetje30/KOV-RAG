#!/usr/bin/env python3
"""
Test login authentication directly.
"""
import sys
sys.path.insert(0, '/app')

from db.base import SessionLocal
from db.crud import UserRepository

def test_login():
    """Test login with admin credentials."""
    db = SessionLocal()

    username = "admin@kov-rag.nl"
    password = "Admin123!ChangeMe"

    print("=" * 60)
    print("TESTING LOGIN")
    print("=" * 60)
    print(f"Username: {username}")
    print(f"Password: {password}")
    print()

    # Try to authenticate
    user = UserRepository.authenticate_user(db, username, password)

    if user:
        print("✅ LOGIN SUCCESSFUL!")
        print(f"   User ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Role: {user.role}")
        print(f"   Active: {user.is_active}")
    else:
        print("❌ LOGIN FAILED!")
        print()

        # Debug: Check if user exists
        user_by_username = UserRepository.get_user_by_username(db, username)
        if user_by_username:
            print(f"✅ User exists: {user_by_username.username}")
            print(f"   Email: {user_by_username.email}")
            print(f"   Active: {user_by_username.is_active}")
            print(f"   Hash: {user_by_username.hashed_password[:30]}...")
            print()

            # Try password verification
            print("Testing password verification...")
            from db.models import truncate_password_for_bcrypt, pwd_context

            password_truncated = truncate_password_for_bcrypt(password)
            print(f"   Password length: {len(password)} bytes")
            print(f"   Truncated length: {len(password_truncated)} bytes")
            print(f"   Truncated password: {password_truncated}")

            try:
                result = pwd_context.verify(password_truncated, user_by_username.hashed_password)
                print(f"   pwd_context.verify() result: {result}")
            except Exception as e:
                print(f"   ❌ Verification error: {str(e)}")
        else:
            print(f"❌ User does not exist: {username}")

    print("=" * 60)
    db.close()

if __name__ == "__main__":
    try:
        test_login()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

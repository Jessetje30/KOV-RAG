#!/usr/bin/env python3
"""
Debug script to check database state.
"""
import sqlite3
import sys

def check_database():
    """Check database schema and users."""
    try:
        conn = sqlite3.connect('/app/rag_app.db')
        cursor = conn.cursor()

        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("❌ Users table does not exist!")
            return

        # Check schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        schema = cursor.fetchone()[0]
        print("=" * 60)
        print("DATABASE SCHEMA")
        print("=" * 60)
        print(schema)
        print()

        # Check if role column exists
        has_role = 'role' in schema.lower()
        print(f"Has 'role' column: {has_role}")
        print()

        # Check users
        print("=" * 60)
        print("USERS IN DATABASE")
        print("=" * 60)

        if has_role:
            cursor.execute('SELECT id, username, email, is_active, role FROM users')
            print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Active':<8} {'Role':<10}")
            print("-" * 60)
            for row in cursor.fetchall():
                print(f"{row[0]:<5} {row[1]:<20} {row[2]:<30} {str(row[3]):<8} {row[4]:<10}")
        else:
            cursor.execute('SELECT id, username, email FROM users')
            print(f"{'ID':<5} {'Username':<20} {'Email':<30}")
            print("-" * 60)
            for row in cursor.fetchall():
                print(f"{row[0]:<5} {row[1]:<20} {row[2]:<30}")

        # Check password hash for admin
        cursor.execute("SELECT username, substr(hashed_password, 1, 10) FROM users WHERE username='admin' OR email='admin@kov-rag.nl'")
        admin = cursor.fetchone()
        if admin:
            print()
            print(f"Admin user found: {admin[0]}, Hash starts with: {admin[1]}...")
        else:
            print()
            print("❌ No admin user found!")

        conn.close()
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    check_database()

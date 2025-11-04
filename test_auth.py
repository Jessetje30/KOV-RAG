"""
Test script for authentication (register and login).
Run this to debug the password issue.
"""
import requests
import json
import sys

BACKEND_URL = "http://localhost:8000"

def test_register(username, email, password):
    """Test user registration."""
    print(f"\n{'='*60}")
    print(f"Testing Registration")
    print(f"{'='*60}")
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Password length (chars): {len(password)}")
    print(f"Password length (bytes): {len(password.encode('utf-8'))}")
    print(f"Password: {password[:20]}..." if len(password) > 20 else f"Password: {password}")

    url = f"{BACKEND_URL}/api/auth/register"
    data = {
        "username": username,
        "email": email,
        "password": password
    }

    try:
        response = requests.post(url, json=data)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 201:
            print("\n✅ Registration successful!")
            return response.json().get("access_token")
        else:
            print("\n❌ Registration failed!")
            return None
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to backend. Is it running?")
        return None
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None


def test_login(username, password):
    """Test user login."""
    print(f"\n{'='*60}")
    print(f"Testing Login")
    print(f"{'='*60}")
    print(f"Username: {username}")
    print(f"Password length (chars): {len(password)}")
    print(f"Password length (bytes): {len(password.encode('utf-8'))}")

    url = f"{BACKEND_URL}/api/auth/login"
    data = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(url, json=data)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            print("\n✅ Login successful!")
            return response.json().get("access_token")
        else:
            print("\n❌ Login failed!")
            return None
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None


def test_me(token):
    """Test getting current user info."""
    print(f"\n{'='*60}")
    print(f"Testing /api/auth/me")
    print(f"{'='*60}")

    url = f"{BACKEND_URL}/api/auth/me"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            print("\n✅ Auth token works!")
            return True
        else:
            print("\n❌ Auth token invalid!")
            return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def main():
    """Run all tests."""
    print(f"\n{'#'*60}")
    print(f"# Authentication Test Script")
    print(f"{'#'*60}")

    # Test with different password lengths
    test_cases = [
        ("testuser1", "test1@example.com", "short123"),  # 8 chars
        ("testuser2", "test2@example.com", "medium_password_123"),  # 21 chars
        ("testuser3", "test3@example.com", "a" * 50),  # 50 chars
        ("testuser4", "test4@example.com", "a" * 72),  # 72 chars (max)
    ]

    for username, email, password in test_cases:
        token = test_register(username, email, password)

        if token:
            # Test login with same credentials
            login_token = test_login(username, password)

            if login_token:
                # Test token validity
                test_me(login_token)

        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    # Check if backend is running
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code == 200:
            print("✅ Backend is running")
            main()
        else:
            print("❌ Backend is not responding correctly")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend at http://localhost:8000")
        print("Please start the backend first:")
        print("  cd backend")
        print("  source venv/bin/activate")
        print("  python main.py")
        sys.exit(1)

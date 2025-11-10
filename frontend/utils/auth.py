"""
Authentication utilities for login, logout, and session management.
"""
import streamlit as st
from services.api_client import api_request


def login(username: str, password: str, cookies) -> bool:
    """
    Login user and store token.

    Args:
        username: Username to login with
        password: Password to login with
        cookies: Cookie manager instance

    Returns:
        True if login successful, False otherwise
    """
    response = api_request(
        "/api/auth/login",
        method="POST",
        data={"username": username, "password": password}
    )

    if response:
        st.session_state.token = response["access_token"]
        # Save token to cookie for persistent login
        cookies['auth_token'] = response["access_token"]
        cookies.save()

        # Get user info (don't silence errors here as user actively tried to login)
        user_info = api_request("/api/auth/me", auth=True, silent_auth_errors=False)
        if user_info:
            st.session_state.user = user_info
            return True

    return False


def logout(cookies):
    """
    Logout user and clear session.

    Args:
        cookies: Cookie manager instance
    """
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.page = 'login'
    # Clear cookie
    cookies['auth_token'] = ''
    cookies.save()


def initialize_session(cookies):
    """
    Initialize session state with cookie support.

    Args:
        cookies: Cookie manager instance
    """
    # Session state initialization with cookie support
    if 'token' not in st.session_state:
        # Try to load token from cookie
        token_from_cookie = cookies.get('auth_token', None)
        # Only use token if it's not empty and appears to be a valid JWT format
        # JWT tokens have 3 parts separated by dots
        if token_from_cookie and isinstance(token_from_cookie, str) and len(token_from_cookie.strip()) > 0:
            # Basic JWT format validation (should have at least 2 dots)
            if token_from_cookie.count('.') >= 2:
                st.session_state.token = token_from_cookie
            else:
                # Invalid format, clear it
                st.session_state.token = None
                cookies['auth_token'] = ''
                cookies.save()
        else:
            st.session_state.token = None

    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'page' not in st.session_state:
        st.session_state.page = 'login'

    # If we have a token from cookie but no user info, fetch user info
    # Only attempt this if we have a valid-looking token
    if st.session_state.token and not st.session_state.user:
        user_info = api_request("/api/auth/me", auth=True, silent_auth_errors=True)
        if user_info:
            st.session_state.user = user_info
            st.session_state.page = 'main'
        else:
            # Token is invalid or expired, clear it silently
            st.session_state.token = None
            st.session_state.user = None
            st.session_state.page = 'login'
            cookies['auth_token'] = ''
            cookies.save()

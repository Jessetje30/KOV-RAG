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

        # Get user info
        user_info = api_request("/api/auth/me", auth=True)
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
        st.session_state.token = cookies.get('auth_token', None)
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'page' not in st.session_state:
        st.session_state.page = 'login'

    # If we have a token from cookie but no user info, fetch user info
    if st.session_state.token and not st.session_state.user:
        user_info = api_request("/api/auth/me", auth=True)
        if user_info:
            st.session_state.user = user_info
            st.session_state.page = 'main'
        else:
            # Token is invalid, clear it
            st.session_state.token = None
            st.session_state.user = None
            st.session_state.page = 'login'
            cookies['auth_token'] = ''
            cookies.save()

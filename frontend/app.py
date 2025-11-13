"""
Streamlit frontend for RAG Application.
Provides user interface for authentication, document management, and querying.
"""
import os
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

# Page configuration - MUST BE ABSOLUTE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="BBL RAG - Kijk op Veiligheid",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Import modules after page config
from assets.styles import apply_custom_styles
from utils.auth import initialize_session
from pages.auth import show_auth_page
from pages.main import show_main_page
from pages.setup_account import show_setup_account_page


# Initialize cookie manager for persistent login
COOKIE_PASSWORD = os.getenv("COOKIE_ENCRYPTION_KEY")
if not COOKIE_PASSWORD:
    raise ValueError(
        "COOKIE_ENCRYPTION_KEY environment variable must be set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )

cookies = EncryptedCookieManager(
    prefix="rag_app_",
    password=COOKIE_PASSWORD
)

if not cookies.ready():
    st.stop()


def main():
    """Main application entry point."""
    # Apply custom CSS and JavaScript
    apply_custom_styles()

    # Initialize session state with cookie support
    initialize_session(cookies)

    # Check for invitation token in query params
    query_params = st.query_params
    invitation_token = query_params.get("token", None)

    # Route to appropriate page
    if invitation_token:
        # Show setup account page for invited users
        show_setup_account_page(cookies)
    elif st.session_state.token is None or st.session_state.user is None:
        # Show login page
        show_auth_page(cookies)
    else:
        # Show main application
        show_main_page(cookies)


if __name__ == "__main__":
    main()

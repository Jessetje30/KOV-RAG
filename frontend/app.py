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
    initial_sidebar_state="expanded"
)

# Import modules after page config
from assets.styles import apply_custom_styles
from utils.auth import initialize_session
from pages.auth import show_auth_page
from pages.main import show_main_page


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

    # Route to appropriate page based on authentication state
    if st.session_state.token is None or st.session_state.user is None:
        show_auth_page(cookies)
    else:
        show_main_page(cookies)


if __name__ == "__main__":
    main()

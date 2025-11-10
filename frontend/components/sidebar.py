"""
Sidebar component for authenticated pages.
Displays user info, navigation, and BBL version info.
"""
import streamlit as st
from api.client import get_api_client
from utils.auth import logout, get_current_user, is_admin


def show_sidebar():
    """
    Display sidebar with user info and BBL metadata.
    Should be called in authenticated pages.
    """
    with st.sidebar:
        # BBL Branding
        st.markdown("## BBL RAG")
        st.markdown("**Kijk op Veiligheid**")
        st.caption("Besluit Bouwwerken Leefomgeving")

        st.markdown("---")

        # User info
        user = get_current_user()
        if user:
            st.markdown(f"### Welkom, {user['username']}!")
            st.markdown(f"**Email:** {user['email']}")

            # Show admin badge
            if user.get("role") == "admin":
                st.markdown("**Administrator**")

        st.markdown("---")

        # Logout button
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()

        st.markdown("---")

        # BBL version info (dynamic)
        _show_bbl_info()


def _show_bbl_info():
    """Display BBL version and document count."""
    api = get_api_client()
    documents_response = api.get_documents()

    if documents_response:
        bbl_docs = [
            doc for doc in documents_response.get("documents", []) if doc["document_id"].startswith("BBL_")
        ]
        doc_count = len(bbl_docs)

        if doc_count > 0:
            st.info(f"**BBL Database**\n\n{doc_count} artikelen beschikbaar")
        else:
            st.warning("**Geen BBL documenten**\n\nUpload BBL documenten via het Admin Panel")
    else:
        st.warning("**Kan documenten niet laden**")

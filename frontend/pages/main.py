"""
Main application page with sidebar navigation.
"""
import streamlit as st
from services.api_client import api_request
from utils.auth import logout
from utils.document_helpers import get_bbl_document_count
from pages.query import show_query_page
from pages.documents import show_manage_documents_page
from pages.admin import show_admin_panel
from components.footer import show_footer


def show_main_page(cookies):
    """
    Display main application page.

    Args:
        cookies: Cookie manager instance
    """
    # Auto-expand sidebar on main page
    st.markdown("""
    <script>
    setTimeout(function() {
        const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
        if (sidebar && sidebar.getAttribute('aria-expanded') === 'false') {
            const collapseButton = window.parent.document.querySelector('[data-testid="stSidebarCollapseButton"] button');
            if (collapseButton) {
                collapseButton.click();
            }
        }
    }, 100);
    </script>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        # BBL Branding
        st.markdown("## BBL RAG")
        st.markdown("**Kijk op Veiligheid**")
        st.caption("Besluit Bouwwerken Leefomgeving")

        st.markdown("---")

        st.markdown(f"### Welkom, {st.session_state.user['username']}!")
        st.markdown(f"**Email:** {st.session_state.user['email']}")

        # Show admin badge
        if st.session_state.user.get('role') == 'admin':
            st.markdown("**Administrator**")

        st.markdown("---")

        # Navigation - add Admin Panel for admins
        nav_options = ["BBL Vragen Stellen", "BBL Documenten"]
        if st.session_state.user.get('role') == 'admin':
            nav_options.append("Admin Panel")

        page = st.radio(
            "Navigation",
            nav_options,
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Info over BBL documenten (dynamisch)
        documents_response = api_request("/api/documents", auth=True)
        if documents_response:
            doc_count = get_bbl_document_count(documents_response)
            if doc_count > 0:
                st.info(f"**BBL Database**\n\n{doc_count} artikelen beschikbaar")
            else:
                st.warning("**Geen BBL documenten**\n\nUpload BBL documenten via het Admin Panel")
        else:
            st.warning("**Kan documenten niet laden**")

        st.markdown("---")

        if st.button("Logout", use_container_width=True):
            logout(cookies)
            st.rerun()

    # Main content
    if page == "BBL Vragen Stellen":
        show_query_page()
    elif page == "BBL Documenten":
        show_manage_documents_page()
    elif page == "Admin Panel":
        show_admin_panel()

    # Footer with version info
    show_footer()

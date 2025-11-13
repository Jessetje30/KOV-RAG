"""
Footer component with version information.
"""
import streamlit as st
from version import VERSION, VERSION_NAME, RELEASE_DATE


def show_footer():
    """Display application footer with version information."""
    st.markdown("---")
    st.markdown(
        f"""
        <div style="text-align: center; color: #666; font-size: 0.85em; padding: 20px 0 10px 0;">
            <strong>KOV-RAG</strong> v{VERSION} "{VERSION_NAME}" | Release: {RELEASE_DATE}<br>
            <span style="font-size: 0.9em;">Kijk op Veiligheid - BBL RAG System</span>
        </div>
        """,
        unsafe_allow_html=True
    )

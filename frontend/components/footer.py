"""
Footer component with version information.
"""
import streamlit as st
from version import VERSION, VERSION_NAME, RELEASE_DATE, GIT_COMMIT, GIT_BRANCH


def show_footer():
    """Display application footer with version information."""
    st.markdown("---")

    # Shorten branch name if it's long (claude branches)
    branch_display = GIT_BRANCH
    if len(branch_display) > 40:
        # Show first 20 and last 15 chars for claude branches
        branch_display = f"{branch_display[:20]}...{branch_display[-15:]}"

    st.markdown(
        f"""
        <div style="text-align: center; color: #666; font-size: 0.85em; padding: 20px 0 10px 0;">
            <strong>KOV-RAG</strong> v{VERSION} "{VERSION_NAME}" | Release: {RELEASE_DATE}<br>
            <span style="font-size: 0.85em; color: #888;">
                Git: <code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">{GIT_COMMIT}</code>
                on <strong>{branch_display}</strong>
            </span><br>
            <span style="font-size: 0.8em;">Kijk op Veiligheid - BBL RAG System</span>
        </div>
        """,
        unsafe_allow_html=True
    )

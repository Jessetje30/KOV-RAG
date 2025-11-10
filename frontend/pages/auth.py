"""
Authentication page for login.
"""
import streamlit as st
from utils.auth import login


def show_auth_page(cookies):
    """
    Display authentication page.

    Args:
        cookies: Cookie manager instance
    """
    st.markdown('<div class="main-header">BBL RAG</div>', unsafe_allow_html=True)
    st.markdown("### Kijk op Veiligheid - Besluit Bouwwerken Leefomgeving")
    st.markdown("*Stel vragen over het BBL en krijg direct antwoord met artikelverwijzingen*")

    st.subheader("Login to Your Account")

    # Info message about invitation-based access
    st.info("**Nieuwe gebruikers**: Accounts worden aangemaakt via uitnodiging. Neem contact op met een administrator voor toegang.")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                with st.spinner("Logging in..."):
                    if login(username, password, cookies):
                        st.success("Login successful!")
                        st.session_state.page = 'main'
                        st.rerun()
                    else:
                        st.error("Login failed. Please check your credentials.")

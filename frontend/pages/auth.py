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
    # Flexbox centered login
    st.markdown("""
        <div class="jcc" style="min-height: 60vh;">
            <div style="max-width: 400px; text-align: center;">
                <div style="font-size: 2rem; font-weight: 700; color: #FF6B35; margin-bottom: 0.5rem;">
                    BBL RAG
                </div>
                <div style="font-size: 1rem; font-weight: 600; color: #3F3F46; margin-bottom: 0.25rem;">
                    Kijk op Veiligheid
                </div>
                <div style="font-size: 0.875rem; color: #71717A; margin-bottom: 2rem;">
                    Besluit Bouwwerken Leefomgeving
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Flexbox centered form container
    st.markdown('<div class="jcc">', unsafe_allow_html=True)
    st.markdown('<div style="width: 400px; max-width: 90vw;">', unsafe_allow_html=True)

    st.markdown('<div style="margin-bottom: 1rem; text-align: center;"><strong>Inloggen</strong></div>', unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Gebruikersnaam", label_visibility="collapsed", placeholder="Gebruikersnaam")
        password = st.text_input("Wachtwoord", type="password", label_visibility="collapsed", placeholder="Wachtwoord")
        submit = st.form_submit_button("Inloggen", use_container_width=True)

        if submit:
            if not username or not password:
                st.error("Vul beide velden in")
            else:
                with st.spinner("Inloggen..."):
                    if login(username, password, cookies):
                        st.success("Login succesvol!")
                        st.session_state.page = 'main'
                        st.rerun()
                    else:
                        st.error("Login mislukt. Controleer je gegevens.")

    # Compact info message
    st.markdown("""
        <div style="font-size: 0.75rem; color: #71717A; margin-top: 1rem; text-align: center;">
            <strong>Nieuwe gebruikers?</strong><br>
            Neem contact op met een administrator.
        </div>
    """, unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)

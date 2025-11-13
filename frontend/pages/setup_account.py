"""
Setup Account page for invited users.
Allows users to create their account from an email invitation.
"""
import streamlit as st
from services.api_client import api_request
from components.footer import show_footer


def show_setup_account_page(cookies):
    """
    Display setup account page for invited users.

    Args:
        cookies: Cookie manager instance
    """
    # Check if we have a token in query params
    query_params = st.query_params
    token = query_params.get("token", None)

    if not token:
        st.error("Geen uitnodigingstoken gevonden. Controleer de link in je email.")
        st.info("Als je problemen hebt, neem dan contact op met de administrator die je heeft uitgenodigd.")
        show_footer()
        return

    # Validate the invitation token
    if 'invitation_validated' not in st.session_state:
        with st.spinner("Uitnodiging valideren..."):
            validation_response = api_request(
                f"/api/auth/validate-invitation/{token}",
                method="GET",
                auth=False
            )

            if validation_response and validation_response.get('valid'):
                st.session_state.invitation_validated = True
                st.session_state.invitation_email = validation_response.get('email')
                st.session_state.invitation_token = token
            else:
                st.session_state.invitation_validated = False
                st.session_state.validation_error = validation_response.get('message', 'Onbekende fout') if validation_response else 'Uitnodiging kon niet worden gevalideerd'

    # If validation failed, show error
    if not st.session_state.invitation_validated:
        st.error(f"Uitnodiging ongeldig: {st.session_state.get('validation_error', 'Onbekende fout')}")
        st.info("Mogelijke oorzaken:")
        st.markdown("""
        - De uitnodiging is verlopen (7 dagen geldig)
        - De uitnodiging is al gebruikt
        - De link is ongeldig
        """)
        st.info("Vraag de administrator om een nieuwe uitnodiging te versturen.")
        show_footer()
        return

    # Show setup form
    st.markdown("""
        <div class="jcc" style="min-height: 60vh;">
            <div style="max-width: 400px; text-align: center;">
                <div style="font-size: 2rem; font-weight: 700; color: #FF6B35; margin-bottom: 0.5rem;">
                    Bbl RAG
                </div>
                <div style="font-size: 1rem; font-weight: 600; color: #3F3F46; margin-bottom: 0.25rem;">
                    Kijk op Veiligheid
                </div>
                <div style="font-size: 0.875rem; color: #71717A; margin-bottom: 2rem;">
                    Account Aanmaken
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Flexbox centered form container
    st.markdown('<div class="jcc">', unsafe_allow_html=True)
    st.markdown('<div style="width: 400px; max-width: 90vw;">', unsafe_allow_html=True)

    st.success(f"✅ Uitnodiging geldig voor: **{st.session_state.invitation_email}**")

    st.markdown('<div style="margin-bottom: 1rem; margin-top: 1.5rem; text-align: center;"><strong>Maak je account aan</strong></div>', unsafe_allow_html=True)

    with st.form("setup_account_form"):
        username = st.text_input(
            "Gebruikersnaam",
            label_visibility="collapsed",
            placeholder="Kies een gebruikersnaam",
            max_chars=50,
            help="Kies een unieke gebruikersnaam (minimaal 3 tekens)"
        )

        password = st.text_input(
            "Wachtwoord",
            type="password",
            label_visibility="collapsed",
            placeholder="Kies een wachtwoord",
            max_chars=128,
            help="Minimaal 8 tekens"
        )

        password_confirm = st.text_input(
            "Bevestig Wachtwoord",
            type="password",
            label_visibility="collapsed",
            placeholder="Bevestig je wachtwoord",
            max_chars=128
        )

        submit = st.form_submit_button("Account Aanmaken", use_container_width=True)

        if submit:
            # Validation
            errors = []

            if not username or len(username) < 3:
                errors.append("Gebruikersnaam moet minimaal 3 tekens zijn")

            if not password or len(password) < 8:
                errors.append("Wachtwoord moet minimaal 8 tekens zijn")

            if password != password_confirm:
                errors.append("Wachtwoorden komen niet overeen")

            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Create account
                with st.spinner("Account aanmaken..."):
                    response = api_request(
                        "/api/auth/setup-account",
                        method="POST",
                        data={
                            "token": st.session_state.invitation_token,
                            "username": username,
                            "password": password
                        },
                        auth=False
                    )

                    if response and response.get('success'):
                        # Auto-login
                        st.session_state.token = response.get('access_token')

                        # Get user info
                        user_response = api_request(
                            "/api/auth/me",
                            auth=True
                        )

                        if user_response:
                            st.session_state.user = user_response

                            # Save to cookie
                            cookies['token'] = st.session_state.token
                            cookies['user'] = str(user_response)
                            cookies.save()

                            # Clear invitation state
                            del st.session_state.invitation_validated
                            del st.session_state.invitation_email
                            del st.session_state.invitation_token

                            st.success("✅ Account succesvol aangemaakt! Je wordt doorgestuurd...")
                            st.balloons()

                            # Redirect to main page
                            st.rerun()
                        else:
                            st.error("Account aangemaakt maar inloggen mislukt. Probeer in te loggen op de loginpagina.")
                    else:
                        st.error("Account aanmaken mislukt. Mogelijk is de gebruikersnaam al in gebruik.")

    # Info message
    st.markdown("""
        <div style="font-size: 0.75rem; color: #71717A; margin-top: 1rem; text-align: center;">
            <strong>Al een account?</strong><br>
            <a href="/" style="color: #FF6B35;">Klik hier om in te loggen</a>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)

    # Footer
    show_footer()

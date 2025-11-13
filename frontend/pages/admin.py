"""
Admin panel for user management and Bbl document uploads.
"""
import streamlit as st
from services.api_client import api_request
from utils.security import validate_email, sanitize_html


# Maximum file size in bytes (50 MB)
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024


def show_admin_panel():
    """Display admin panel for user management (admin only)."""
    st.markdown('<div class="main-header">Admin Panel</div>', unsafe_allow_html=True)
    st.markdown("*Beheer gebruikers en verstuur uitnodigingen*")

    # Check if user is admin
    if st.session_state.user.get('role') != 'admin':
        st.error("Toegang geweigerd. Deze pagina is alleen toegankelijk voor administrators.")
        return

    st.markdown("---")

    # Tabs for different admin functions
    tab1, tab2, tab3 = st.tabs(["Gebruiker Uitnodigen", "Gebruikers Beheren", "Bbl Uploaden"])

    with tab1:
        st.subheader("Nieuwe Gebruiker Uitnodigen")
        st.markdown("Stuur een uitnodiging naar een nieuw emailadres. De gebruiker ontvangt een email met een link om hun account aan te maken.")

        with st.form("invite_user_form"):
            email = st.text_input("Email Adres", placeholder="gebruiker@example.com")
            submit = st.form_submit_button("Uitnodiging Versturen", use_container_width=True)

            if submit:
                # Validate email input
                is_valid, error_msg = validate_email(email)
                if not is_valid:
                    st.error(error_msg)
                else:
                    with st.spinner("Uitnodiging versturen..."):
                        response = api_request(
                            "/api/admin/invite-user",
                            method="POST",
                            data={"email": email},
                            auth=True
                        )

                        if response:
                            st.success(f"Uitnodiging verstuurd naar {email}!")
                            st.info(f"De gebruiker kan hun account aanmaken via de link in de email. De uitnodiging verloopt over 7 dagen.")
                        else:
                            st.error("Uitnodiging versturen mislukt. Mogelijk bestaat dit email adres al.")

    with tab2:
        st.subheader("Gebruikers Overzicht")
        st.markdown("Bekijk alle geregistreerde gebruikers en hun status.")

        with st.spinner("Gebruikers laden..."):
            users_response = api_request("/api/admin/users?page=1&page_size=50", auth=True)

        if users_response and 'users' in users_response:
            users = users_response['users']
            total = users_response.get('total', 0)

            st.markdown(f"**Totaal gebruikers:** {total}")
            st.markdown("---")

            if not users:
                st.info("Nog geen gebruikers geregistreerd.")
            else:
                for user in users:
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        # User info
                        status_icon = "[Actief]" if user.get('is_active') else "[Inactief]"
                        role_badge = "Admin" if user.get('role') == 'admin' else "User"
                        st.markdown(f"{status_icon} **{user.get('username')}** ({role_badge})")
                        st.caption(f"Email: {user.get('email')}")

                    with col2:
                        # Status toggle (simplified - would need full implementation)
                        if user.get('is_active'):
                            st.caption("Actief")
                        else:
                            st.caption("Inactief")

                    with col3:
                        # Show ID for reference
                        st.caption(f"ID: {user.get('id')}")

                    st.markdown("---")

    with tab3:
        st.subheader("Bbl Documenten Uploaden")
        st.markdown("Upload PDF, DOCX of TXT bestanden met Bbl artikelen om ze doorzoekbaar te maken.")

        uploaded_file = st.file_uploader(
            "Kies een bestand",
            type=['pdf', 'docx', 'txt', 'xml'],
            help="Upload een document om toe te voegen aan de kennisbank (XML voor Bbl documenten)",
            key="admin_upload"
        )

        if uploaded_file is not None:
            # Display file info
            st.markdown("#### Bestandsinformatie")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Bestandsnaam:** {sanitize_html(uploaded_file.name)}")
            with col2:
                st.write(f"**Grootte:** {uploaded_file.size / 1024:.2f} KB")

            # Validate file size
            if uploaded_file.size > MAX_FILE_SIZE:
                st.error(f"Bestand te groot. Maximaal {MAX_FILE_SIZE_MB} MB toegestaan.")
            elif st.button("Upload en Verwerk", use_container_width=True, key="upload_submit"):
                with st.spinner("Document uploaden en verwerken..."):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}

                    response = api_request(
                        "/api/documents/upload",
                        method="POST",
                        files=files,
                        auth=True
                    )

                    if response:
                        st.success(f"{response['message']}")
                        st.markdown(f"""
                        **Document ID:** {response['document_id']}
                        **Chunks Aangemaakt:** {response['chunks_created']}
                        **Bestandsgrootte:** {response['file_size'] / 1024:.2f} KB
                        """)
                    else:
                        st.error("Upload mislukt. Probeer het opnieuw.")

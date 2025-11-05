"""
Streamlit frontend for RAG Application.
Provides user interface for authentication, document management, and querying.
"""
import os
import streamlit as st

# Page configuration - MUST BE ABSOLUTE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="BBL RAG - Kijk op Veiligheid",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now import other modules (some may use Streamlit internally)
import requests
import html
from datetime import datetime
from typing import Optional, Dict, Any
from streamlit_cookies_manager import EncryptedCookieManager

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

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

# Modern CSS with Tailwind CDN and 2025 styling
st.markdown("""
<!-- Google Fonts - Inter (Modern 2025 font) -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

<!-- Tailwind CSS 4.0 CDN -->
<script src="https://cdn.tailwindcss.com?plugins=forms,typography"></script>
<script>
tailwind.config = {
    theme: {
        extend: {
            colors: {
                primary: {
                    500: '#FF6B35',
                    600: '#E85A2A',
                    700: '#CC4620'
                },
                zinc: {
                    50: '#FAFAFA',
                    100: '#F4F4F5',
                    600: '#52525B',
                    700: '#3F3F46',
                    800: '#27272A',
                    900: '#18181B'
                }
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif']
            }
        }
    }
}
</script>

<style>
    /* Import Inter font */
    * {
        font-family: 'Inter', -apple-system, system-ui, sans-serif !important;
    }

    /* Modern header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
        color: #18181B;
        letter-spacing: -0.02em;
    }

    /* Modern card styling with hover effects */
    .modern-card {
        background: white;
        border: 1px solid #E4E4E7;
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .modern-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transform: translateY(-2px);
    }

    /* Success box - modern green */
    .success-box {
        padding: 1rem 1.25rem;
        border-radius: 0.75rem;
        background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
        border: 1px solid #BBF7D0;
        color: #166534;
        margin: 1rem 0;
        font-weight: 500;
    }

    /* Error box - modern red */
    .error-box {
        padding: 1rem 1.25rem;
        border-radius: 0.75rem;
        background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
        border: 1px solid #FECACA;
        color: #991B1B;
        margin: 1rem 0;
        font-weight: 500;
    }

    /* Info box - modern blue */
    .info-box {
        padding: 1.25rem;
        border-radius: 0.75rem;
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border: 1px solid #BFDBFE;
        color: #1E40AF;
        margin: 1rem 0;
        font-weight: 500;
    }

    /* Source box - modern style with accent */
    .source-box {
        padding: 1.25rem;
        border-radius: 0.875rem;
        background: white;
        border: 1px solid #E4E4E7;
        border-left: 4px solid #FF6B35;
        color: #18181B;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: all 0.2s;
    }

    .source-box:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        border-left-color: #CC4620;
    }

    /* Responsive breakpoints */
    @media (max-width: 640px) {
        .main-header {
            font-size: 2rem;
        }
        .modern-card, .source-box {
            padding: 1rem;
        }
    }

    /* Touch optimization for mobile */
    @media (hover: none) and (pointer: coarse) {
        .modern-card:hover, .source-box:hover {
            transform: none;
        }
    }
</style>

<script>
// Fix tab navigation and enable Enter to submit
document.addEventListener('DOMContentLoaded', function() {
    fixPasswordTabOrder();
    enableEnterToSubmit();
});

setTimeout(function() {
    fixPasswordTabOrder();
    enableEnterToSubmit();
}, 1000);

setTimeout(function() {
    enableEnterToSubmit();
}, 2000);

function fixPasswordTabOrder() {
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        const container = input.closest('div[data-baseweb="input"]') || input.parentElement;
        const buttons = container.querySelectorAll('button');
        buttons.forEach(button => {
            button.setAttribute('tabindex', '-1');
        });
    });
}

function enableEnterToSubmit() {
    const textareas = document.querySelectorAll('form textarea');
    textareas.forEach(textarea => {
        textarea.removeEventListener('keydown', handleEnterKey);
        textarea.addEventListener('keydown', handleEnterKey);
    });
}

function handleEnterKey(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        const form = event.target.closest('form');
        if (form) {
            const submitButton = form.querySelector('button[kind="primary"], button[type="submit"]');
            if (submitButton) {
                submitButton.click();
            }
        }
    }
}

const observer = new MutationObserver(function(mutations) {
    fixPasswordTabOrder();
    enableEnterToSubmit();
});
observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)

# API Helper Functions
def api_request(endpoint: str, method: str = "GET", data: Dict = None, files: Dict = None, auth: bool = False) -> Optional[Dict[str, Any]]:
    """
    Make API request to backend.

    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, DELETE)
        data: Request data (JSON)
        files: Files to upload
        auth: Whether to include authentication token

    Returns:
        Response data or None if error
    """
    url = f"{BACKEND_URL}{endpoint}"
    headers = {}

    if auth and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, files=files)
            else:
                response = requests.post(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            st.error(f"Unsupported HTTP method: {method}")
            return None

        if response.status_code in [200, 201]:
            return response.json()
        else:
            error_detail = response.json().get("detail", "Unknown error")
            st.error(f"Error: {error_detail}")
            return None

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend server. Please ensure the backend is running.")
        return None
    except Exception as e:
        st.error(f"Request failed: {str(e)}")
        return None


def login(username: str, password: str) -> bool:
    """Login user and store token."""
    response = api_request(
        "/api/auth/login",
        method="POST",
        data={"username": username, "password": password}
    )

    if response:
        st.session_state.token = response["access_token"]
        # Save token to cookie for persistent login
        cookies['auth_token'] = response["access_token"]
        cookies.save()

        # Get user info
        user_info = api_request("/api/auth/me", auth=True)
        if user_info:
            st.session_state.user = user_info
            return True

    return False


def logout():
    """Logout user."""
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.page = 'login'
    # Clear cookie
    cookies['auth_token'] = ''
    cookies.save()


# Session state initialization with cookie support
if 'token' not in st.session_state:
    # Try to load token from cookie
    st.session_state.token = cookies.get('auth_token', None)
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# If we have a token from cookie but no user info, fetch user info
if st.session_state.token and not st.session_state.user:
    user_info = api_request("/api/auth/me", auth=True)
    if user_info:
        st.session_state.user = user_info
        st.session_state.page = 'main'
    else:
        # Token is invalid, clear it
        st.session_state.token = None
        st.session_state.user = None
        st.session_state.page = 'login'
        cookies['auth_token'] = ''
        cookies.save()


# Page: Login
def show_auth_page():
    """Display authentication page."""
    # Modern centered login page
    st.markdown("""
        <div style="max-width: 440px; margin: 4rem auto 0 auto; padding: 0 1rem;">
            <div style="text-align: center; margin-bottom: 2.5rem;">
                <div style="font-size: 3rem; font-weight: 700; color: #FF6B35; margin-bottom: 0.5rem; letter-spacing: -0.02em;">
                    BBL RAG
                </div>
                <div style="font-size: 1.125rem; font-weight: 600; color: #27272A; margin-bottom: 0.5rem;">
                    Kijk op Veiligheid
                </div>
                <div style="font-size: 0.875rem; color: #52525B; line-height: 1.4;">
                    Besluit Bouwwerken Leefomgeving
                </div>
                <div style="font-size: 0.875rem; color: #71717A; margin-top: 0.75rem; font-style: italic;">
                    Stel vragen over het BBL en krijg direct antwoord met artikelverwijzingen
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Login card
    st.markdown("""
        <div style="max-width: 440px; margin: 0 auto; padding: 0 1rem;">
            <div class="modern-card" style="padding: 2rem;">
                <h2 style="font-size: 1.5rem; font-weight: 700; color: #18181B; margin: 0 0 0.5rem 0;">
                    Inloggen
                </h2>
                <p style="font-size: 0.875rem; color: #71717A; margin: 0 0 1.5rem 0;">
                    Log in met uw account gegevens
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Info message about invitation-based access
    st.markdown("""
        <div style="max-width: 440px; margin: 1rem auto; padding: 0 1rem;">
            <div class="info-box">
                <strong>Nieuwe gebruikers</strong>: Accounts worden aangemaakt via uitnodiging. Neem contact op met een administrator voor toegang.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Form container
    st.markdown('<div style="max-width: 440px; margin: 0 auto; padding: 0 1rem;">', unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Gebruikersnaam", placeholder="Voer uw gebruikersnaam in")
        password = st.text_input("Wachtwoord", type="password", placeholder="Voer uw wachtwoord in")
        submit = st.form_submit_button("Inloggen", use_container_width=True)

        if submit:
            if not username or not password:
                st.markdown('<div class="error-box">Vul zowel gebruikersnaam als wachtwoord in</div>', unsafe_allow_html=True)
            else:
                with st.spinner("Inloggen..."):
                    if login(username, password):
                        st.markdown('<div class="success-box">Login succesvol!</div>', unsafe_allow_html=True)
                        st.session_state.page = 'main'
                        st.rerun()
                    else:
                        st.markdown('<div class="error-box">Login mislukt. Controleer uw inloggegevens.</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# Page: Main Application
def show_main_page():
    """Display main application page."""
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

        # Info over BBL versie (dynamisch)
        documents_response = api_request("/api/documents", auth=True)
        if documents_response:
            bbl_docs = [doc for doc in documents_response.get("documents", []) if doc['document_id'].startswith('BBL_')]
            doc_count = len(bbl_docs)
            if doc_count > 0:
                st.info(f"**BBL Versie**: 2025-07-01\n\n{doc_count} artikelen beschikbaar")
            else:
                st.warning("**Geen BBL documenten**\n\nUpload BBL documenten via het Admin Panel")
        else:
            st.warning("**Kan documenten niet laden**")

        st.markdown("---")

        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()

    # Main content
    if page == "BBL Vragen Stellen":
        show_query_page()
    elif page == "BBL Documenten":
        show_manage_documents_page()
    elif page == "Admin Panel":
        show_admin_panel()


# Page: Query Documents
def show_query_page():
    """Display document query interface."""
    st.markdown('<div class="main-header">Stel BBL Vragen</div>', unsafe_allow_html=True)
    st.markdown("*Stel vragen over het Besluit Bouwwerken Leefomgeving (BBL versie 2025-07-01)*")

    # Check if user has any documents
    documents_response = api_request("/api/documents", auth=True)
    has_documents = documents_response and documents_response.get("total_count", 0) > 0

    if not has_documents:
        st.warning("Geen BBL documenten beschikbaar.")
        st.info("Het BBL moet worden geladen door een administrator. Neem contact op met de systeembeheerder.")
        return

    # Model information box
    st.markdown("""
    <div class="info-box">
        <strong>Model:</strong> OpenAI GPT-4-turbo<br>
        <strong>Embeddings:</strong> text-embedding-3-large (3072 dimensies)<br>
        <strong>Database:</strong> 602 BBL artikelen (versie 2025-07-01)
    </div>
    """, unsafe_allow_html=True)

    # BBL Example questions
    st.markdown("**💡 Voorbeeldvragen:**")
    example_col1, example_col2 = st.columns(2)

    with example_col1:
        st.markdown("""
        - Wat zijn de eisen voor brandveiligheid in kantoorgebouwen?
        - Wat staat er in artikel 4.101 van het BBL?
        - Wat zijn de MPG-eisen voor nieuwbouw?
        """)

    with example_col2:
        st.markdown("""
        - Welke constructieve veiligheidsregels gelden voor bouwwerken?
        - Wat zijn de regels voor energieprestatie van gebouwen?
        - Wat zijn de eisen voor ventilatie in verblijfsruimten?
        """)

    st.markdown("---")

    # Query input
    query = st.text_area(
        "Jouw BBL Vraag",
        placeholder="Bijvoorbeeld: Wat zijn de brandveiligheidseisen voor kantoren?",
        height=100,
        key="bbl_query_input",
        max_chars=500
    )

    # Submit button
    submit = st.button("Zoek in BBL", use_container_width=True)

    if submit:
        if not query.strip():
            st.error("Voer een vraag in")
        elif len(query.strip()) < 20:
            st.error("Je vraag moet minimaal 20 tekens bevatten")
        else:
            with st.spinner("BBL doorzoeken..."):
                # Beperk tot top 5 meest relevante artikelen
                response = api_request(
                    "/api/query",
                    method="POST",
                    data={"query": query, "top_k": 5},
                    auth=True
                )

                if response:
                    # Store response in session state
                    st.session_state.query_response = response
                else:
                    st.session_state.query_response = None

    # Display query results OUTSIDE the form
    if 'query_response' in st.session_state and st.session_state.query_response:
        response = st.session_state.query_response

        # Display metadata
        st.caption(f"Verwerkingstijd: {response['processing_time_seconds']:.2f} seconden")

        # Only display sources if there are any (relevance >= 0.4)
        if response["sources"]:
            # Display sources
            st.markdown("### Gevonden BBL Artikelen")

            # Display sources with AI-generated summary and expandable full text
            for idx, source in enumerate(response["sources"], 1):
                # Use AI-generated title if available, otherwise fall back to metadata
                ai_title = source.get("title")

                if ai_title:
                    # Use AI-generated title (GPT-4-turbo)
                    title = f"{idx}. {ai_title}"
                else:
                    # Fallback: Build title from artikel metadata
                    artikel_label = source.get("artikel_label", "")
                    artikel_titel = source.get("artikel_titel", "")

                    if artikel_label and artikel_titel:
                        title = f"{idx}. {artikel_label} - {artikel_titel}"
                    elif artikel_label:
                        title = f"{idx}. {artikel_label}"
                    else:
                        title = f"{idx}. BBL Artikel"

                st.markdown(f"#### {title}")

                # Get AI-generated summary or fallback to longer truncation
                summary = source.get("summary")
                if not summary:
                    # Fallback: show first 300 chars (~3 sentences)
                    summary = source["text"][:300] + "..." if len(source["text"]) > 300 else source["text"]

                full_text = source["text"]

                # Show AI-generated summary in a styled box (HTML escaped for XSS protection)
                summary_escaped = html.escape(summary)
                st.markdown(f'<div class="source-box"><strong>AI Samenvatting (GPT-4-turbo):</strong><br>{summary_escaped}</div>', unsafe_allow_html=True)

                # Full text in expander
                with st.expander("Lees volledige artikel"):
                    st.markdown(f"**Document:** {source['filename']}")
                    st.markdown(f"**Chunk:** {source['chunk_index']}")
                    st.markdown("---")
                    st.markdown(full_text)

                st.markdown("")  # Add spacing between sources


# Page: Upload Documents
def show_upload_page():
    """Display document upload interface."""
    st.markdown('<div class="main-header">Upload Documents</div>', unsafe_allow_html=True)
    st.markdown("Upload PDF, DOCX, or TXT files to make them searchable.")

    st.markdown('<div class="info-box">Supported formats: PDF, DOCX, TXT<br>Maximum file size: 10MB</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'docx', 'txt'],
        help="Upload a document to add to your knowledge base"
    )

    if uploaded_file is not None:
        # Display file info
        st.markdown("#### File Information")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Filename:** {uploaded_file.name}")
        with col2:
            st.write(f"**Size:** {uploaded_file.size / 1024:.2f} KB")

        if st.button("Upload and Process", use_container_width=True):
            with st.spinner("Uploading and processing document..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}

                response = api_request(
                    "/api/documents/upload",
                    method="POST",
                    files=files,
                    auth=True
                )

                if response:
                    st.success(response["message"])
                    st.markdown(f"""
                    **Document ID:** {response['document_id']}
                    **Chunks Created:** {response['chunks_created']}
                    **File Size:** {response['file_size'] / 1024:.2f} KB
                    """)


# Page: Manage Documents
def show_manage_documents_page():
    """Display document management interface."""
    st.markdown('<div class="main-header">BBL Documenten</div>', unsafe_allow_html=True)
    st.markdown("*Overzicht van beschikbare BBL artikelen*")

    # Refresh button
    if st.button("Ververs Lijst"):
        st.rerun()

    # Get documents
    with st.spinner("BBL documenten laden..."):
        response = api_request("/api/documents", auth=True)

    if response:
        documents = response["documents"]

        # Filter: alleen BBL documenten tonen
        bbl_documents = [doc for doc in documents if doc['document_id'].startswith('BBL_')]
        total_count = len(bbl_documents)

        st.markdown(f"### BBL Artikelen ({total_count})")

        if total_count == 0:
            st.warning("Geen BBL documenten gevonden.")
            st.info("Het BBL moet worden geladen door een administrator.\n\nNeem contact op met de systeembeheerder.")
        else:
            # Display only BBL documents
            for doc in bbl_documents:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        st.markdown(f"**{doc['filename']}**")
                        st.caption(f"ID: {doc['document_id'][:8]}...")

                    with col2:
                        st.write(f"Chunks: {doc['chunks_count']}")
                        st.caption(f"Size: {doc['file_size'] / 1024:.2f} KB")

                    with col3:
                        if st.button("Delete", key=f"delete_{doc['document_id']}"):
                            with st.spinner("Deleting..."):
                                delete_response = api_request(
                                    f"/api/documents/{doc['document_id']}",
                                    method="DELETE",
                                    auth=True
                                )
                                if delete_response:
                                    st.success("Document deleted successfully!")
                                    st.rerun()

                    st.markdown("---")


# Page: Admin Panel
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
    tab1, tab2, tab3 = st.tabs(["Gebruiker Uitnodigen", "Gebruikers Beheren", "BBL Uploaden"])

    with tab1:
        st.subheader("Nieuwe Gebruiker Uitnodigen")
        st.markdown("Stuur een uitnodiging naar een nieuw emailadres. De gebruiker ontvangt een email met een link om hun account aan te maken.")

        with st.form("invite_user_form"):
            email = st.text_input("Email Adres", placeholder="gebruiker@example.com")
            submit = st.form_submit_button("Uitnodiging Versturen", use_container_width=True)

            if submit:
                if not email or '@' not in email:
                    st.error("Voer een geldig email adres in")
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
        st.subheader("BBL Documenten Uploaden")
        st.markdown("Upload PDF, DOCX of TXT bestanden met BBL artikelen om ze doorzoekbaar te maken.")

        uploaded_file = st.file_uploader(
            "Kies een bestand",
            type=['pdf', 'docx', 'txt', 'xml'],
            help="Upload een document om toe te voegen aan de kennisbank (XML voor BBL documenten)",
            key="admin_upload"
        )

        if uploaded_file is not None:
            # Display file info
            st.markdown("#### Bestandsinformatie")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Bestandsnaam:** {uploaded_file.name}")
            with col2:
                st.write(f"**Grootte:** {uploaded_file.size / 1024:.2f} KB")

            if st.button("Upload en Verwerk", use_container_width=True, key="upload_submit"):
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


# Main App Logic
def main():
    """Main application entry point."""
    if st.session_state.token is None or st.session_state.user is None:
        show_auth_page()
    else:
        show_main_page()


if __name__ == "__main__":
    main()

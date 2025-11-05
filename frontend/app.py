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

# Custom CSS with proper dark mode support
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: var(--text-color);
    }

    /* Light theme boxes */
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    .source-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        color: #212529;
        margin: 0.5rem 0;
    }

    /* Dark theme - using Streamlit's data-testid attribute on body */
    [data-testid="stAppViewContainer"][data-theme="dark"] .success-box,
    body[data-theme="dark"] .success-box {
        background-color: #1e4620 !important;
        border-color: #2d5a2e !important;
        color: #a3d9a5 !important;
    }
    [data-testid="stAppViewContainer"][data-theme="dark"] .error-box,
    body[data-theme="dark"] .error-box {
        background-color: #4a1f1f !important;
        border-color: #6b2c2c !important;
        color: #f5a3a3 !important;
    }
    [data-testid="stAppViewContainer"][data-theme="dark"] .info-box,
    body[data-theme="dark"] .info-box {
        background-color: #1a3a42 !important;
        border-color: #2a4f5a !important;
        color: #a3d5e6 !important;
    }
    [data-testid="stAppViewContainer"][data-theme="dark"] .source-box,
    body[data-theme="dark"] .source-box {
        background-color: #000000 !important;
        border-color: #333333 !important;
        color: #ffffff !important;
    }
    [data-testid="stAppViewContainer"][data-theme="dark"] .main-header,
    body[data-theme="dark"] .main-header {
        color: #ffffff !important;
    }

    /* Additional dark mode support using prefers-color-scheme */
    @media (prefers-color-scheme: dark) {
        .stApp[data-theme="dark"] .success-box,
        .stApp .success-box {
            background-color: #1e4620 !important;
            border-color: #2d5a2e !important;
            color: #a3d9a5 !important;
        }
        .stApp[data-theme="dark"] .error-box,
        .stApp .error-box {
            background-color: #4a1f1f !important;
            border-color: #6b2c2c !important;
            color: #f5a3a3 !important;
        }
        .stApp[data-theme="dark"] .info-box,
        .stApp .info-box {
            background-color: #1a3a42 !important;
            border-color: #2a4f5a !important;
            color: #a3d5e6 !important;
        }
        .stApp[data-theme="dark"] .source-box,
        .stApp .source-box {
            background-color: #000000 !important;
            border-color: #333333 !important;
            color: #ffffff !important;
        }
        .stApp[data-theme="dark"] .main-header,
        .stApp .main-header {
            color: #ffffff !important;
        }
    }
</style>

<script>
// Detect and apply dark mode
function applyDarkModeStyles() {
    const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const stApp = document.querySelector('.stApp');
    const body = document.body;

    if (stApp) {
        if (isDark) {
            stApp.setAttribute('data-theme', 'dark');
            body.setAttribute('data-theme', 'dark');
        } else {
            stApp.setAttribute('data-theme', 'light');
            body.setAttribute('data-theme', 'light');
        }
    }
}

// Apply dark mode on load
applyDarkModeStyles();

// Listen for theme changes
if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyDarkModeStyles);
}

// Fix tab navigation: remove password visibility toggle buttons from tab order
document.addEventListener('DOMContentLoaded', function() {
    applyDarkModeStyles();
    fixPasswordTabOrder();
    enableEnterToSubmit();
});

// Also run after a short delay for Streamlit's dynamic rendering
setTimeout(function() {
    applyDarkModeStyles();
    fixPasswordTabOrder();
    enableEnterToSubmit();
}, 1000);

// Run again after longer delay to catch late-loading elements
setTimeout(function() {
    applyDarkModeStyles();
    enableEnterToSubmit();
}, 2000);

function fixPasswordTabOrder() {
    // Find all password input containers
    const passwordInputs = document.querySelectorAll('input[type="password"]');

    passwordInputs.forEach(input => {
        // Find the parent container
        const container = input.closest('div[data-baseweb="input"]') || input.parentElement;

        // Find all buttons within this container (the visibility toggle)
        const buttons = container.querySelectorAll('button');

        buttons.forEach(button => {
            // Remove from tab order
            button.setAttribute('tabindex', '-1');
        });
    });

    console.log('Password field tab order fixed');
}

function enableEnterToSubmit() {
    // Find all textareas in forms
    const textareas = document.querySelectorAll('form textarea');

    textareas.forEach(textarea => {
        // Remove existing listener to avoid duplicates
        textarea.removeEventListener('keydown', handleEnterKey);
        // Add new listener
        textarea.addEventListener('keydown', handleEnterKey);
    });

    console.log('Enter-to-submit enabled for forms');
}

function handleEnterKey(event) {
    // Check if Enter was pressed (without Shift, which creates new line)
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();

        // Find the submit button in the same form
        const form = event.target.closest('form');
        if (form) {
            const submitButton = form.querySelector('button[kind="primary"], button[type="submit"]');
            if (submitButton) {
                submitButton.click();
                console.log('Form submitted via Enter key');
            }
        }
    }
}

// Re-run when Streamlit reruns (on interaction)
const observer = new MutationObserver(function(mutations) {
    applyDarkModeStyles();
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
                    if login(username, password):
                        st.success("Login successful!")
                        st.session_state.page = 'main'
                        st.rerun()
                    else:
                        st.error("Login failed. Please check your credentials.")


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

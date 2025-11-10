"""
CSS and JavaScript assets for the BBL RAG application.
Modern styling with Tailwind CSS and Inter font.
"""
import streamlit as st


def apply_custom_styles():
    """Apply modern custom CSS and JavaScript to the Streamlit app."""
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

    /* Remove default Streamlit padding/margins */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        max-width: 100% !important;
    }

    /* Hide cookie manager iframe */
    iframe[title*="cookie"] {
        display: none !important;
        height: 0 !important;
        width: 0 !important;
    }

    /* Hide Streamlit auto-generated page navigation */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* Show sidebar collapse button (will be auto-expanded on main page) */
    [data-testid="stSidebarCollapseButton"] button {
        background: transparent !important;
        border: none !important;
    }

    /* Compact Streamlit elements */
    .element-container {
        margin-bottom: 0.5rem !important;
    }

    /* Remove excessive vertical spacing */
    .stMarkdown {
        margin-bottom: 0.5rem !important;
    }

    /* Compact headings */
    h1, h2, h3 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* Compact info/error/success boxes */
    .stAlert {
        padding: 0.75rem 1rem !important;
        margin: 0.5rem 0 !important;
    }

    /* Modern header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
        color: #18181B;
        letter-spacing: -0.02em;
    }

    /* Minimalist card styling */
    .modern-card {
        background: #FAFAFA;
        border: 1px solid #E4E4E7;
        border-radius: 0.375rem;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: border-color 0.15s;
    }

    .modern-card:hover {
        border-color: #A1A1AA;
    }

    /* Success box - flat green */
    .success-box {
        padding: 1rem 1.25rem;
        border-radius: 0.375rem;
        background: #F0FDF4;
        border-left: 3px solid #22C55E;
        color: #166534;
        margin: 1rem 0;
        font-weight: 400;
    }

    /* Error box - flat red */
    .error-box {
        padding: 1rem 1.25rem;
        border-radius: 0.375rem;
        background: #FEF2F2;
        border-left: 3px solid #EF4444;
        color: #991B1B;
        margin: 1rem 0;
        font-weight: 400;
    }

    /* Info box - flat blue */
    .info-box {
        padding: 1rem 1.25rem;
        border-radius: 0.375rem;
        background: #EFF6FF;
        border-left: 3px solid #3B82F6;
        color: #1E40AF;
        margin: 1rem 0;
        font-weight: 400;
    }

    /* Source box - minimalist with subtle accent */
    .source-box {
        padding: 1.25rem;
        border-radius: 0.375rem;
        background: #FAFAFA;
        border: 1px solid #E4E4E7;
        border-left: 2px solid #FF6B35;
        color: #18181B;
        margin: 1rem 0;
        transition: border-color 0.15s;
    }

    .source-box:hover {
        border-left-color: #DC2626;
    }

    /* Minimalist Sidebar */
    section[data-testid="stSidebar"] {
        background: #FAFAFA !important;
        border-right: 1px solid #E4E4E7 !important;
    }

    /* Hide collapsed sidebar completely on login page */
    section[data-testid="stSidebar"][aria-expanded="false"] {
        display: none !important;
    }

    /* Also hide sidebar background when collapsed */
    section[data-testid="stSidebar"].st-emotion-cache-1gwvy71,
    section[data-testid="stSidebar"].st-emotion-cache-1cypcdb {
        display: none !important;
    }

    /* Minimalist sidebar buttons */
    section[data-testid="stSidebar"] button[kind="secondary"] {
        background: white !important;
        color: #3F3F46 !important;
        border: 1px solid #D4D4D8 !important;
        font-weight: 400 !important;
        transition: border-color 0.15s !important;
    }

    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: white !important;
        border-color: #52525B !important;
    }

    /* Hide default streamlit elements in sidebar */
    section[data-testid="stSidebar"] .stRadio {
        display: none;
    }

    /* Hide navigation button containers completely */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(button[aria-label=""]) {
        height: 0 !important;
        overflow: visible !important;
        margin: 0 !important;
    }

    /* Make navigation buttons invisible overlays */
    section[data-testid="stSidebar"] button[aria-label=""] {
        position: absolute !important;
        top: -2.5rem !important;
        left: 0 !important;
        width: 100% !important;
        height: 2.5rem !important;
        opacity: 0 !important;
        background: transparent !important;
        border: none !important;
        cursor: pointer !important;
        z-index: 10 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Minimalist primary buttons */
    button[kind="primary"] {
        background: #18181B !important;
        color: white !important;
        border: none !important;
        font-weight: 400 !important;
        transition: background 0.15s !important;
    }

    button[kind="primary"]:hover {
        background: #000000 !important;
    }

    /* Minimalist button styling */
    .stButton button {
        border-radius: 0.25rem !important;
        font-weight: 400 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.15s !important;
        height: auto !important;
        min-height: 2.5rem !important;
    }

    /* Form submit button - compact */
    .stFormSubmitButton button {
        height: 2.5rem !important;
        padding: 0.5rem 1.5rem !important;
        font-size: 0.875rem !important;
    }

    /* Compact text inputs */
    input[type="text"], input[type="password"] {
        padding: 0.5rem 0.75rem !important;
        font-size: 0.875rem !important;
        height: 2.5rem !important;
    }

    /* Compact form spacing */
    .stForm {
        padding: 0 !important;
    }

    /* Remove button outline on focus */
    button:focus {
        outline: none !important;
        box-shadow: 0 0 0 2px #E4E4E7 !important;
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
        button:hover {
            transform: none !important;
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

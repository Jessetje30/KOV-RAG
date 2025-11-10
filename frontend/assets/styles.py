"""
CSS and JavaScript assets for the BBL RAG application.
"""
import streamlit as st


def apply_custom_styles():
    """Apply custom CSS and JavaScript to the Streamlit app."""
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

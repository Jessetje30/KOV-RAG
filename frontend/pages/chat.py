"""
Bbl Chat Interface - Conversational Q&A with inline citations.
"""
import streamlit as st
import re
from services.api_client import api_request
from utils.security import sanitize_html, validate_query
from utils.document_helpers import get_bbl_document_count


def show_chat_page():
    """Display conversational chat interface for Bbl documents."""
    st.markdown('<div class="main-header">Bbl Chat</div>', unsafe_allow_html=True)
    st.markdown("*Converseer met het Besluit Bouwwerken Leefomgeving*")

    # Check if user has any documents
    documents_response = api_request("/api/documents", auth=True)
    has_documents = documents_response and documents_response.get("total_count", 0) > 0

    if not has_documents:
        st.warning("Geen Bbl documenten beschikbaar.")
        st.info("Het Bbl moet worden geladen door een administrator. Neem contact op met de systeembeheerder.")
        return

    # Get Bbl document count
    bbl_count = get_bbl_document_count(documents_response)

    # Initialize session state
    if 'current_chat_session_id' not in st.session_state:
        st.session_state.current_chat_session_id = None
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'chat_sessions_list' not in st.session_state:
        st.session_state.chat_sessions_list = []

    # Sidebar: Chat Session Management
    with st.sidebar:
        st.markdown("### 💬 Chat Sessies")

        # New chat button
        if st.button("➕ Nieuwe Chat", use_container_width=True, key="new_chat_btn"):
            # Create new session via API
            response = api_request(
                "/api/chat/sessions",
                method="POST",
                data={"title": "Nieuwe Chat"},
                auth=True
            )
            if response:
                st.session_state.current_chat_session_id = response['id']
                st.session_state.chat_messages = []
                st.rerun()

        st.markdown("---")

        # Load existing sessions
        sessions_response = api_request("/api/chat/sessions", auth=True)
        if sessions_response:
            st.session_state.chat_sessions_list = sessions_response

            if sessions_response:
                st.markdown("**Jouw Chats:**")
                for session in sessions_response[:10]:  # Show last 10
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        # Session button
                        is_current = st.session_state.current_chat_session_id == session['id']
                        button_label = f"{'▶️' if is_current else '💬'} {session['title'][:25]}..."

                        if st.button(
                            button_label,
                            key=f"sess_{session['id']}",
                            use_container_width=True
                        ):
                            # Load session
                            session_data = api_request(
                                f"/api/chat/sessions/{session['id']}",
                                auth=True
                            )
                            if session_data:
                                st.session_state.current_chat_session_id = session['id']
                                st.session_state.chat_messages = session_data.get('messages', [])
                                st.rerun()

                    with col2:
                        # Delete button
                        if st.button("🗑️", key=f"del_{session['id']}"):
                            api_request(
                                f"/api/chat/sessions/{session['id']}",
                                method="DELETE",
                                auth=True
                            )
                            if st.session_state.current_chat_session_id == session['id']:
                                st.session_state.current_chat_session_id = None
                                st.session_state.chat_messages = []
                            st.rerun()

    # Main chat area
    st.markdown(f"""
    <div class="info-box">
        <strong>Model:</strong> OpenAI GPT-4-turbo<br>
        <strong>Embeddings:</strong> text-embedding-3-large (3072 dimensies)<br>
        <strong>Database:</strong> {bbl_count} Bbl artikelen beschikbaar<br>
        <strong>💡 Tip:</strong> Bronnen verschijnen als [1], [2], [3] in antwoorden
    </div>
    """, unsafe_allow_html=True)

    # Check if we have an active session
    if st.session_state.current_chat_session_id is None:
        st.info("👈 Klik op **'➕ Nieuwe Chat'** in de sidebar om te beginnen")
        return

    # Display chat history
    if st.session_state.chat_messages:
        st.markdown("### 📜 Gesprekgeschiedenis")
        for message in st.session_state.chat_messages:
            if message['role'] == 'user':
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 12px; border-radius: 8px; margin-bottom: 10px;">
                    <strong>👤 Jij:</strong><br>
                    {sanitize_html(message['content'])}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Assistant message with inline citations
                content = message['content']

                st.markdown(f"""
                <div style="background-color: #e3f2fd; padding: 12px; border-radius: 8px; margin-bottom: 10px;">
                    <strong>🤖 Assistent:</strong><br>
                    {sanitize_html(content)}
                </div>
                """, unsafe_allow_html=True)

                # Display citations if available
                if message.get('sources'):
                    with st.expander("📚 Bekijk Bronnen"):
                        for source in message['sources']:
                            st.markdown(f"""
                            **[{source['number']}]** {source['filename']} (Relevantie: {source['score']:.3f})
                            """)
                            st.markdown(f'<div class="source-box">{sanitize_html(source["text"][:500])}...</div>', unsafe_allow_html=True)
                            st.markdown("---")

        st.markdown("---")

    # Chat input
    st.markdown("### ✍️ Stel een Vraag")

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Jouw bericht",
            placeholder="Stel een vraag over het Bbl...",
            height=120,
            key="chat_input",
            max_chars=2000,
            label_visibility="collapsed"
        )

        col1, col2 = st.columns([3, 1])
        with col1:
            submitted = st.form_submit_button("📤 Verstuur", use_container_width=True)
        with col2:
            top_k = st.number_input("Bronnen", min_value=1, max_value=10, value=5, help="Aantal bronnen om op te halen", label_visibility="collapsed")

        if submitted and user_input.strip():
            # Validate input
            is_valid, error_msg = validate_query(user_input)
            if not is_valid:
                st.error(error_msg)
            else:
                # Add user message to display (optimistic UI)
                st.session_state.chat_messages.append({
                    'role': 'user',
                    'content': user_input,
                    'sources': None
                })

                # Send query to backend
                with st.spinner("Bbl doorzoeken en antwoord genereren..."):
                    response = api_request(
                        "/api/chat/query",
                        method="POST",
                        data={
                            "session_id": st.session_state.current_chat_session_id,
                            "message": user_input,
                            "top_k": top_k
                        },
                        auth=True
                    )

                    if response:
                        # Add assistant message to display
                        st.session_state.chat_messages.append({
                            'role': 'assistant',
                            'content': response['answer'],
                            'sources': response.get('citations', [])
                        })

                        st.rerun()
                    else:
                        # Remove optimistic user message if failed
                        st.session_state.chat_messages.pop()
                        st.error("Fout bij het versturen van het bericht. Probeer het opnieuw.")

    # Example questions
    st.markdown("---")
    st.markdown("**💡 Voorbeeldvragen:**")
    example_col1, example_col2 = st.columns(2)

    with example_col1:
        st.markdown("""
        - Wat zijn de eisen voor brandveiligheid in kantoorgebouwen?
        - Wat staat er in artikel 4.101 van het Bbl?
        - Wat zijn de MPG-eisen voor nieuwbouw?
        """)

    with example_col2:
        st.markdown("""
        - Welke constructieve veiligheidsregels gelden voor bouwwerken?
        - Wat zijn de regels voor energieprestatie van gebouwen?
        - Kun je dat verder uitleggen?
        """)

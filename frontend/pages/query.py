"""
BBL Query page - Ask questions about BBL documents.
"""
import streamlit as st
from services.api_client import api_request


def show_query_page():
    """Display document query interface."""
    st.markdown('<div class="main-header">Stel BBL Vragen</div>', unsafe_allow_html=True)
    st.markdown("*Stel vragen over het Besluit Bouwwerken Leefomgeving*")

    # Check if user has any documents
    documents_response = api_request("/api/documents", auth=True)
    has_documents = documents_response and documents_response.get("total_count", 0) > 0

    if not has_documents:
        st.warning("Geen BBL documenten beschikbaar.")
        st.info("Het BBL moet worden geladen door een administrator. Neem contact op met de systeembeheerder.")
        return

    # Get BBL document count
    bbl_docs = [doc for doc in documents_response.get("documents", []) if doc['document_id'].startswith('BBL_')]
    bbl_count = len(bbl_docs)

    # Model information box
    st.markdown(f"""
    <div class="info-box">
        <strong>Model:</strong> OpenAI GPT-4-turbo<br>
        <strong>Embeddings:</strong> text-embedding-3-large (3072 dimensies)<br>
        <strong>Database:</strong> {bbl_count} BBL artikelen beschikbaar
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

                # Show AI-generated summary in a styled box
                st.markdown(f'<div class="source-box"><strong>AI Samenvatting (GPT-4-turbo):</strong><br>{summary}</div>', unsafe_allow_html=True)

                # Full text in expander
                with st.expander("Lees volledige artikel"):
                    st.markdown(f"**Document:** {source['filename']}")
                    st.markdown(f"**Chunk:** {source['chunk_index']}")
                    st.markdown("---")
                    st.markdown(full_text)

                st.markdown("")  # Add spacing between sources

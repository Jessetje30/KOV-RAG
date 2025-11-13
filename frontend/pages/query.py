"""
Bbl Query page - Ask questions about Bbl documents.
"""
import streamlit as st
import re
import pandas as pd
from services.api_client import api_request
from utils.security import sanitize_html, validate_query
from utils.document_helpers import get_bbl_document_count


def detect_and_render_tables(text: str):
    """
    Detecteer markdown tabellen in tekst en render ze als echte tabellen.

    Args:
        text: Tekst met mogelijk markdown tabellen
    """
    lines = text.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check if line looks like markdown table
        if line.startswith('|') and line.endswith('|') and line.count('|') >= 3:
            # Potential table start
            table_lines = []

            # Collect all consecutive table lines
            while i < len(lines):
                current_line = lines[i].strip()
                if current_line.startswith('|') and current_line.endswith('|'):
                    table_lines.append(current_line)
                    i += 1
                else:
                    break

            # Validate: must have at least 3 lines (header, separator, data)
            if len(table_lines) >= 3:
                # Check if second line is separator
                separator_line = table_lines[1]
                if re.match(r'^[\|\-\:\s]+$', separator_line):
                    # Valid markdown table - parse and render
                    try:
                        # Extract header
                        headers = [cell.strip() for cell in table_lines[0].split('|')[1:-1]]

                        # Extract data rows
                        data_rows = []
                        for line in table_lines[2:]:
                            cells = [cell.strip() for cell in line.split('|')[1:-1]]
                            if len(cells) == len(headers):
                                data_rows.append(cells)

                        if data_rows:
                            # Create and display DataFrame
                            df = pd.DataFrame(data_rows, columns=headers)
                            st.table(df)  # Render as table
                        else:
                            # Fallback: show as markdown
                            st.markdown('\n'.join(table_lines))
                    except Exception:
                        # Parse failed, show as markdown
                        st.markdown('\n'.join(table_lines))
                else:
                    # Not a valid table, show as text
                    for line in table_lines:
                        st.markdown(line)
                    i += 1
            else:
                # Not enough lines, show as text
                for line in table_lines:
                    st.markdown(line)
                i += 1
        else:
            # Regular line
            if line:
                st.markdown(line)
            i += 1


def show_query_page():
    """Display document query interface."""
    st.markdown('<div class="main-header">Stel Bbl Vragen</div>', unsafe_allow_html=True)
    st.markdown("*Stel vragen over het Besluit Bouwwerken Leefomgeving*")

    # Check if user has any documents
    documents_response = api_request("/api/documents", auth=True)
    has_documents = documents_response and documents_response.get("total_count", 0) > 0

    if not has_documents:
        st.warning("Geen Bbl documenten beschikbaar.")
        st.info("Het Bbl moet worden geladen door een administrator. Neem contact op met de systeembeheerder.")
        return

    # Get Bbl document count using utility function
    bbl_count = get_bbl_document_count(documents_response)

    # Model information box
    st.markdown(f"""
    <div class="info-box">
        <strong>Model:</strong> OpenAI GPT-4-turbo<br>
        <strong>Embeddings:</strong> text-embedding-3-large (3072 dimensies)<br>
        <strong>Database:</strong> {bbl_count} Bbl artikelen beschikbaar
    </div>
    """, unsafe_allow_html=True)

    # Bbl Example questions
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
        - Wat zijn de eisen voor ventilatie in verblijfsruimten?
        """)

    st.markdown("---")

    # Query input
    query = st.text_area(
        "Jouw Bbl Vraag",
        placeholder="Bijvoorbeeld: Wat zijn de brandveiligheidseisen voor kantoren?",
        height=100,
        key="bbl_query_input",
        max_chars=500
    )

    # Submit button
    submit = st.button("Zoek in Bbl", use_container_width=True)

    if submit:
        # Validate query input
        is_valid, error_msg = validate_query(query)
        if not is_valid:
            st.error(error_msg)
        else:
            with st.spinner("Bbl doorzoeken..."):
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
            st.markdown("### Gevonden Bbl Artikelen")

            # Show threshold info
            st.markdown("""
            <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                <strong>📊 Relevantie Score Uitleg:</strong><br>
                🟢 <strong>≥ 0.65</strong>: Hoge relevantie (goede match)<br>
                🟡 <strong>0.40 - 0.64</strong>: Middelmatige relevantie (mogelijk relevant)<br>
                🔴 <strong>&lt; 0.40</strong>: Lage relevantie (niet getoond)
            </div>
            """, unsafe_allow_html=True)

            # Display sources with AI-generated summary and expandable full text
            for idx, source in enumerate(response["sources"], 1):
                # Get relevance score
                score = source.get("score", 0.0)

                # Determine score color and badge
                if score >= 0.65:
                    score_color = "#28a745"  # Green
                    score_badge = "🟢"
                elif score >= 0.40:
                    score_color = "#ffc107"  # Orange/Yellow
                    score_badge = "🟡"
                else:
                    score_color = "#dc3545"  # Red
                    score_badge = "🔴"

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
                        title = f"{idx}. Bbl Artikel"

                # Display title with score badge
                st.markdown(f"#### {title}")
                st.markdown(f'{score_badge} <span style="color: {score_color}; font-weight: bold;">Relevantie Score: {score:.3f}</span>', unsafe_allow_html=True)

                # Get AI-generated summary or fallback to longer truncation
                summary = source.get("summary")
                if not summary:
                    # Fallback: show first 300 chars (~3 sentences)
                    summary = source["text"][:300] + "..." if len(source["text"]) > 300 else source["text"]

                full_text = source["text"]

                # Show AI-generated summary in a styled box (sanitized to prevent XSS)
                sanitized_summary = sanitize_html(summary)
                st.markdown(f'<div class="source-box"><strong>AI Samenvatting (GPT-4-turbo):</strong><br>{sanitized_summary}</div>', unsafe_allow_html=True)

                # Full text in expander with table detection
                with st.expander("Lees volledige artikel"):
                    st.markdown(f"**Document:** {source['filename']}")
                    st.markdown(f"**Chunk:** {source['chunk_index']}")
                    st.markdown("---")
                    # Detect and render tables properly
                    detect_and_render_tables(full_text)

                st.markdown("")  # Add spacing between sources

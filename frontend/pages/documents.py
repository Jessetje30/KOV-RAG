"""
Bbl Documents management page.
"""
import streamlit as st
from services.api_client import api_request


def show_manage_documents_page():
    """Display document management interface."""
    st.markdown('<div class="main-header">Bbl Documenten</div>', unsafe_allow_html=True)
    st.markdown("*Overzicht van beschikbare Bbl artikelen*")

    # Refresh button
    if st.button("Ververs Lijst"):
        st.rerun()

    # Get documents
    with st.spinner("Bbl documenten laden..."):
        response = api_request("/api/documents", auth=True)

    if response:
        documents = response["documents"]

        # Filter: alleen Bbl documenten tonen
        bbl_documents = [doc for doc in documents if doc['document_id'].startswith('BBL_')]
        total_count = len(bbl_documents)

        st.markdown(f"### Bbl Artikelen ({total_count})")

        if total_count == 0:
            st.warning("Geen Bbl documenten gevonden.")
            st.info("Het Bbl moet worden geladen door een administrator.\n\nNeem contact op met de systeembeheerder.")
        else:
            # Display only Bbl documents
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

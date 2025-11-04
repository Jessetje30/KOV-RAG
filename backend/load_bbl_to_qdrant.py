"""
Load BBL chunks into Qdrant for testing
"""

import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from bbl.xml_parser import parse_bbl_xml
from bbl.chunker import create_bbl_chunks
from rag import RAGPipeline
from qdrant_client.models import PointStruct


def load_bbl_to_qdrant(user_id: int = 1, version_date: str = "2025-07-01"):
    """
    Load BBL chunks into Qdrant for a specific user

    Args:
        user_id: User ID to load BBL for (default: 1)
        version_date: BBL version date (default: 2025-07-01)
    """
    print("=" * 80)
    print("LOAD BBL INTO QDRANT")
    print("=" * 80)
    print(f"User ID: {user_id}")
    print(f"BBL Version: {version_date}")

    # Paths
    xml_path = Path(f"../data/koop_wetten/BWBR0041297/{version_date}_0/xml/BWBR0041297_{version_date}_0.xml")

    if not xml_path.exists():
        print(f"\n❌ Error: BBL XML niet gevonden: {xml_path}")
        return

    print(f"\n📄 XML bestand: {xml_path.name}")

    # Parse BBL
    print("\n" + "-" * 80)
    print("PARSING BBL XML")
    print("-" * 80)

    metadata, artikelen = parse_bbl_xml(xml_path)
    print(f"✅ {len(artikelen)} artikelen geparsed")
    print(f"   Titel: {metadata.get('citeertitel', 'N/A')[:50]}")
    print(f"   Inwerkingtreding: {metadata.get('inwerkingtreding')}")

    # Create chunks
    print("\n" + "-" * 80)
    print("CHUNKING")
    print("-" * 80)

    chunks = create_bbl_chunks(artikelen, version_date)
    print(f"✅ {len(chunks)} chunks gegenereerd")

    # Statistics
    avg_length = sum(len(c['text']) for c in chunks) / len(chunks)
    print(f"   Gemiddelde lengte: {avg_length:.0f} characters")

    # Initialize RAG pipeline
    print("\n" + "-" * 80)
    print("INITIALIZE RAG PIPELINE")
    print("-" * 80)

    try:
        rag = RAGPipeline()
        print(f"✅ RAG pipeline initialized")
        print(f"   Embedding dimension: {rag.embedding_dimension}")
        print(f"   LLM provider: {type(rag.llm_provider).__name__}")
    except Exception as e:
        print(f"❌ Error initializing RAG: {e}")
        return

    # Ensure collection exists
    rag._ensure_collection_exists(user_id)
    collection_name = rag._get_collection_name(user_id)
    print(f"✅ Collection: {collection_name}")

    # Generate embeddings and store
    print("\n" + "-" * 80)
    print("EMBEDDING & STORING CHUNKS")
    print("-" * 80)
    print("This may take a few minutes...")

    # Generate unique document ID for BBL
    document_id = f"BBL_{version_date}"

    # Process chunks in batches to avoid memory issues
    batch_size = 50
    total_batches = (len(chunks) + batch_size - 1) // batch_size

    all_points = []

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min((batch_idx + 1) * batch_size, len(chunks))
        batch_chunks = chunks[start_idx:end_idx]

        print(f"\nBatch {batch_idx + 1}/{total_batches}: chunks {start_idx + 1}-{end_idx}")

        # Extract texts for embedding
        texts = [chunk['text'] for chunk in batch_chunks]

        # Get embeddings
        print(f"  Generating embeddings...")
        try:
            embeddings = rag._get_embeddings(texts)
        except Exception as e:
            print(f"  ❌ Error generating embeddings: {e}")
            continue

        print(f"  ✅ {len(embeddings)} embeddings generated")

        # Create points
        for chunk, embedding in zip(batch_chunks, embeddings):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    # Standard RAG fields
                    "document_id": document_id,
                    "user_id": user_id,
                    "filename": f"BBL_{version_date}.xml",
                    "chunk_index": len(all_points),
                    "text": chunk['text'],
                    "upload_date": datetime.now(timezone.utc).isoformat(),
                    "file_size": len(chunk['text']),

                    # BBL-specific metadata
                    "document_type": chunk['metadata']['document_type'],
                    "bwb_identifier": chunk['metadata']['bwb_identifier'],
                    "version_date": chunk['metadata']['version_date'],
                    "artikel_nummer": chunk['metadata']['artikel_nummer'],
                    "artikel_label": chunk['metadata']['artikel_label'],
                    "artikel_titel": chunk['metadata']['artikel_titel'],
                    "hoofdstuk_nr": chunk['metadata']['hoofdstuk_nr'],
                    "hoofdstuk_titel": chunk['metadata']['hoofdstuk_titel'],
                    "hoofdstuk": chunk['metadata']['hoofdstuk'],
                    "afdeling_nr": chunk['metadata']['afdeling_nr'],
                    "afdeling_titel": chunk['metadata']['afdeling_titel'],
                    "afdeling": chunk['metadata']['afdeling'],
                    "leden_count": chunk['metadata']['leden_count'],
                    "source_url": chunk['metadata']['source_url'],
                    "chunk_type": chunk['metadata']['chunk_type']
                }
            )
            all_points.append(point)

    # Upload all points to Qdrant in batches
    print(f"\n" + "-" * 80)
    print(f"UPLOADING TO QDRANT")
    print("-" * 80)
    print(f"Total points to upload: {len(all_points)}")

    # Upload in smaller batches to avoid timeout
    upload_batch_size = 100
    upload_batches = (len(all_points) + upload_batch_size - 1) // upload_batch_size

    try:
        for i in range(upload_batches):
            start = i * upload_batch_size
            end = min((i + 1) * upload_batch_size, len(all_points))
            batch = all_points[start:end]

            rag.qdrant_client.upsert(
                collection_name=collection_name,
                points=batch
            )
            print(f"  ✅ Uploaded batch {i + 1}/{upload_batches} ({len(batch)} points)")

        print(f"✅ Successfully uploaded all {len(all_points)} points to Qdrant")
    except Exception as e:
        print(f"❌ Error uploading to Qdrant: {e}")
        import traceback
        traceback.print_exc()
        return

    # Verify
    print("\n" + "-" * 80)
    print("VERIFICATION")
    print("-" * 80)

    try:
        collection_info = rag.qdrant_client.get_collection(collection_name)
        print(f"✅ Collection points count: {collection_info.points_count}")

        # Test query
        print("\n" + "-" * 80)
        print("TEST QUERY")
        print("-" * 80)
        test_query = "Wat zijn de eisen voor brandveiligheid?"
        print(f"Query: {test_query}")

        answer, sources, time_taken = rag.query(user_id, test_query, top_k=3)

        print(f"\n✅ Query successful!")
        print(f"Time taken: {time_taken:.2f}s")
        print(f"Sources found: {len(sources)}")

        print(f"\nAnswer preview:")
        print(answer[:300] + "...")

        print(f"\nTop source:")
        if sources:
            top_source = sources[0]
            print(f"  Artikel: {top_source.get('artikel_label', 'N/A')}")
            print(f"  Titel: {top_source.get('artikel_titel', 'N/A')}")
            print(f"  Score: {top_source['score']:.3f}")
            print(f"  Text: {top_source['text'][:200]}...")

    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("BBL SUCCESSFULLY LOADED!")
    print("=" * 80)
    print(f"✅ {len(chunks)} BBL artikelen beschikbaar voor queries")
    print(f"✅ User ID {user_id} kan nu BBL vragen stellen")
    print(f"\nStart de applicatie met: ./start.sh")
    print(f"Login als user {user_id} en stel BBL-gerelateerde vragen!")


if __name__ == "__main__":
    # Default user ID = 1
    # Je kunt dit aanpassen of als command line argument meegeven
    load_bbl_to_qdrant(user_id=1, version_date="2025-07-01")

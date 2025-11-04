"""
Migrate BBL data to separate collection
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition, MatchValue, PointStruct

# Load environment variables
load_dotenv()

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

def migrate_bbl_to_separate_collection(user_id: int = 1):
    """
    Migrate BBL documents to a separate collection
    """
    print("=" * 80)
    print("MIGRATE BBL TO SEPARATE COLLECTION")
    print("=" * 80)

    # Connect to Qdrant
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    old_collection = f"user_{user_id}_documents"
    new_collection = f"user_{user_id}_bbl_documents"

    print(f"\nOld collection: {old_collection}")
    print(f"New collection: {new_collection}")

    # Check if old collection exists
    collections = client.get_collections().collections
    collection_names = [col.name for col in collections]

    if old_collection not in collection_names:
        print(f"\n❌ Old collection doesn't exist: {old_collection}")
        return

    # Get collection info
    old_info = client.get_collection(old_collection)
    vector_size = old_info.config.params.vectors.size

    print(f"\n📊 Old collection stats:")
    print(f"   Total points: {old_info.points_count}")
    print(f"   Vector size: {vector_size}")

    # Create new collection
    if new_collection in collection_names:
        print(f"\n⚠️  Collection {new_collection} already exists. Deleting...")
        client.delete_collection(new_collection)

    client.create_collection(
        collection_name=new_collection,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE
        )
    )
    print(f"✅ Created new collection: {new_collection}")

    # Scroll through old collection and copy BBL documents
    print("\n📥 Copying BBL documents...")
    offset = None
    total_copied = 0
    batch_size = 100

    while True:
        # Scroll through all documents (no filter - we'll filter in Python)
        results, offset = client.scroll(
            collection_name=old_collection,
            limit=batch_size,
            offset=offset,
            with_payload=True,
            with_vectors=True
        )

        if not results:
            break

        # Filter to only BBL documents (document_id starts with "BBL_")
        bbl_points = [p for p in results if p.payload.get('document_id', '').startswith('BBL_')]

        print(f"   Scanned {len(results)} points, found {len(bbl_points)} BBL points")

        if bbl_points:
            # Convert Records to PointStruct
            point_structs = [
                PointStruct(
                    id=p.id,
                    vector=p.vector,
                    payload=p.payload
                )
                for p in bbl_points
            ]

            # Upload to new collection
            client.upsert(
                collection_name=new_collection,
                points=point_structs
            )
            total_copied += len(bbl_points)
            print(f"   Copied {len(bbl_points)} BBL points (total: {total_copied})")

        if offset is None:
            break

    print(f"\n✅ Migration complete!")
    print(f"   Total BBL points copied: {total_copied}")

    # Verify new collection
    new_info = client.get_collection(new_collection)
    print(f"\n📊 New BBL collection stats:")
    print(f"   Total points: {new_info.points_count}")

    # Test query
    print("\n🔍 Testing query on new collection...")
    test_results = client.scroll(
        collection_name=new_collection,
        limit=3,
        with_payload=True,
        with_vectors=False
    )[0]

    if test_results:
        print("✅ Sample BBL documents:")
        for point in test_results:
            artikel = point.payload.get('artikel_label', 'N/A')
            hoofdstuk = point.payload.get('hoofdstuk', 'N/A')
            print(f"   - {artikel}: {hoofdstuk}")

    print("\n" + "=" * 80)
    print("MIGRATION SUCCESSFUL!")
    print("=" * 80)
    print(f"\n✅ BBL data is now in: {new_collection}")
    print(f"📝 Next step: Update backend to use BBL collection")


if __name__ == "__main__":
    migrate_bbl_to_separate_collection(user_id=1)

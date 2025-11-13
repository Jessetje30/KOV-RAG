#!/usr/bin/env python3
"""
Reset Qdrant collection voor een user.
Verwijdert alle chunks zodat BBL opnieuw kan worden geüpload met metadata.
"""
import sys
from qdrant_client import QdrantClient
from config import QDRANT_HOST, QDRANT_PORT


def reset_user_collection(user_id: int, collection_type: str = "bbl"):
    """
    Verwijder een user collection.

    Args:
        user_id: User ID
        collection_type: "bbl" of "documents"
    """
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    if collection_type == "bbl":
        collection_name = f"user_{user_id}_bbl_documents"
    else:
        collection_name = f"user_{user_id}_documents"

    # Check if collection exists
    collections = client.get_collections().collections
    collection_names = [col.name for col in collections]

    if collection_name in collection_names:
        print(f"🗑️  Deleting collection: {collection_name}")
        client.delete_collection(collection_name)
        print(f"✅ Collection {collection_name} deleted successfully!")
        print(f"\nℹ️  You can now re-upload BBL documents via the Admin Panel.")
        print(f"   New metadata will be automatically extracted and stored.")
    else:
        print(f"❌ Collection {collection_name} does not exist.")
        print(f"\nAvailable collections:")
        for col in collection_names:
            print(f"  - {col}")


def list_collections():
    """List all Qdrant collections."""
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    collections = client.get_collections().collections

    print("📊 Available Qdrant Collections:")
    print("-" * 50)
    for col in collections:
        info = client.get_collection(col.name)
        print(f"\n🗂️  {col.name}")
        print(f"   Points: {info.points_count}")
        print(f"   Vectors: {info.vectors_count}")


if __name__ == "__main__":
    print("=" * 50)
    print("🔄 Qdrant Collection Reset Tool")
    print("=" * 50)
    print()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python reset_qdrant_collection.py <user_id> [collection_type]")
        print()
        print("Examples:")
        print("  python reset_qdrant_collection.py 1 bbl       # Reset BBL collection for user 1")
        print("  python reset_qdrant_collection.py 1 documents # Reset documents collection for user 1")
        print("  python reset_qdrant_collection.py list       # List all collections")
        print()
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        list_collections()
    else:
        try:
            user_id = int(command)
            collection_type = sys.argv[2] if len(sys.argv) > 2 else "bbl"

            print(f"⚠️  WARNING: This will delete ALL chunks for user {user_id}!")
            print(f"   Collection: user_{user_id}_{collection_type}_documents")
            print()
            confirm = input("Continue? (yes/no): ")

            if confirm.lower() == "yes":
                reset_user_collection(user_id, collection_type)
            else:
                print("❌ Aborted.")
        except ValueError:
            print("❌ Error: user_id must be a number")
            sys.exit(1)

#!/usr/bin/env python3
"""
Check database status voor debugging.
Toont users, collections, en chunk metadata.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from qdrant_client import QdrantClient
from config import DATABASE_URL, QDRANT_HOST, QDRANT_PORT
from db.models import User
import json


def check_users():
    """List all users in the database."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    users = session.query(User).all()

    print("👥 USERS IN DATABASE:")
    print("=" * 60)
    for user in users:
        print(f"ID: {user.id} | Username: {user.username} | Email: {user.email} | Role: {user.role}")
    print()

    session.close()
    return users


def check_collections(user_id=None):
    """Check Qdrant collections and their contents."""
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    collections = client.get_collections().collections

    print("📊 QDRANT COLLECTIONS:")
    print("=" * 60)

    if not collections:
        print("❌ No collections found in Qdrant")
        return

    for col in collections:
        info = client.get_collection(col.name)
        print(f"\n🗂️  {col.name}")
        print(f"   Total points: {info.points_count}")
        print(f"   Vectors: {info.vectors_count}")

        # If user_id specified, show sample point
        if user_id and f"user_{user_id}" in col.name:
            try:
                # Get a sample point
                results = client.scroll(
                    collection_name=col.name,
                    limit=1,
                    with_payload=True,
                    with_vectors=False
                )

                if results[0]:
                    sample = results[0][0]
                    print(f"\n   📄 Sample chunk metadata:")

                    # Check for new metadata fields
                    payload = sample.payload
                    print(f"      artikel_label: {payload.get('artikel_label', 'N/A')}")
                    print(f"      artikel_nummer: {payload.get('artikel_nummer', 'N/A')}")
                    print(f"      hoofdstuk_nr: {payload.get('hoofdstuk_nr', 'N/A')}")

                    # NEW METADATA FIELDS
                    has_metadata = (
                        'functie_types' in payload or
                        'bouw_type' in payload or
                        'thema_tags' in payload
                    )

                    if has_metadata:
                        print(f"      ✅ HAS NEW METADATA:")
                        print(f"         functie_types: {payload.get('functie_types', [])}")
                        print(f"         bouw_type: {payload.get('bouw_type', 'None')}")
                        print(f"         thema_tags: {payload.get('thema_tags', [])}")
                    else:
                        print(f"      ❌ NO NEW METADATA (needs re-upload!)")
                        print(f"         Missing: functie_types, bouw_type, thema_tags")

            except Exception as e:
                print(f"   ⚠️  Could not fetch sample: {e}")

    print()


def main():
    print("=" * 60)
    print("🔍 KOV-RAG Database Status Check")
    print("=" * 60)
    print()

    # Check users
    users = check_users()

    # Check collections for each user
    for user in users:
        check_collections(user_id=user.id)


if __name__ == "__main__":
    main()

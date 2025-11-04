"""
Test script voor BBL Chunker
"""

from pathlib import Path
from bbl.xml_parser import parse_bbl_xml
from bbl.chunker import BBLChunker, create_bbl_chunks
import json


def main():
    print("=" * 80)
    print("BBL CHUNKER TEST")
    print("=" * 80)

    # Parse BBL XML
    xml_path = Path("../data/koop_wetten/BWBR0041297/2025-07-01_0/xml/BWBR0041297_2025-07-01_0.xml")
    print(f"\nParsing: {xml_path.name}")

    metadata, artikelen = parse_bbl_xml(xml_path)
    print(f"✅ {len(artikelen)} artikelen geparsed")

    # Create chunks
    print("\n" + "-" * 80)
    print("CHUNKING")
    print("-" * 80)

    version_date = "2025-07-01"
    chunks = create_bbl_chunks(artikelen, version_date)

    print(f"✅ {len(chunks)} chunks gegenereerd")

    # Statistieken
    print("\n" + "-" * 80)
    print("CHUNK STATISTIEKEN")
    print("-" * 80)

    chunker = BBLChunker(version_date)
    stats = chunker.get_statistics(chunks)

    print(f"Totaal chunks:        {stats['total_chunks']}")
    print(f"Gem. chunk lengte:    {stats['avg_chunk_length']:.0f} characters")
    print(f"Min chunk lengte:     {stats['min_chunk_length']} characters")
    print(f"Max chunk lengte:     {stats['max_chunk_length']} characters")
    print(f"Totaal hoofdstukken:  {stats['total_hoofdstukken']}")

    # Chunks per hoofdstuk
    print("\n" + "-" * 80)
    print("CHUNKS PER HOOFDSTUK")
    print("-" * 80)

    for hst, count in sorted(stats['chunks_per_hoofdstuk'].items()):
        print(f"{hst:70} {count:3} chunks")

    # Toon sample chunks
    print("\n" + "-" * 80)
    print("VOORBEELD CHUNKS")
    print("-" * 80)

    sample_indices = [0, 10, 100, 300, 500]  # Spread over document

    for idx in sample_indices:
        if idx >= len(chunks):
            continue

        chunk = chunks[idx]
        print(f"\n--- CHUNK {idx + 1} ---")
        print(f"Artikel: {chunk['metadata']['artikel_label']}")
        if chunk['metadata']['artikel_titel']:
            print(f"Titel: {chunk['metadata']['artikel_titel']}")
        print(f"Context: {chunk['metadata']['hoofdstuk']}")
        if chunk['metadata']['afdeling']:
            print(f"         {chunk['metadata']['afdeling']}")
        print(f"Leden: {chunk['metadata']['leden_count']}")
        print(f"Lengte: {len(chunk['text'])} characters")
        print(f"\nTekst preview (eerste 300 chars):")
        print(chunk['text'][:300] + "...")

    # Toon volledige chunk voor artikel 2.1
    print("\n" + "=" * 80)
    print("VOLLEDIGE CHUNK VOORBEELD: Artikel 2.1")
    print("=" * 80)

    chunk_2_1 = next((c for c in chunks if c['metadata']['artikel_nummer'] == "2.1"), None)

    if chunk_2_1:
        print("\n--- TEXT ---")
        print(chunk_2_1['text'])
        print("\n--- METADATA ---")
        print(json.dumps(chunk_2_1['metadata'], indent=2, ensure_ascii=False))
    else:
        print("Artikel 2.1 niet gevonden")

    # Test met complexer artikel (bijv artikel met meerdere leden)
    print("\n" + "=" * 80)
    print("COMPLEX ARTIKEL VOORBEELD: Artikel met meerdere leden")
    print("=" * 80)

    # Zoek artikel met minimaal 3 leden
    complex_chunk = next((c for c in chunks if c['metadata']['leden_count'] >= 3), None)

    if complex_chunk:
        print(f"\n{complex_chunk['metadata']['artikel_label']} - {complex_chunk['metadata']['artikel_titel']}")
        print(f"Leden: {complex_chunk['metadata']['leden_count']}")
        print(f"\n--- TEXT ---")
        print(complex_chunk['text'][:500] + "..." if len(complex_chunk['text']) > 500 else complex_chunk['text'])
    else:
        print("Geen complex artikel gevonden")

    # Sla sample chunks op
    output_path = Path("../data/bbl_chunks_sample.json")
    print(f"\n" + "-" * 80)
    print(f"Opslaan sample chunks naar: {output_path}")
    print("-" * 80)

    # Sla eerste 10 chunks op
    sample_chunks = chunks[:10]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_chunks, f, indent=2, ensure_ascii=False)

    print(f"✅ {len(sample_chunks)} sample chunks opgeslagen")

    print("\n" + "=" * 80)
    print("TEST VOLTOOID")
    print("=" * 80)
    print(f"\n✅ {len(chunks)} chunks klaar voor embedding")
    print(f"📊 Gemiddelde lengte: {stats['avg_chunk_length']:.0f} characters")
    print(f"📝 Totaal tekst: {sum(len(c['text']) for c in chunks):,} characters")


if __name__ == "__main__":
    main()

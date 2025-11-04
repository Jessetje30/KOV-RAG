"""
Test script voor BBL XML parser
"""

from pathlib import Path
from bbl.xml_parser import BWBParser, parse_bbl_xml


def main():
    # Path naar BBL XML (vanaf backend folder)
    xml_path = Path("../data/koop_wetten/BWBR0041297/2025-07-01_0/xml/BWBR0041297_2025-07-01_0.xml")

    print("=" * 80)
    print("BBL XML PARSER TEST")
    print("=" * 80)
    print(f"\nXML bestand: {xml_path}")
    print(f"Bestand bestaat: {xml_path.exists()}")
    print(f"Bestand grootte: {xml_path.stat().st_size / 1024 / 1024:.2f} MB\n")

    # Parse het bestand
    print("Parsing XML...")
    parser = BWBParser(xml_path)

    # Extract metadata
    print("\n" + "-" * 80)
    print("METADATA")
    print("-" * 80)
    metadata = parser.extract_metadata()
    for key, value in metadata.items():
        print(f"{key:20}: {value}")

    # Count structuur
    print("\n" + "-" * 80)
    print("STRUCTUUR OVERZICHT")
    print("-" * 80)
    counts = parser.count_structure()
    for key, value in counts.items():
        print(f"{key:20}: {value}")

    # Extract alle artikelen
    print("\n" + "-" * 80)
    print("ARTIKELEN EXTRAHEREN")
    print("-" * 80)
    print("Extracting artikelen...")
    artikelen = parser.extract_all_artikelen()
    print(f"\n✅ Totaal {len(artikelen)} artikelen geëxtraheerd")

    # Toon eerste 5 artikelen als voorbeeld
    print("\n" + "-" * 80)
    print("VOORBEELD ARTIKELEN (eerste 5)")
    print("-" * 80)

    for i, artikel in enumerate(artikelen[:5], 1):
        print(f"\n{i}. {artikel.get_artikel_label()}")
        if artikel.titel:
            print(f"   Titel: {artikel.titel}")
        print(f"   Context: {artikel.get_full_context()}")
        print(f"   Aantal leden: {len(artikel.leden)}")

        # Toon eerste lid
        if artikel.leden:
            eerste_lid = artikel.leden[0]
            lid_tekst = eerste_lid.tekst[:150] + "..." if len(eerste_lid.tekst) > 150 else eerste_lid.tekst
            if eerste_lid.nummer:
                print(f"   Lid {eerste_lid.nummer}: {lid_tekst}")
            else:
                print(f"   Tekst: {lid_tekst}")

    # Statistieken per hoofdstuk
    print("\n" + "-" * 80)
    print("ARTIKELEN PER HOOFDSTUK")
    print("-" * 80)

    hoofdstukken = {}
    for artikel in artikelen:
        hst_key = f"Hoofdstuk {artikel.hoofdstuk_nr}: {artikel.hoofdstuk_titel}"
        if hst_key not in hoofdstukken:
            hoofdstukken[hst_key] = 0
        hoofdstukken[hst_key] += 1

    for hst, count in sorted(hoofdstukken.items()):
        print(f"{hst:70} {count:3} artikelen")

    # Toon een volledig artikel als voorbeeld
    print("\n" + "-" * 80)
    print("VOLLEDIG ARTIKEL VOORBEELD (Artikel 2.1)")
    print("-" * 80)

    # Zoek artikel 2.1
    artikel_2_1 = next((a for a in artikelen if a.nummer == "2.1"), None)

    if artikel_2_1:
        print(f"\n{artikel_2_1.get_artikel_label()}", end="")
        if artikel_2_1.titel:
            print(f" {artikel_2_1.titel}")
        else:
            print()

        print(f"Context: {artikel_2_1.get_full_context()}\n")

        for lid in artikel_2_1.leden:
            if lid.nummer:
                print(f"Lid {lid.nummer}:")
            print(f"{lid.tekst}\n")
    else:
        print("Artikel 2.1 niet gevonden")

    print("\n" + "=" * 80)
    print("TEST VOLTOOID")
    print("=" * 80)


if __name__ == "__main__":
    main()

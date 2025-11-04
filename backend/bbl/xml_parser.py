"""
BWB XML Parser voor BBL (Besluit Bouwwerken Leefomgeving)
Parse de XML structuur en extract artikelen met hiërarchische context
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Lid:
    """Representatie van een lid binnen een artikel"""
    nummer: str
    tekst: str


@dataclass
class Artikel:
    """Representatie van een artikel uit de wet"""
    nummer: str  # "2.1"
    titel: Optional[str]
    leden: List[Lid]
    hoofdstuk_nr: str  # "2"
    hoofdstuk_titel: str  # "Algemene bepalingen voor bouwwerken"
    afdeling_nr: Optional[str]  # "2.1"
    afdeling_titel: Optional[str]  # "Algemeen"

    def get_artikel_label(self) -> str:
        """Return formatted artikel label"""
        return f"Artikel {self.nummer}"

    def get_full_context(self) -> str:
        """Return volledige hiërarchische context"""
        context_parts = [f"Hoofdstuk {self.hoofdstuk_nr}. {self.hoofdstuk_titel}"]
        if self.afdeling_nr and self.afdeling_titel:
            context_parts.append(f"Afdeling {self.afdeling_nr}. {self.afdeling_titel}")
        return ", ".join(context_parts)


class BWBParser:
    """Parse BWB toestand XML voor BBL"""

    def __init__(self, xml_path: Path):
        self.xml_path = Path(xml_path)
        if not self.xml_path.exists():
            raise FileNotFoundError(f"XML bestand niet gevonden: {xml_path}")

        # Parse XML
        self.tree = ET.parse(self.xml_path)
        self.root = self.tree.getroot()

    def extract_metadata(self) -> Dict:
        """Extract metadata van het BBL"""
        metadata = {}

        # Zoek intitule (officiële titel)
        intitule = self.root.find('.//intitule')
        if intitule is not None:
            metadata['intitule'] = self._get_text_content(intitule)

        # Zoek citeertitel (verkorte naam)
        citeertitel = self.root.find('.//citeertitel')
        if citeertitel is not None:
            metadata['citeertitel'] = self._get_text_content(citeertitel)

        # Inwerkingtreding datum
        metadata['inwerkingtreding'] = self.root.get('inwerkingtreding', '')
        metadata['bwb_id'] = self.root.get('bwb-id', '')

        return metadata

    def extract_all_artikelen(self) -> List[Artikel]:
        """
        Extract alle artikelen met hiërarchische context
        """
        artikelen = []

        # Itereer door hoofdstukken
        for hoofdstuk in self.root.findall('.//hoofdstuk'):
            # Extract hoofdstuk info
            hst_kop = hoofdstuk.find('kop')
            if hst_kop is None:
                continue

            hst_nr_el = hst_kop.find('nr')
            hst_titel_el = hst_kop.find('titel')

            hst_nr = self._get_text_content(hst_nr_el) if hst_nr_el is not None else "?"
            hst_titel = self._get_text_content(hst_titel_el) if hst_titel_el is not None else ""

            # Zoek afdelingen binnen hoofdstuk
            afdelingen = hoofdstuk.findall('.//afdeling')

            if afdelingen:
                # Er zijn afdelingen
                for afdeling in afdelingen:
                    afd_kop = afdeling.find('kop')
                    if afd_kop is None:
                        continue

                    afd_nr_el = afd_kop.find('nr')
                    afd_titel_el = afd_kop.find('titel')

                    afd_nr = self._get_text_content(afd_nr_el) if afd_nr_el is not None else None
                    afd_titel = self._get_text_content(afd_titel_el) if afd_titel_el is not None else None

                    # Artikelen binnen afdeling
                    for artikel_el in afdeling.findall('.//artikel'):
                        artikel = self._parse_artikel(
                            artikel_el,
                            hoofdstuk_nr=hst_nr,
                            hoofdstuk_titel=hst_titel,
                            afdeling_nr=afd_nr,
                            afdeling_titel=afd_titel
                        )
                        if artikel:
                            artikelen.append(artikel)
            else:
                # Geen afdelingen, artikelen direct in hoofdstuk
                for artikel_el in hoofdstuk.findall('./artikel'):
                    artikel = self._parse_artikel(
                        artikel_el,
                        hoofdstuk_nr=hst_nr,
                        hoofdstuk_titel=hst_titel,
                        afdeling_nr=None,
                        afdeling_titel=None
                    )
                    if artikel:
                        artikelen.append(artikel)

        return artikelen

    def _parse_artikel(
        self,
        artikel_el: ET.Element,
        hoofdstuk_nr: str,
        hoofdstuk_titel: str,
        afdeling_nr: Optional[str],
        afdeling_titel: Optional[str]
    ) -> Optional[Artikel]:
        """Parse individueel artikel element"""

        # Extract artikel kop
        kop = artikel_el.find('kop')
        if kop is None:
            return None

        nr_el = kop.find('nr')
        titel_el = kop.find('titel')

        if nr_el is None:
            return None

        art_nr = self._get_text_content(nr_el)
        art_titel = self._get_text_content(titel_el) if titel_el is not None else None

        # Extract leden
        leden = []
        lid_elements = artikel_el.findall('.//lid')

        if lid_elements:
            # Artikel heeft explicite leden
            for lid_el in lid_elements:
                lidnr_el = lid_el.find('lidnr')
                lid_nr = self._get_text_content(lidnr_el) if lidnr_el is not None else ""

                # Haal alle tekst op uit dit lid
                lid_tekst = self._extract_lid_text(lid_el)

                if lid_tekst.strip():
                    leden.append(Lid(nummer=lid_nr, tekst=lid_tekst.strip()))
        else:
            # Geen explicite leden, pak alle tekst uit artikel
            artikel_tekst = self._extract_artikel_text(artikel_el)
            if artikel_tekst.strip():
                leden.append(Lid(nummer="", tekst=artikel_tekst.strip()))

        return Artikel(
            nummer=art_nr,
            titel=art_titel,
            leden=leden,
            hoofdstuk_nr=hoofdstuk_nr,
            hoofdstuk_titel=hoofdstuk_titel,
            afdeling_nr=afdeling_nr,
            afdeling_titel=afdeling_titel
        )

    def _extract_lid_text(self, lid_el: ET.Element) -> str:
        """Extract alle text content uit een lid element"""
        text_parts = []

        # Haal alle <al> (alinea) elementen
        for al in lid_el.findall('.//al'):
            text = self._get_text_content(al)
            if text:
                text_parts.append(text)

        return " ".join(text_parts)

    def _extract_artikel_text(self, artikel_el: ET.Element) -> str:
        """Extract alle text content uit artikel (zonder leden structuur)"""
        text_parts = []

        # Haal alle <al> elementen op die niet in <kop> zitten
        # Simpele aanpak: skip kop element expliciet
        kop = artikel_el.find('kop')

        for al in artikel_el.findall('.//al'):
            # Check of dit al element binnen de kop zit
            if kop is not None and al in list(kop.iter()):
                continue  # Skip al's in kop

            text = self._get_text_content(al)
            if text:
                text_parts.append(text)

        return " ".join(text_parts)

    def _get_text_content(self, element: Optional[ET.Element]) -> str:
        """Get alle text content recursief (inclusief tail text)"""
        if element is None:
            return ""

        # Start met element text
        parts = [element.text or ""]

        # Itereer door alle child elements
        for child in element:
            # Recursief get child text
            parts.append(self._get_text_content(child))
            # Voeg tail text toe (text na child closing tag)
            if child.tail:
                parts.append(child.tail)

        return "".join(parts).strip()

    def count_structure(self) -> Dict:
        """Tel structurele elementen voor overzicht"""
        return {
            "hoofdstukken": len(self.root.findall('.//hoofdstuk')),
            "afdelingen": len(self.root.findall('.//afdeling')),
            "artikelen": len(self.root.findall('.//artikel')),
            "paragrafen": len(self.root.findall('.//paragraaf')),
        }


def parse_bbl_xml(xml_path: Path) -> tuple[Dict, List[Artikel]]:
    """
    Convenience functie om BBL XML te parsen

    Returns:
        tuple: (metadata, list_van_artikelen)
    """
    parser = BWBParser(xml_path)
    metadata = parser.extract_metadata()
    artikelen = parser.extract_all_artikelen()

    return metadata, artikelen

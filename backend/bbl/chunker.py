"""
BBL Chunking Strategie
1 chunk = 1 artikel (inclusief alle leden)
Behoud volledige hiërarchische context
"""

from typing import List, Dict
from datetime import datetime
from .xml_parser import Artikel


class BBLChunker:
    """
    Chunking strategie voor juridische teksten (BBL)

    Strategie: 1 chunk = 1 artikel
    - Behoud juridische structuur
    - Makkelijk citeerbaar met artikel nummer
    - Volledige context altijd aanwezig
    """

    def __init__(self, version_date: str, bwb_identifier: str = "BWBR0041297"):
        """
        Args:
            version_date: Versie datum van BBL (bijv. "2025-07-01")
            bwb_identifier: BWB nummer (default: BWBR0041297 voor BBL)
        """
        self.version_date = version_date
        self.bwb_identifier = bwb_identifier

    def chunk_artikel(self, artikel: Artikel) -> Dict:
        """
        Creëer chunk van 1 artikel

        Returns:
            Dict met 'text' en 'metadata' keys
        """
        # Construeer volledige tekst
        text_parts = []

        # Header: Artikel nummer + titel
        text_parts.append(f"{artikel.get_artikel_label()}")
        if artikel.titel:
            text_parts.append(f" {artikel.titel}")
        text_parts.append("\n")

        # Context info
        text_parts.append(f"(Bron: {artikel.get_full_context()})")
        text_parts.append("\n\n")

        # Leden
        for lid in artikel.leden:
            if lid.nummer:
                text_parts.append(f"Lid {lid.nummer}. {lid.tekst}\n\n")
            else:
                text_parts.append(f"{lid.tekst}\n\n")

        full_text = "".join(text_parts).strip()

        # Metadata
        metadata = {
            "document_type": "BBL",
            "bwb_identifier": self.bwb_identifier,
            "version_date": self.version_date,
            "artikel_nummer": artikel.nummer,
            "artikel_label": artikel.get_artikel_label(),
            "artikel_titel": artikel.titel or "",
            "hoofdstuk_nr": artikel.hoofdstuk_nr,
            "hoofdstuk_titel": artikel.hoofdstuk_titel,
            "hoofdstuk": f"Hoofdstuk {artikel.hoofdstuk_nr}. {artikel.hoofdstuk_titel}",
            "afdeling_nr": artikel.afdeling_nr or "",
            "afdeling_titel": artikel.afdeling_titel or "",
            "afdeling": f"Afdeling {artikel.afdeling_nr}. {artikel.afdeling_titel}" if artikel.afdeling_nr else "",
            "leden_count": len(artikel.leden),
            "source_url": f"https://wetten.overheid.nl/{self.bwb_identifier}/{self.version_date}",
            "chunk_type": "artikel",
            "processed_at": datetime.now().isoformat()
        }

        return {
            "text": full_text,
            "metadata": metadata
        }

    def chunk_document(self, artikelen: List[Artikel]) -> List[Dict]:
        """
        Chunk alle artikelen van document

        Args:
            artikelen: List van Artikel objecten

        Returns:
            List van chunks (dicts met 'text' en 'metadata')
        """
        chunks = []

        for artikel in artikelen:
            chunk = self.chunk_artikel(artikel)
            chunks.append(chunk)

        return chunks

    def get_statistics(self, chunks: List[Dict]) -> Dict:
        """
        Bereken statistieken over chunks

        Returns:
            Dict met statistieken
        """
        if not chunks:
            return {}

        text_lengths = [len(chunk['text']) for chunk in chunks]
        hoofdstukken = set(chunk['metadata']['hoofdstuk'] for chunk in chunks)

        # Chunks per hoofdstuk
        hoofdstuk_counts = {}
        for chunk in chunks:
            hst = chunk['metadata']['hoofdstuk']
            hoofdstuk_counts[hst] = hoofdstuk_counts.get(hst, 0) + 1

        return {
            "total_chunks": len(chunks),
            "avg_chunk_length": sum(text_lengths) / len(text_lengths),
            "min_chunk_length": min(text_lengths),
            "max_chunk_length": max(text_lengths),
            "total_hoofdstukken": len(hoofdstukken),
            "chunks_per_hoofdstuk": hoofdstuk_counts
        }


def create_bbl_chunks(artikelen: List[Artikel], version_date: str) -> List[Dict]:
    """
    Convenience functie om BBL chunks te maken

    Args:
        artikelen: List van Artikel objecten
        version_date: Versie datum (bijv. "2025-07-01")

    Returns:
        List van chunks
    """
    chunker = BBLChunker(version_date=version_date)
    return chunker.chunk_document(artikelen)

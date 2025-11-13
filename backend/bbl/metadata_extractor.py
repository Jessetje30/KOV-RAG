"""
BBL Metadata Extractor
Detecteert functie types en bouw types uit BBL artikelen
"""
import re
from typing import List, Optional


class BBLMetadataExtractor:
    """
    Extraheert metadata uit BBL artikelen voor betere filtering.
    Detecteert functie types en bouw types.
    """

    # BBL Functie types
    FUNCTIE_TYPES = [
        "Woonfunctie",
        "Bijeenkomstfunctie",
        "Celfunctie",
        "Gezondheidszorgfunctie",
        "Industriefunctie",
        "Kantoorfunctie",
        "Logiesfunctie",
        "Onderwijsfunctie",
        "Sportfunctie",
        "Winkelfunctie",
        "Overige gebruiksfunctie",
        "Bouwwerk geen gebouw zijnde"
    ]

    # Hoofdstuk mapping naar functie types (BBL specifiek)
    # Hoofdstuk 5 t/m 16 zijn functie-specifiek
    HOOFDSTUK_FUNCTIE_MAPPING = {
        "5": ["Woonfunctie"],
        "6": ["Bijeenkomstfunctie"],
        "7": ["Celfunctie"],
        "8": ["Gezondheidszorgfunctie"],
        "9": ["Industriefunctie"],
        "10": ["Kantoorfunctie"],
        "11": ["Logiesfunctie"],
        "12": ["Onderwijsfunctie"],
        "13": ["Sportfunctie"],
        "14": ["Winkelfunctie"],
        "15": ["Overige gebruiksfunctie"],
        "16": ["Bouwwerk geen gebouw zijnde"]
    }

    # Patronen voor bouw types
    NIEUWBOUW_PATTERNS = [
        r'\bnieuwbouw\b',
        r'\bte bouwen\b',
        r'\bnogmaals te bouwen\b',
        r'\bnog te bouwen\b',
    ]

    BESTAANDE_BOUW_PATTERNS = [
        r'\bbestaande? bouw\b',
        r'\breeds? bestaand\b',
        r'\bbestaand(?:e)? gebouw\b',
        r'\bbij bestaande bouw\b',
        r'\baan bestaande bouw\b',
    ]

    def extract_functie_types(
        self,
        artikel_text: str,
        hoofdstuk_nr: str,
        afdeling_titel: Optional[str] = None
    ) -> List[str]:
        """
        Detecteer welke functie types van toepassing zijn op dit artikel.

        Args:
            artikel_text: Tekst van het artikel
            hoofdstuk_nr: Hoofdstuk nummer
            afdeling_titel: Afdeling titel (optioneel)

        Returns:
            List van functie type strings
        """
        functie_types = []

        # METHODE 1: Gebruik hoofdstuk mapping
        # Hoofdstukken 5-16 zijn functie-specifiek
        if hoofdstuk_nr in self.HOOFDSTUK_FUNCTIE_MAPPING:
            hoofdstuk_functies = self.HOOFDSTUK_FUNCTIE_MAPPING[hoofdstuk_nr]
            functie_types.extend(hoofdstuk_functies)

        # METHODE 2: Detecteer uit afdeling titel
        if afdeling_titel:
            for functie in self.FUNCTIE_TYPES:
                if functie.lower() in afdeling_titel.lower():
                    if functie not in functie_types:
                        functie_types.append(functie)

        # METHODE 3: Detecteer expliciet genoemde functies in artikel tekst
        artikel_lower = artikel_text.lower()
        for functie in self.FUNCTIE_TYPES:
            # Check volledige functie naam
            if functie.lower() in artikel_lower:
                if functie not in functie_types:
                    functie_types.append(functie)

        # METHODE 4: Detecteer synoniemen en kortere vormen
        functie_synoniemen = {
            "woning": "Woonfunctie",
            "woningen": "Woonfunctie",
            "woongebouw": "Woonfunctie",
            "kantoor": "Kantoorfunctie",
            "kantoren": "Kantoorfunctie",
            "kantoorgebouw": "Kantoorfunctie",
            "winkel": "Winkelfunctie",
            "winkels": "Winkelfunctie",
            "verkoopruimte": "Winkelfunctie",
            "school": "Onderwijsfunctie",
            "scholen": "Onderwijsfunctie",
            "onderwijsgebouw": "Onderwijsfunctie",
            "ziekenhuis": "Gezondheidszorgfunctie",
            "kliniek": "Gezondheidszorgfunctie",
            "zorginstelling": "Gezondheidszorgfunctie",
            "sporthal": "Sportfunctie",
            "sportzaal": "Sportfunctie",
            "sportaccommodatie": "Sportfunctie",
            "hotel": "Logiesfunctie",
            "logiesgebouw": "Logiesfunctie",
            "gevangenis": "Celfunctie",
            "celgebouw": "Celfunctie",
            "detentie": "Celfunctie",
            "theater": "Bijeenkomstfunctie",
            "biosco": "Bijeenkomstfunctie",
            "evenementenhal": "Bijeenkomstfunctie",
            "fabriek": "Industriefunctie",
            "fabriekshal": "Industriefunctie",
            "industriegebouw": "Industriefunctie",
        }

        for synoniem, functie in functie_synoniemen.items():
            if re.search(r'\b' + re.escape(synoniem), artikel_lower):
                if functie not in functie_types:
                    functie_types.append(functie)

        # Als geen specifieke functies gevonden: hoofdstukken 1-4 zijn algemeen
        # (van toepassing op ALLE functies)
        if not functie_types and hoofdstuk_nr in ["1", "2", "3", "4"]:
            # Deze artikelen gelden voor alle functies
            functie_types = ["Algemeen"]  # Special marker

        return functie_types

    def extract_bouw_type(self, artikel_text: str) -> Optional[str]:
        """
        Detecteer of artikel over Nieuwbouw of Bestaande bouw gaat.

        Args:
            artikel_text: Tekst van het artikel

        Returns:
            "Nieuwbouw", "Bestaande bouw", of None (algemeen)
        """
        artikel_lower = artikel_text.lower()

        # Check voor nieuwbouw
        for pattern in self.NIEUWBOUW_PATTERNS:
            if re.search(pattern, artikel_lower):
                return "Nieuwbouw"

        # Check voor bestaande bouw
        for pattern in self.BESTAANDE_BOUW_PATTERNS:
            if re.search(pattern, artikel_lower):
                return "Bestaande bouw"

        # Als niet specifiek vermeld, is het waarschijnlijk voor beide
        return None  # Algemeen (geldt voor beide)

    def extract_thema_tags(self, artikel_text: str, artikel_titel: Optional[str] = None) -> List[str]:
        """
        Detecteer thema tags uit artikel voor betere categorisatie.

        Args:
            artikel_text: Tekst van het artikel
            artikel_titel: Titel van het artikel (optioneel)

        Returns:
            List van thema tags
        """
        thema_patterns = {
            "brandveiligheid": [
                r'\bbrand(?:veiligheid|veilig|weerstand|werendheid)?\b',
                r'\bvluchtroute\b',
                r'\bvluchten\b',
                r'\bbrandmelding\b',
                r'\bbrandblusser\b',
                r'\bbrandweer\b'
            ],
            "constructie": [
                r'\bconstructie(?:f|ve)?\b',
                r'\bstabiliteit\b',
                r'\bdraagconstructie\b',
                r'\bsterkte\b',
                r'\bbelasting\b'
            ],
            "ventilatie": [
                r'\bventilatie\b',
                r'\bventileren\b',
                r'\bluchtkwaliteit\b',
                r'\bverse lucht\b',
                r'\bCO2\b'
            ],
            "energieprestatie": [
                r'\benergie(?:prestatie)?\b',
                r'\bEPC\b',
                r'\bisolatie\b',
                r'\bwarmte\b',
                r'\bMPG\b',
                r'\bTOjuli\b'
            ],
            "geluid": [
                r'\bgeluid(?:sisolatie|swering|overlast)?\b',
                r'\bakoestiek\b',
                r'\bgeluidsbelasting\b'
            ],
            "toegankelijkheid": [
                r'\btoegankelij(?:k|kheid)\b',
                r'\brolstoel(?:toegankelijk)?\b',
                r'\bmindervalide\b',
                r'\bdrempel(?:vrij)?\b'
            ],
            "daglicht": [
                r'\bdaglicht(?:toetreding)?\b',
                r'\bbelichting\b',
                r'\bramen\b',
                r'\bglasoppervlak\b'
            ],
            "installaties": [
                r'\binstallaties?\b',
                r'\belektr(?:a|isch)\b',
                r'\bgas\b',
                r'\bwater\b',
                r'\briolering\b'
            ]
        }

        combined_text = artikel_text.lower()
        if artikel_titel:
            combined_text = artikel_titel.lower() + " " + combined_text

        thema_tags = []

        for thema, patterns in thema_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined_text):
                    if thema not in thema_tags:
                        thema_tags.append(thema)
                    break  # Move to next thema

        return thema_tags

    def enrich_metadata(
        self,
        artikel_text: str,
        hoofdstuk_nr: str,
        artikel_titel: Optional[str] = None,
        afdeling_titel: Optional[str] = None
    ) -> dict:
        """
        Extraheer alle metadata voor een artikel.

        Args:
            artikel_text: Tekst van het artikel
            hoofdstuk_nr: Hoofdstuk nummer
            artikel_titel: Titel van artikel (optioneel)
            afdeling_titel: Afdeling titel (optioneel)

        Returns:
            Dict met metadata fields
        """
        return {
            "functie_types": self.extract_functie_types(
                artikel_text, hoofdstuk_nr, afdeling_titel
            ),
            "bouw_type": self.extract_bouw_type(artikel_text),
            "thema_tags": self.extract_thema_tags(artikel_text, artikel_titel)
        }

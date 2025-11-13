"""
Query Analysis voor BBL RAG systeem.
Analyseert gebruikersvragen en extraheert metadata voor intelligente filtering.
"""
import json
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class QueryAnalysis:
    """Resultaat van query analyse"""
    # Originele query
    original_query: str

    # Functie types (kan meerdere zijn)
    functie_types: List[str]  # ["Woonfunctie", "Kantoorfunctie", etc.]

    # Bouw type
    bouw_type: Optional[str]  # "Nieuwbouw" / "Bestaande bouw" / None

    # Hoofdonderwerp/thema
    thema: Optional[str]  # "brandveiligheid", "ventilatie", etc.

    # Specifieke artikel nummers indien vermeld
    artikel_nummers: List[str]  # ["4.101", "2.1", etc.]

    # Hoofdstuk nummer indien vermeld
    hoofdstuk_nr: Optional[str]

    # Enhanced query voor betere retrieval
    enhanced_query: str

    # Synoniemen en gerelateerde termen
    related_terms: List[str]

    # Confidence score (0.0 - 1.0)
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class QueryAnalyzer:
    """
    Analyseert BBL queries en extraheert metadata.
    Gebruikt LLM voor intelligente query parsing.
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

    # Synoniemen voor functie types
    FUNCTIE_SYNONIEMEN = {
        "woning": "Woonfunctie",
        "huis": "Woonfunctie",
        "appartement": "Woonfunctie",
        "flat": "Woonfunctie",
        "wonen": "Woonfunctie",
        "kantoor": "Kantoorfunctie",
        "kantoorgebouw": "Kantoorfunctie",
        "werkplek": "Kantoorfunctie",
        "winkel": "Winkelfunctie",
        "retail": "Winkelfunctie",
        "verkoop": "Winkelfunctie",
        "school": "Onderwijsfunctie",
        "onderwijs": "Onderwijsfunctie",
        "klaslokaal": "Onderwijsfunctie",
        "ziekenhuis": "Gezondheidszorgfunctie",
        "kliniek": "Gezondheidszorgfunctie",
        "medisch": "Gezondheidszorgfunctie",
        "sport": "Sportfunctie",
        "sporthal": "Sportfunctie",
        "sportzaal": "Sportfunctie",
        "fitness": "Sportfunctie",
        "hotel": "Logiesfunctie",
        "logies": "Logiesfunctie",
        "verblijf": "Logiesfunctie",
        "gevangenis": "Celfunctie",
        "cel": "Celfunctie",
        "detentie": "Celfunctie",
        "bijeenkomst": "Bijeenkomstfunctie",
        "theater": "Bijeenkomstfunctie",
        "zaal": "Bijeenkomstfunctie",
        "evenement": "Bijeenkomstfunctie",
        "fabriek": "Industriefunctie",
        "industrie": "Industriefunctie",
        "productie": "Industriefunctie",
    }

    # Thema synoniemen
    THEMA_TERMEN = {
        "brandveiligheid": ["brand", "brandweer", "brandwerendheid", "vluchtroute", "vluchten"],
        "ventilatie": ["ventileren", "lucht", "luchtkwaliteit", "verse lucht", "CO2"],
        "constructieve veiligheid": ["constructie", "stabiliteit", "draagconstructie", "sterkte"],
        "energieprestatie": ["energie", "EPC", "isolatie", "warmte", "energiezuinig", "MPG"],
        "geluid": ["geluidsisolatie", "akoestiek", "geluidsoverlast", "geluidswering"],
        "toegankelijkheid": ["rolstoel", "mindervalide", "bereikbaarheid", "drempels"],
        "installaties": ["elektra", "gas", "water", "riolering", "leidingen"],
        "daglicht": ["licht", "belichting", "ramen", "daglichttoetreding"],
    }

    def __init__(self, llm_provider=None):
        """
        Initialize query analyzer.

        Args:
            llm_provider: Optional LLM provider for advanced analysis
        """
        self.llm_provider = llm_provider
        logger.info("QueryAnalyzer initialized")

    def analyze(self, query: str) -> QueryAnalysis:
        """
        Analyseer een query en extraheer metadata.

        Args:
            query: User query string

        Returns:
            QueryAnalysis object met geëxtraheerde metadata
        """
        logger.info(f"Analyzing query: {query}")

        # 1. Basis regex-based extractie
        functie_types = self._extract_functie_types(query)
        bouw_type = self._extract_bouw_type(query)
        artikel_nummers = self._extract_artikel_nummers(query)
        hoofdstuk_nr = self._extract_hoofdstuk_nr(query)
        thema = self._extract_thema(query)

        # 2. LLM-based verrijking (indien beschikbaar)
        if self.llm_provider:
            llm_analysis = self._llm_analyze(query)

            # Merge LLM resultaten met regex resultaten
            if llm_analysis:
                if not functie_types and llm_analysis.get("functie_types"):
                    functie_types = llm_analysis["functie_types"]
                if not bouw_type and llm_analysis.get("bouw_type"):
                    bouw_type = llm_analysis["bouw_type"]
                if not thema and llm_analysis.get("thema"):
                    thema = llm_analysis["thema"]

        # 3. Query enhancement
        enhanced_query, related_terms = self._enhance_query(
            query, functie_types, bouw_type, thema
        )

        # 4. Confidence score
        confidence = self._calculate_confidence(
            functie_types, bouw_type, thema, artikel_nummers
        )

        analysis = QueryAnalysis(
            original_query=query,
            functie_types=functie_types,
            bouw_type=bouw_type,
            thema=thema,
            artikel_nummers=artikel_nummers,
            hoofdstuk_nr=hoofdstuk_nr,
            enhanced_query=enhanced_query,
            related_terms=related_terms,
            confidence=confidence
        )

        logger.info(f"Query analysis complete: {analysis.to_dict()}")
        return analysis

    def _extract_functie_types(self, query: str) -> List[str]:
        """Detecteer functie types in query"""
        query_lower = query.lower()
        detected = []

        # Check directe functies
        for functie in self.FUNCTIE_TYPES:
            if functie.lower() in query_lower:
                detected.append(functie)

        # Check synoniemen
        for synoniem, functie in self.FUNCTIE_SYNONIEMEN.items():
            if re.search(r'\b' + re.escape(synoniem) + r'\b', query_lower):
                if functie not in detected:
                    detected.append(functie)

        return detected

    def _extract_bouw_type(self, query: str) -> Optional[str]:
        """Detecteer bouw type (Nieuwbouw / Bestaande bouw)"""
        query_lower = query.lower()

        # Nieuwbouw patronen
        nieuwbouw_patterns = [
            r'\bnieuwbouw\b',
            r'\bnieuwe? bouw\b',
            r'\bnieuwe? gebouwen?\b',
            r'\bte bouwen\b',
            r'\bnog te bouwen\b',
        ]

        for pattern in nieuwbouw_patterns:
            if re.search(pattern, query_lower):
                return "Nieuwbouw"

        # Bestaande bouw patronen
        bestaand_patterns = [
            r'\bbestaande? bouw\b',
            r'\bbestaande? gebouwen?\b',
            r'\breeds bestaand\b',
            r'\bverbouwing\b',
            r'\brenovatie\b',
            r'\bbestaand(?:e)?\b',
        ]

        for pattern in bestaand_patterns:
            if re.search(pattern, query_lower):
                return "Bestaande bouw"

        return None

    def _extract_artikel_nummers(self, query: str) -> List[str]:
        """Detecteer artikel nummers in query"""
        # Patronen: "artikel 4.101", "art. 2.1", "4.101", etc.
        patterns = [
            r'artikel\s+(\d+\.?\d*)',
            r'art\.?\s+(\d+\.?\d*)',
            r'\b(\d+\.\d+)\b',  # Direct nummer zoals 4.101
        ]

        artikelen = []
        for pattern in patterns:
            matches = re.findall(pattern, query.lower())
            for match in matches:
                if match not in artikelen:
                    artikelen.append(match)

        return artikelen

    def _extract_hoofdstuk_nr(self, query: str) -> Optional[str]:
        """Detecteer hoofdstuk nummer in query"""
        patterns = [
            r'hoofdstuk\s+(\d+)',
            r'hfst\.?\s+(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                return match.group(1)

        return None

    def _extract_thema(self, query: str) -> Optional[str]:
        """Detecteer hoofdthema van de query"""
        query_lower = query.lower()

        # Score elk thema op basis van aanwezigheid van termen
        thema_scores = {}

        for thema, termen in self.THEMA_TERMEN.items():
            score = 0
            for term in termen:
                if re.search(r'\b' + re.escape(term) + r'\b', query_lower):
                    score += 1

            if score > 0:
                thema_scores[thema] = score

        # Return thema met hoogste score
        if thema_scores:
            best_thema = max(thema_scores.items(), key=lambda x: x[1])
            return best_thema[0]

        return None

    def _llm_analyze(self, query: str) -> Optional[Dict]:
        """
        Gebruik LLM voor geavanceerde query analyse.

        Returns:
            Dict met geëxtraheerde metadata, of None bij falen
        """
        try:
            prompt = f"""Analyseer deze BBL (Besluit Bouwwerken Leefomgeving) vraag en extraheer de volgende informatie:

Vraag: "{query}"

Extraheer:
1. functie_types: Lijst van relevante functie types uit deze opties:
   - Woonfunctie, Bijeenkomstfunctie, Celfunctie, Gezondheidszorgfunctie,
   - Industriefunctie, Kantoorfunctie, Logiesfunctie, Onderwijsfunctie,
   - Sportfunctie, Winkelfunctie, Overige gebruiksfunctie, Bouwwerk geen gebouw zijnde
   (Geef lege lijst [] als niet duidelijk)

2. bouw_type: "Nieuwbouw", "Bestaande bouw", of null (als niet vermeld)

3. thema: Hoofdonderwerp van de vraag in enkele woorden (bijv. "brandveiligheid", "ventilatie", "energieprestatie")

Geef je antwoord als JSON in dit exacte formaat (geen extra tekst):
{{
  "functie_types": ["..."],
  "bouw_type": "..." of null,
  "thema": "..." of null
}}"""

            response = self.llm_provider.generate_answer(prompt, max_length=300)

            # Parse JSON uit response
            # Zoek JSON block in response
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                return result
            else:
                logger.warning(f"Could not parse LLM response as JSON: {response}")
                return None

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return None

    def _enhance_query(
        self,
        query: str,
        functie_types: List[str],
        bouw_type: Optional[str],
        thema: Optional[str]
    ) -> tuple[str, List[str]]:
        """
        Verbeter query met extra context en synoniemen.

        Returns:
            (enhanced_query, related_terms)
        """
        enhanced_parts = [query]
        related_terms = []

        # Voeg functie types toe
        if functie_types:
            enhanced_parts.append(f"({' of '.join(functie_types)})")
            related_terms.extend(functie_types)

        # Voeg bouw type toe
        if bouw_type:
            enhanced_parts.append(bouw_type)
            related_terms.append(bouw_type)

        # Voeg thema synoniemen toe
        if thema and thema in self.THEMA_TERMEN:
            thema_synoniemen = self.THEMA_TERMEN[thema][:3]  # Top 3 synoniemen
            related_terms.extend(thema_synoniemen)

        enhanced_query = " ".join(enhanced_parts)
        return enhanced_query, related_terms

    def _calculate_confidence(
        self,
        functie_types: List[str],
        bouw_type: Optional[str],
        thema: Optional[str],
        artikel_nummers: List[str]
    ) -> float:
        """
        Bereken confidence score voor de analyse.

        Returns:
            Float tussen 0.0 en 1.0
        """
        score = 0.0

        # Artikel nummers = hoogste confidence
        if artikel_nummers:
            score += 0.4

        # Functie type gevonden
        if functie_types:
            score += 0.3

        # Bouw type gevonden
        if bouw_type:
            score += 0.15

        # Thema gevonden
        if thema:
            score += 0.15

        return min(score, 1.0)

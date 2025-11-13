"""
Reranker voor RAG resultaten.
Her-sorteert en filtert resultaten op basis van metadata matching en LLM verificatie.
"""
import logging
from typing import List, Dict, Any, Optional
import re

logger = logging.getLogger(__name__)


class BBLReranker:
    """
    Reranks RAG search results op basis van:
    1. Metadata matching met query analysis
    2. Optioneel: LLM-based relevance verification
    """

    def __init__(self, llm_provider=None):
        """
        Initialize reranker.

        Args:
            llm_provider: Optional LLM provider for relevance checking
        """
        self.llm_provider = llm_provider

    def rerank(
        self,
        sources: List[Dict[str, Any]],
        query_text: str,
        query_analysis: Optional[Dict] = None,
        use_llm: bool = False,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rerank sources based on metadata matching and optionally LLM verification.

        Args:
            sources: List of source dictionaries with metadata
            query_text: Original query text
            query_analysis: Query analysis dict (from QueryAnalyzer)
            use_llm: Whether to use LLM for relevance verification
            top_k: Number of top results to return

        Returns:
            Reranked list of sources (limited to top_k)
        """
        if not sources:
            return []

        logger.info(f"Reranking {len(sources)} sources")

        # Step 1: Calculate metadata matching scores
        for source in sources:
            metadata_score = self._calculate_metadata_score(source, query_analysis)
            source["metadata_score"] = metadata_score

            # Combined score: vector similarity + metadata matching
            # Weight: 70% vector similarity, 30% metadata matching
            original_score = source.get("score", 0.0)
            source["combined_score"] = (0.7 * original_score) + (0.3 * metadata_score)

        # Step 2: Sort by combined score
        sorted_sources = sorted(sources, key=lambda x: x["combined_score"], reverse=True)

        # Step 3: Optionally verify relevance with LLM
        if use_llm and self.llm_provider:
            sorted_sources = self._llm_relevance_check(sorted_sources, query_text, top_k * 2)

        # Step 4: Return top_k results
        top_sources = sorted_sources[:top_k]

        logger.info(f"Reranking complete. Top {len(top_sources)} sources selected")
        return top_sources

    def _calculate_metadata_score(
        self,
        source: Dict[str, Any],
        query_analysis: Optional[Dict]
    ) -> float:
        """
        Calculate metadata matching score (0.0 - 1.0).

        Args:
            source: Source dictionary with metadata
            query_analysis: Query analysis dict

        Returns:
            Score between 0.0 and 1.0
        """
        if not query_analysis:
            return 0.0

        score = 0.0
        max_score = 0.0

        # Get query metadata
        query_functie_types = query_analysis.get("functie_types", [])
        query_bouw_type = query_analysis.get("bouw_type")
        query_thema = query_analysis.get("thema")
        query_artikel_nummers = query_analysis.get("artikel_nummers", [])

        # Get source metadata
        source_functie_types = source.get("functie_types", [])
        source_bouw_type = source.get("bouw_type")
        source_thema_tags = source.get("thema_tags", [])
        source_artikel_nummer = source.get("artikel_nummer", "")

        # 1. Functie type matching (weight: 0.4)
        max_score += 0.4
        if query_functie_types:
            if "Algemeen" in source_functie_types:
                # General articles match all queries
                score += 0.4
            else:
                # Check overlap between query and source functie types
                matching_functie = set(query_functie_types) & set(source_functie_types)
                if matching_functie:
                    # Full match
                    score += 0.4
                elif source_functie_types:
                    # Partial penalty for non-matching functie
                    score += 0.1

        # 2. Bouw type matching (weight: 0.25)
        max_score += 0.25
        if query_bouw_type:
            if source_bouw_type == query_bouw_type:
                score += 0.25
            elif source_bouw_type is None:
                # General articles (no specific bouw_type) partially match
                score += 0.15
            else:
                # Wrong bouw_type: penalty
                score += 0.0

        # 3. Thema matching (weight: 0.25)
        max_score += 0.25
        if query_thema:
            if query_thema in source_thema_tags:
                score += 0.25
            elif any(self._is_related_thema(query_thema, tag) for tag in source_thema_tags):
                # Related thema: partial match
                score += 0.15

        # 4. Exact artikel nummer match (weight: 0.1, bonus)
        max_score += 0.1
        if query_artikel_nummers:
            if source_artikel_nummer in query_artikel_nummers:
                # Exact artikel match: high boost
                score += 0.1
            else:
                # Check if source artikel is mentioned in query
                # (but wasn't extracted as explicit artikel nummer)
                for num in query_artikel_nummers:
                    if num in source_artikel_nummer or source_artikel_nummer in num:
                        score += 0.05
                        break

        # Normalize score to 0-1 range
        if max_score > 0:
            normalized_score = score / max_score
        else:
            normalized_score = 0.0

        return normalized_score

    def _is_related_thema(self, thema1: str, thema2: str) -> bool:
        """
        Check if two themas are related.

        Args:
            thema1: First thema
            thema2: Second thema

        Returns:
            True if related
        """
        # Define related thema groups
        related_groups = [
            {"brandveiligheid", "constructie"},
            {"ventilatie", "daglicht"},
            {"energieprestatie", "isolatie"},
            {"geluid", "akoestiek"},
        ]

        thema1_lower = thema1.lower()
        thema2_lower = thema2.lower()

        for group in related_groups:
            if thema1_lower in group and thema2_lower in group:
                return True

        return False

    def _llm_relevance_check(
        self,
        sources: List[Dict[str, Any]],
        query_text: str,
        max_sources: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to verify relevance of top sources.

        Args:
            sources: List of sources (already sorted by combined_score)
            query_text: Original query
            max_sources: Maximum number of sources to check with LLM

        Returns:
            Sources with LLM relevance verification
        """
        # Only check top sources to avoid excessive LLM calls
        sources_to_check = sources[:max_sources]

        logger.info(f"LLM relevance check for {len(sources_to_check)} sources")

        for source in sources_to_check:
            relevance = self._check_relevance_with_llm(
                query_text,
                source["text"],
                source.get("artikel_label", "")
            )
            source["llm_relevance"] = relevance

            # Adjust combined score based on LLM relevance
            if relevance == "RELEVANT":
                source["combined_score"] *= 1.2  # Boost
            elif relevance == "NIET_RELEVANT":
                source["combined_score"] *= 0.5  # Penalty
            # MOGELIJK_RELEVANT: no change

        # Re-sort after LLM adjustment
        sources_to_check.sort(key=lambda x: x["combined_score"], reverse=True)

        # Combine checked and unchecked sources
        remaining_sources = sources[max_sources:]
        return sources_to_check + remaining_sources

    def _check_relevance_with_llm(
        self,
        query: str,
        artikel_text: str,
        artikel_label: str
    ) -> str:
        """
        Use LLM to check if artikel is relevant to query.

        Args:
            query: User query
            artikel_text: Artikel text (truncated to first 500 chars)
            artikel_label: Artikel label (e.g., "Artikel 4.101")

        Returns:
            "RELEVANT", "MOGELIJK_RELEVANT", or "NIET_RELEVANT"
        """
        try:
            # Truncate artikel text for efficiency
            text_preview = artikel_text[:500] + "..." if len(artikel_text) > 500 else artikel_text

            prompt = f"""Beoordeel of dit BBL artikel relevant is voor de volgende vraag.

Vraag: {query}

Artikel: {artikel_label}
Tekst: {text_preview}

Geef ÉÉN van de volgende antwoorden (zonder extra uitleg):
- RELEVANT (als het artikel direct antwoord geeft op de vraag)
- MOGELIJK_RELEVANT (als het artikel gerelateerde informatie bevat)
- NIET_RELEVANT (als het artikel niet relevant is)

Antwoord:"""

            response = self.llm_provider.generate_answer(prompt, max_length=50)
            response_upper = response.strip().upper()

            if "RELEVANT" in response_upper and "NIET" not in response_upper and "MOGELIJK" not in response_upper:
                return "RELEVANT"
            elif "MOGELIJK" in response_upper or "GERELATEERD" in response_upper:
                return "MOGELIJK_RELEVANT"
            elif "NIET" in response_upper:
                return "NIET_RELEVANT"
            else:
                # Fallback: assume mogelijk relevant
                logger.warning(f"Could not parse LLM relevance response: {response}")
                return "MOGELIJK_RELEVANT"

        except Exception as e:
            logger.error(f"LLM relevance check failed: {e}")
            return "MOGELIJK_RELEVANT"  # Fallback to neutral

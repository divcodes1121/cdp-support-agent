"""
Information retrieval system for CDP documentation.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any

from src.config import TOP_K_RESULTS, SIMILARITY_THRESHOLD
from src.indexer.vectorstore import VectorStore

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DocumentRetriever:
    """
    Retriever for CDP documentation.
    """

    def __init__(self, vector_store: VectorStore):
        """
        Initialize the document retriever.

        Args:
            vector_store: Vector store instance.
        """
        self.vector_store = vector_store
    
    def _extract_cdp_from_query(self, query: str) -> Optional[str]:
        """
        Extract CDP name from the query.

        Args:
            query: User query.

        Returns:
            CDP name or None if not found.
        """
        # Define CDP names to look for
        cdp_names = ["segment", "mparticle", "lytics", "zeotap"]
        
        # Lowercase the query
        query_lower = query.lower()
        
        # Check for CDP names in the query
        for cdp in cdp_names:
            if cdp in query_lower:
                return cdp
        
        return None
    
    def _classify_query_type(self, query: str) -> str:
        """
        Classify the type of query.

        Args:
            query: User query.

        Returns:
            Query type: "how-to", "comparison", or "general".
        """
        query_lower = query.lower()
        
        # Check for comparison queries
        comparison_patterns = [
            r"compare", r"difference between", r"vs", r"versus",
            r"how does .+ compare", r"which is better", r"pros and cons"
        ]
        
        for pattern in comparison_patterns:
            if re.search(pattern, query_lower):
                return "comparison"
        
        # Check for how-to queries
        how_to_patterns = [
            r"how (to|do|can|should)", r"steps to", r"guide for",
            r"tutorial", r"instructions for", r"process of"
        ]
        
        for pattern in how_to_patterns:
            if re.search(pattern, query_lower):
                return "how-to"
        
        # Default to general query
        return "general"
    
    def _is_relevant_query(self, query: str) -> bool:
        """
        Check if the query is relevant to CDPs.

        Args:
            query: User query.

        Returns:
            True if relevant, False otherwise.
        """
        # Define relevant terms
        relevant_terms = [
            "segment", "mparticle", "lytics", "zeotap", "cdp", 
            "customer data platform", "data", "analytics", "integration",
            "tracking", "source", "destination", "audience", "profile",
            "event", "user", "identity", "segment", "campaign"
        ]
        
        # Lowercase the query
        query_lower = query.lower()
        
        # Check for relevant terms in the query
        for term in relevant_terms:
            if term in query_lower:
                return True
        
        return False
    
    def retrieve(self, query: str, top_k: int = TOP_K_RESULTS) -> Tuple[List[Dict], Dict]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: User query.
            top_k: Number of top results to return.

        Returns:
            Tuple of (list of relevant documents, query analysis).
        """
        # Analyze the query
        cdp = self._extract_cdp_from_query(query)
        query_type = self._classify_query_type(query)
        is_relevant = self._is_relevant_query(query)
        
        query_analysis = {
            "cdp": cdp,
            "query_type": query_type,
            "is_relevant": is_relevant
        }
        
        logger.info(f"Query analysis: {query_analysis}")
        
        # If the query is not relevant to CDPs, return empty results
        if not is_relevant:
            return [], query_analysis
        
        # Prepare filter based on CDP and query type
        filter_dict = {}
        
        if cdp:
            filter_dict["platform"] = cdp
        
        if query_type == "how-to":
            # For how-to queries, prioritize how-to documents but don't exclude others
            pass
        
        # Retrieve documents
        results = self.vector_store.query(
            query_text=query,
            n_results=top_k,
            filter_dict=filter_dict if filter_dict else None
        )
        
        # Filter out irrelevant results
        relevant_results = [
            result for result in results
            if result.get("distance") is None or result.get("distance") < SIMILARITY_THRESHOLD
        ]
        
        return relevant_results, query_analysis


class ComparisonRetriever:
    """
    Specialized retriever for CDP comparison queries.
    """

    def __init__(self, vector_store: VectorStore):
        """
        Initialize the comparison retriever.

        Args:
            vector_store: Vector store instance.
        """
        self.vector_store = vector_store
        self.document_retriever = DocumentRetriever(vector_store)
    
    def _extract_cdps_for_comparison(self, query: str) -> List[str]:
        """
        Extract CDP names for comparison from the query.

        Args:
            query: User query.

        Returns:
            List of CDP names mentioned in the query.
        """
        # Define CDP names to look for
        cdp_names = ["segment", "mparticle", "lytics", "zeotap"]
        
        # Lowercase the query
        query_lower = query.lower()
        
        # Find CDP names in the query
        mentioned_cdps = [
            cdp for cdp in cdp_names
            if cdp in query_lower
        ]
        
        return mentioned_cdps
    
    def _extract_feature_for_comparison(self, query: str) -> Optional[str]:
        """
        Extract the feature or aspect for comparison.

        Args:
            query: User query.

        Returns:
            Feature name or None if not found.
        """
        query_lower = query.lower()
        
        # Define patterns to extract features
        feature_patterns = [
            r"how does .+ (handle|manage|support|implement|provide) (.+)",
            r"compare .+ (in terms of|regarding|for) (.+)",
            r"difference between .+ for (.+)",
            r"which is better for (.+)",
            r"how do .+ compare for (.+)"
        ]
        
        for pattern in feature_patterns:
            match = re.search(pattern, query_lower)
            if match:
                return match.group(2).strip()
        
        return None
    
    def retrieve_for_comparison(
        self, 
        query: str, 
        top_k_per_cdp: int = 3
    ) -> Tuple[Dict[str, List[Dict]], Dict]:
        """
        Retrieve documents for a comparison query.

        Args:
            query: User query.
            top_k_per_cdp: Number of top results to return per CDP.

        Returns:
            Tuple of (map of CDP to relevant documents, query analysis).
        """
        # Extract CDPs for comparison
        cdps = self._extract_cdps_for_comparison(query)
        
        # Extract feature for comparison
        feature = self._extract_feature_for_comparison(query)
        
        # If no CDPs mentioned, use all
        if not cdps:
            cdps = ["segment", "mparticle", "lytics", "zeotap"]
        
        # Build comparison query
        if feature:
            comparison_query = f"{feature}"
        else:
            comparison_query = query
        
        query_analysis = {
            "cdps": cdps,
            "feature": feature,
            "query_type": "comparison"
        }
        
        logger.info(f"Comparison query analysis: {query_analysis}")
        
        # Retrieve documents for each CDP
        results = {}
        
        for cdp in cdps:
            filter_dict = {"platform": cdp}
            
            cdp_results = self.vector_store.query(
                query_text=comparison_query,
                n_results=top_k_per_cdp,
                filter_dict=filter_dict
            )
            
            # Filter out irrelevant results
            relevant_results = [
                result for result in cdp_results
                if result.get("distance") is None or result.get("distance") < SIMILARITY_THRESHOLD
            ]
            
            results[cdp] = relevant_results
        
        return results, query_analysis
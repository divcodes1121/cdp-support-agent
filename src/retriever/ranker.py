"""
Result ranking and filtering for CDP documentation retrieval.
"""

import logging
import re
from typing import Dict, List, Tuple

from src.config import SIMILARITY_THRESHOLD

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ResultRanker:
    """
    Ranker for retrieval results.
    """

    def __init__(self, similarity_threshold: float = SIMILARITY_THRESHOLD):
        """
        Initialize the result ranker.

        Args:
            similarity_threshold: Threshold for similarity scores.
        """
        self.similarity_threshold = similarity_threshold
    
    def _calculate_content_relevance_score(self, content: str, query: str) -> float:
        """
        Calculate a relevance score based on content and query.

        Args:
            content: Document content.
            query: User query.

        Returns:
            Relevance score (0-1).
        """
        # Normalize strings
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Extract keywords from query
        keywords = re.findall(r'\b\w+\b', query_lower)
        keywords = [kw for kw in keywords if len(kw) > 3]  # Filter out short words
        
        # Count keyword occurrences
        keyword_count = sum(content_lower.count(kw) for kw in keywords)
        
        # Calculate density (keywords per 100 words)
        content_word_count = len(re.findall(r'\b\w+\b', content_lower))
        if content_word_count == 0:
            return 0
        
        keyword_density = keyword_count / content_word_count * 100
        
        # Normalize to 0-1 scale
        relevance_score = min(1.0, keyword_density / 5)  # Cap at 1.0
        
        return relevance_score
    
    def _calculate_metadata_relevance_score(self, metadata: Dict, query: str) -> float:
        """
        Calculate a relevance score based on metadata.

        Args:
            metadata: Document metadata.
            query: User query.

        Returns:
            Relevance score (0-1).
        """
        # Normalize query
        query_lower = query.lower()
        
        # Extract query type
        is_how_to = re.search(r'how (to|do|can|should)', query_lower) is not None
        
        # Get document type
        doc_type = metadata.get("doc_type", "unknown")
        
        # Calculate type match score
        type_match_score = 0.0
        if is_how_to and doc_type == "how-to":
            type_match_score = 1.0
        elif (not is_how_to) and doc_type == "reference":
            type_match_score = 0.8
        elif doc_type == "overview":
            type_match_score = 0.6
        
        # Calculate title relevance
        title = metadata.get("title", "")
        title_lower = title.lower()
        
        # Extract keywords from query
        keywords = re.findall(r'\b\w+\b', query_lower)
        keywords = [kw for kw in keywords if len(kw) > 3]  # Filter out short words
        
        # Count keyword occurrences in title
        title_match_count = sum(title_lower.count(kw) for kw in keywords)
        title_match_score = min(1.0, title_match_count / max(1, len(keywords)))
        
        # Calculate heading relevance
        heading_hierarchy = metadata.get("heading_hierarchy", [])
        heading_match_count = 0
        
        for heading in heading_hierarchy:
            heading_lower = heading.lower()
            heading_match_count += sum(heading_lower.count(kw) for kw in keywords)
        
        heading_match_score = min(1.0, heading_match_count / max(1, len(keywords) * 2))
        
        # Calculate combined score
        combined_score = 0.4 * type_match_score + 0.3 * title_match_score + 0.3 * heading_match_score
        
        return combined_score
    
    def _calculate_final_score(
        self, 
        distance: float, 
        content_score: float, 
        metadata_score: float
    ) -> float:
        """
        Calculate the final relevance score.

        Args:
            distance: Vector distance (lower is better).
            content_score: Content-based relevance score.
            metadata_score: Metadata-based relevance score.

        Returns:
            Final relevance score (higher is better).
        """
        # Normalize distance to 0-1 (assuming distance is between 0-1)
        # If distance is None, assume it's the best possible
        if distance is None:
            distance_score = 1.0
        else:
            distance_score = 1.0 - min(1.0, distance)
        
        # Calculate weighted score
        final_score = 0.5 * distance_score + 0.3 * content_score + 0.2 * metadata_score
        
        return final_score
    
    def rank_results(self, results: List[Dict], query: str) -> List[Dict]:
        """
        Rank retrieval results based on relevance to the query.

        Args:
            results: List of retrieval results.
            query: User query.

        Returns:
            Ranked list of results.
        """
        if not results:
            return []
        
        # Calculate scores for each result
        scored_results = []
        
        for result in results:
            content = result.get("content", "")
            metadata = result.get("metadata", {})
            distance = result.get("distance")
            
            content_score = self._calculate_content_relevance_score(content, query)
            metadata_score = self._calculate_metadata_relevance_score(metadata, query)
            
            final_score = self._calculate_final_score(distance, content_score, metadata_score)
            
            # Add scores to result
            scored_result = {
                **result,
                "content_score": content_score,
                "metadata_score": metadata_score,
                "final_score": final_score
            }
            
            scored_results.append(scored_result)
        
        # Sort by final score (descending)
        ranked_results = sorted(
            scored_results, 
            key=lambda x: x.get("final_score", 0),
            reverse=True
        )
        
        return ranked_results
    
    def filter_results(self, results: List[Dict]) -> List[Dict]:
        """
        Filter results to remove low-quality or redundant information.

        Args:
            results: List of retrieval results.

        Returns:
            Filtered list of results.
        """
        if not results:
            return []
        
        # Filter by score threshold
        threshold = 0.3  # Minimum acceptable score
        filtered_results = [
            result for result in results
            if result.get("final_score", 0) >= threshold
        ]
        
        # Remove redundant content (simple approach)
        unique_results = []
        content_hashes = set()
        
        for result in filtered_results:
            content = result.get("content", "")
            
            # Create a simple hash of the first 100 chars of content
            content_hash = hash(content[:100])
            
            if content_hash not in content_hashes:
                content_hashes.add(content_hash)
                unique_results.append(result)
        
        return unique_results


class ComparisonResultsProcessor:
    """
    Processor for CDP comparison results.
    """

    def __init__(self):
        """Initialize the comparison results processor."""
        self.ranker = ResultRanker()
    
    def process_comparison_results(
        self, 
        comparison_results: Dict[str, List[Dict]], 
        query: str, 
        feature: str = None
    ) -> Dict[str, List[Dict]]:
        """
        Process and rank comparison results.

        Args:
            comparison_results: Map of CDP to retrieval results.
            query: User query.
            feature: Feature for comparison.

        Returns:
            Processed comparison results.
        """
        # Use feature in the ranking if provided
        ranking_query = feature if feature else query
        
        processed_results = {}
        
        for cdp, results in comparison_results.items():
            # Rank results
            ranked_results = self.ranker.rank_results(results, ranking_query)
            
            # Filter results
            filtered_results = self.ranker.filter_results(ranked_results)
            
            processed_results[cdp] = filtered_results
        
        return processed_results
"""
Query processing for the CDP support agent chatbot.
"""

import logging
import re
from typing import Dict, List, Tuple, Optional, Any

from src.config import TOP_K_RESULTS
from src.retriever.retriever import DocumentRetriever, ComparisonRetriever
from src.retriever.ranker import ResultRanker, ComparisonResultsProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class QueryProcessor:
    """
    Processor for user queries.
    """

    def __init__(
        self, 
        document_retriever: DocumentRetriever,
        comparison_retriever: ComparisonRetriever
    ):
        """
        Initialize the query processor.

        Args:
            document_retriever: Document retriever instance.
            comparison_retriever: Comparison retriever instance.
        """
        self.document_retriever = document_retriever
        self.comparison_retriever = comparison_retriever
        self.result_ranker = ResultRanker()
        self.comparison_processor = ComparisonResultsProcessor()
    
    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess the user query.

        Args:
            query: User query.

        Returns:
            Preprocessed query.
        """
        # Convert to lowercase
        query = query.lower()
        
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query).strip()
        
        # Remove special characters except for essential ones
        query = re.sub(r'[^\w\s\?\.]', '', query)
        
        return query
    
    def process_query(self, query: str) -> Dict:
        """
        Process a user query and retrieve relevant information.

        Args:
            query: User query.

        Returns:
            Response data including retrieved information and query analysis.
        """
        # Preprocess query
        processed_query = self._preprocess_query(query)
        
        # Check if query is empty after preprocessing
        if not processed_query:
            return {
                "type": "error",
                "message": "Please provide a valid question.",
                "query": query,
                "analysis": {"is_relevant": False}
            }
        
        # Check for comparison query
        if any(pattern in processed_query for pattern in ["compare", "vs", "versus", "difference between"]):
            return self._process_comparison_query(processed_query)
        
        # Process as regular query
        return self._process_regular_query(processed_query)
    
    def _process_regular_query(self, query: str) -> Dict:
        """
        Process a regular (non-comparison) query.

        Args:
            query: Preprocessed user query.

        Returns:
            Response data.
        """
        # Retrieve documents
        results, query_analysis = self.document_retriever.retrieve(query)
        
        # Check if query is relevant to CDPs
        if not query_analysis.get("is_relevant", False):
            return {
                "type": "irrelevant",
                "message": "I'm sorry, but your question doesn't seem to be related to the CDP platforms I support. I can answer questions about Segment, mParticle, Lytics, and Zeotap.",
                "query": query,
                "analysis": query_analysis
            }
        
        # Check if any results were found
        if not results:
            return {
                "type": "no_results",
                "message": "I couldn't find information related to your question. Could you try rephrasing or asking a different question about one of the CDP platforms?",
                "query": query,
                "analysis": query_analysis
            }
        
        # Rank results
        ranked_results = self.result_ranker.rank_results(results, query)
        
        # Filter results
        filtered_results = self.result_ranker.filter_results(ranked_results)
        
        # Prepare response
        response = {
            "type": "answer",
            "query": query,
            "analysis": query_analysis,
            "results": filtered_results
        }
        
        return response
    
    def _process_comparison_query(self, query: str) -> Dict:
        """
        Process a comparison query.

        Args:
            query: Preprocessed user query.

        Returns:
            Response data.
        """
        # Retrieve documents for comparison
        comparison_results, query_analysis = self.comparison_retriever.retrieve_for_comparison(query)
        
        # Check if any results were found
        if not any(results for cdp, results in comparison_results.items()):
            return {
                "type": "no_results",
                "message": "I couldn't find enough information to compare the CDP platforms based on your question. Could you try asking a more specific comparison question?",
                "query": query,
                "analysis": query_analysis
            }
        
        # Process comparison results
        processed_results = self.comparison_processor.process_comparison_results(
            comparison_results,
            query,
            feature=query_analysis.get("feature")
        )
        
        # Prepare response
        response = {
            "type": "comparison",
            "query": query,
            "analysis": query_analysis,
            "results": processed_results
        }
        
        return response
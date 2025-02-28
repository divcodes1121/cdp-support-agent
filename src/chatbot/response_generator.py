"""
Response generation for the CDP support agent chatbot.
"""

import logging
import re
from typing import Dict, List, Optional, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ResponseGenerator:
    """
    Generator for chatbot responses.
    """

    def __init__(self):
        """Initialize the response generator."""
        pass
    
    def _extract_steps(self, content: str) -> List[str]:
        """
        Extract steps from content.

        Args:
            content: Document content.

        Returns:
            List of steps.
        """
        # Look for numbered steps
        numbered_steps = re.findall(r'\d+\.\s+(.*?)(?=\d+\.\s+|$)', content)
        if numbered_steps:
            return [step.strip() for step in numbered_steps]
        
        # Look for bullet points
        bullet_steps = re.findall(r'[\*\-]\s+(.*?)(?=[\*\-]\s+|$)', content)
        if bullet_steps:
            return [step.strip() for step in bullet_steps]
        
        # Split by sentences if no explicit steps
        sentences = re.split(r'(?<=[.!?])\s+', content)
        return [s.strip() for s in sentences if len(s.strip()) > 20]
    
    def _format_source_reference(self, metadata: Dict) -> str:
        """
        Format a source reference for a response.

        Args:
            metadata: Document metadata.

        Returns:
            Formatted source reference.
        """
        platform = metadata.get("platform", "").capitalize()
        title = metadata.get("title", "Documentation")
        url = metadata.get("url", "")
        
        if url:
            return f"Source: {platform} - [{title}]({url})"
        else:
            return f"Source: {platform} - {title}"
    
    def generate_regular_response(self, query_response: Dict) -> Dict:
        """
        Generate a response for a regular query.

        Args:
            query_response: Query response data.

        Returns:
            Formatted response.
        """
        # Handle error cases
        if query_response.get("type") == "error":
            return {
                "type": "text",
                "content": query_response.get("message", "I'm sorry, I couldn't process your question.")
            }
        
        # Handle irrelevant queries
        if query_response.get("type") == "irrelevant":
            return {
                "type": "text",
                "content": query_response.get("message", "I'm sorry, but your question doesn't seem to be related to the CDP platforms I support.")
            }
        
        # Handle no results
        if query_response.get("type") == "no_results":
            return {
                "type": "text",
                "content": query_response.get("message", "I couldn't find information related to your question.")
            }
        
        # Process regular answers
        results = query_response.get("results", [])
        analysis = query_response.get("analysis", {})
        
        if not results:
            return {
                "type": "text",
                "content": "I couldn't find specific information to answer your question. Could you try rephrasing or asking a different question?"
            }
        
        # Extract CDP name if available
        cdp = analysis.get("cdp")
        cdp_name = cdp.capitalize() if cdp else "the CDP"
        
        # Get the top result
        top_result = results[0]
        content = top_result.get("content", "")
        metadata = top_result.get("metadata", {})
        
        # Determine if this is a how-to question
        query_type = analysis.get("query_type", "general")
        
        if query_type == "how-to":
            # Extract steps
            steps = self._extract_steps(content)
            
            if steps and len(steps) >= 2:
                # Format as a step-by-step guide
                steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
                
                response_text = f"Here's how to do that in {cdp_name}:\n\n{steps_text}"
            else:
                # Fall back to regular text if steps couldn't be extracted
                response_text = f"Here's information on how to do that in {cdp_name}:\n\n{content}"
        else:
            # Format as a regular response
            response_text = f"Here's information about that from {cdp_name}:\n\n{content}"
        
        # Add source reference
        source_reference = self._format_source_reference(metadata)
        response_text = f"{response_text}\n\n{source_reference}"
        
        # Include additional information if available
        if len(results) > 1:
            additional_info = "I found some additional information that might be helpful:\n\n"
            
            for i, result in enumerate(results[1:3]):  # Just include up to 2 additional results
                result_content = result.get("content", "")
                result_metadata = result.get("metadata", {})
                
                # Truncate content if too long
                if len(result_content) > 200:
                    result_content = result_content[:200] + "..."
                
                additional_info += f"**Additional Information {i+1}**:\n{result_content}\n\n"
                additional_info += f"{self._format_source_reference(result_metadata)}\n\n"
            
            response_text = f"{response_text}\n\n{additional_info}"
        
        return {
            "type": "text",
            "content": response_text
        }
    
    def generate_comparison_response(self, query_response: Dict) -> Dict:
        """
        Generate a response for a comparison query.

        Args:
            query_response: Query response data.

        Returns:
            Formatted response.
        """
        # Handle error cases
        if query_response.get("type") == "no_results":
            return {
                "type": "text",
                "content": query_response.get("message", "I couldn't find enough information to compare the CDP platforms based on your question.")
            }
        
        # Process comparison results
        results = query_response.get("results", {})
        analysis = query_response.get("analysis", {})
        
        if not results or not any(cdp_results for cdp, cdp_results in results.items()):
            return {
                "type": "text",
                "content": "I couldn't find specific information to compare the CDP platforms based on your question. Could you try asking a more specific comparison question?"
            }
        
        # Extract feature being compared
        feature = analysis.get("feature", "this feature")
        cdps = analysis.get("cdps", [])
        
        # Build comparison response
        response_text = f"Here's a comparison of how different CDPs handle {feature}:\n\n"
        
        # Process each CDP's results
        for cdp, cdp_results in results.items():
            if not cdp_results:
                continue
                
            # Get the top result for the CDP
            top_result = cdp_results[0]
            content = top_result.get("content", "")
            metadata = top_result.get("metadata", {})
            
            # Truncate content if too long
            if len(content) > 300:
                content = content[:300] + "..."
            
            # Add CDP section
            response_text += f"**{cdp.capitalize()}**:\n{content}\n\n"
            response_text += f"{self._format_source_reference(metadata)}\n\n"
        
        # Add summary if possible
        response_text += "\n**Summary**:\n"
        response_text += f"Each CDP platform has its own approach to {feature}. "
        
        # Add specific comparisons if we have data for multiple CDPs
        if len([cdp for cdp, cdp_results in results.items() if cdp_results]) >= 2:
            response_text += "Consider your specific requirements when choosing between them."
        else:
            response_text += "I could only find detailed information for some of the platforms. Consider checking the official documentation for more details."
        
        return {
            "type": "text",
            "content": response_text
        }
    
    def generate_response(self, query_response: Dict) -> Dict:
        """
        Generate a response based on query processing results.

        Args:
            query_response: Query response data.

        Returns:
            Formatted response.
        """
        response_type = query_response.get("type", "")
        
        if response_type == "comparison":
            return self.generate_comparison_response(query_response)
        else:
            return self.generate_regular_response(query_response)   
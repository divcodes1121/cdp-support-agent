import re
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class ResponseGenerator:
    """Generates responses from query results."""
    
    def __init__(self):
        """Initialize the response generator."""
        pass
    
    def _extract_steps(self, content):
        """Extract steps from content."""
        # Look for numbered steps (e.g., "1. Do this")
        numbered_steps = re.findall(r'\d+\.\s*(.*?)(?=\d+\.\s*|$)', content)
        if numbered_steps and len(numbered_steps) >= 2:
            return [step.strip() for step in numbered_steps]
        
        # Look for bullet points
        bullet_steps = re.findall(r'[\*\-•]\s*(.*?)(?=[\*\-•]\s*|$)', content)
        if bullet_steps and len(bullet_steps) >= 2:
            return [step.strip() for step in bullet_steps]
        
        # Split by sentences for steps
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        # Filter out short sentences
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        return sentences
    
    def _format_source(self, metadata):
        """Format a source reference."""
        platform = metadata.get('platform', '').capitalize()
        title = metadata.get('title', 'Documentation')
        url = metadata.get('url', '')
        
        if url:
            return f"Source: {platform} - [{title}]({url})"
        else:
            return f"Source: {platform} documentation"
    
    def generate_response(self, query_response):
        """Generate a response from query results."""
        response_type = query_response.get('type', '')
        
        # Handle error cases
        if response_type == 'error':
            return {
                'type': 'text',
                'content': query_response.get('message', "I'm sorry, I couldn't process your question.")
            }
        
        # Handle irrelevant queries
        if response_type == 'irrelevant':
            return {
                'type': 'text',
                'content': query_response.get('message', "I'm sorry, but your question doesn't seem to be related to CDP platforms.")
            }
        
        # Handle no results
        if response_type == 'no_results':
            return {
                'type': 'text',
                'content': query_response.get('message', "I couldn't find specific information related to your question.")
            }
        
        # Handle comparison queries
        if response_type == 'comparison':
            return self._generate_comparison_response(query_response)
        
        # Handle regular queries
        return self._generate_regular_response(query_response)
    
    def _generate_regular_response(self, query_response):
        """Generate a response for a regular query."""
        results = query_response.get('results', [])
        
        if not results:
            return {
                'type': 'text',
                'content': "I couldn't find specific information to answer your question. Could you try rephrasing or asking a different question?"
            }
        
        # Get the top result
        top_result = results[0]
        document = top_result.get('document', {})
        metadata = top_result.get('metadata', {})
        
        content = document.get('content', '')
        platform = metadata.get('platform', '').capitalize()
        
        # Generate response based on query type
        if query_response.get('type') == 'how-to':
            # Extract steps for how-to
            steps = self._extract_steps(content)
            
            if steps and len(steps) >= 2:
                # Format as a step-by-step guide
                steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
                
                response_text = f"Here's how to do that in {platform}:\n\n{steps_text}"
            else:
                # Fall back to regular text
                response_text = f"Here's information on how to do that in {platform}:\n\n{content[:800]}..."
        else:
            # Format as a regular response
            response_text = f"Here's information about that from {platform}:\n\n{content[:800]}..."
        
        # Add source reference
        source_reference = self._format_source(metadata)
        response_text = f"{response_text}\n\n{source_reference}"
        
        # Include additional information if available
        if len(results) > 1:
            additional_info = "\n\nI found some additional information that might be helpful:\n\n"
            
            # Add second result as additional info
            second_result = results[1]
            second_doc = second_result.get('document', {})
            second_meta = second_result.get('metadata', {})
            
            second_content = second_doc.get('content', '')
            
            # Truncate if too long
            if len(second_content) > 300:
                second_content = second_content[:300] + "..."
            
            additional_info += f"**Additional Information**:\n{second_content}\n\n"
            additional_info += f"{self._format_source(second_meta)}"
            
            response_text += additional_info
        
        return {
            'type': 'text',
            'content': response_text
        }
    
    def _generate_comparison_response(self, query_response):
        """Generate a response for a comparison query."""
        platform_results = query_response.get('results', {})
        platforms = query_response.get('platforms', [])
        
        if not platform_results or not platforms:
            return {
                'type': 'text',
                'content': "I couldn't find enough information to compare the CDP platforms based on your question."
            }
        
        # Start with comparison intro
        response_text = f"Here's a comparison between {', '.join([p.capitalize() for p in platforms])}:\n\n"
        
        # Add information for each platform
        for platform in platforms:
            results = platform_results.get(platform, [])
            
            if not results:
                response_text += f"**{platform.capitalize()}**:\nI couldn't find specific information about this platform for your question.\n\n"
                continue
            
            # Get top result for the platform
            top_result = results[0]
            document = top_result.get('document', {})
            metadata = top_result.get('metadata', {})
            
            content = document.get('content', '')
            
            # Truncate content if too long
            if len(content) > 300:
                content = content[:300] + "..."
            
            # Add platform section
            response_text += f"**{platform.capitalize()}**:\n{content}\n\n"
            response_text += f"{self._format_source(metadata)}\n\n"
        
        # Add summary
        response_text += "\n**Summary**:\n"
        response_text += f"When comparing these platforms, consider your specific requirements and use cases. Each CDP has different strengths in terms of integrations, data handling, and analytics capabilities."
        
        return {
            'type': 'text',
            'content': response_text
        }

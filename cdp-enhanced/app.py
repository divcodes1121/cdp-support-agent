import os
import logging
from pathlib import Path
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from query_processor import QueryProcessor
from response_generator import ResponseGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Check if index exists, if not warn
index_dir = Path("data/index")
if not index_dir.exists():
    logger.warning("Index directory not found. Please run indexer.py first.")

# Initialize components
query_processor = QueryProcessor()
response_generator = ResponseGenerator()

# Create Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

@app.route("/")
def index():
    """Render the main chat interface."""
    return render_template("index.html")

@app.route("/api/health")
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

@app.route("/api/chat", methods=["POST"])
def chat():
    """Process a chat message and return a response."""
    try:
        data = request.json
        
        if not data or "message" not in data:
            return jsonify({
                "error": "Invalid request. 'message' field is required."
            }), 400
        
        user_message = data["message"]
        conversation_id = data.get("conversation_id")
        
        # Log incoming message
        logger.info(f"Received message: {user_message}")
        
        try:
            # Process query
            query_response = query_processor.process_query(user_message)
            
            # Generate response
            response = response_generator.generate_response(query_response)
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            # Fallback response
            response = {
                "type": "text",
                "content": "I'm having trouble processing that query. Here's what I know about the CDPs:\n\n"
                           "- Segment: A customer data platform for collecting and routing data\n"
                           "- mParticle: A CDP with strong mobile and cross-device capabilities\n"
                           "- Lytics: A CDP focused on behavioral analysis and content personalization\n"
                           "- Zeotap: A CDP specializing in identity resolution and data enrichment"
            }
        
        # Prepare API response
        api_response = {
            "response": response,
            "conversation_id": conversation_id,
            "message_id": hash(f"{conversation_id}_{user_message}")
        }
        
        return jsonify(api_response)
    
    except Exception as e:
        logger.error(f"Error in request handling: {e}")
        return jsonify({
            "response": {
                "type": "text",
                "content": "Sorry, I encountered an error while processing your request."
            }
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

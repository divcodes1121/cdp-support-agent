"""
API routes for the CDP Support Agent Chatbot.
"""

import logging
import json
from typing import Dict, List, Optional

from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(query_processor, response_generator):
    """
    Create Flask application with routes.
    
    Args:
        query_processor: Query processor instance.
        response_generator: Response generator instance.
    
    Returns:
        Flask application instance.
    """
    app = Flask(__name__, template_folder="../../web/templates", static_folder="../../web/static")
    CORS(app)
    
    # Store components as app attributes
    app.query_processor = query_processor
    app.response_generator = response_generator
    
    # Define routes
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
        """
        Process a chat message and return a response.
        
        Request body:
        {
            "message": "User message",
            "conversation_id": "Conversation ID (optional)"
        }
        
        Returns:
            JSON response with chatbot reply.
        """
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
            
            # Process query
            query_response = app.query_processor.process_query(user_message)
            
            # Generate response
            response = app.response_generator.generate_response(query_response)
            
            # Prepare API response
            api_response = {
                "response": response,
                "conversation_id": conversation_id,
                "message_id": hash(f"{conversation_id}_{user_message}")
            }
            
            return jsonify(api_response)
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return jsonify({
                "error": "An error occurred while processing your message."
            }), 500
    
    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 errors."""
        return jsonify({"error": "Resource not found."}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        """Handle 500 errors."""
        return jsonify({"error": "Internal server error."}), 500
    
    return app
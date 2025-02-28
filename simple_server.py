from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging
import random
import re

app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CDP knowledge base with predefined responses
CDP_INFO = {
    "segment": {
        "general": "Segment is a Customer Data Platform (CDP) that helps businesses collect, clean, and control customer data. It simplifies the process of tracking user data across multiple platforms and centralizes it for analysis and marketing use.",
        "features": "Key features of Segment include: 1) Data collection across web, mobile, server, and cloud apps, 2) Identity resolution to create unified customer profiles, 3) Audience management for targeted marketing, 4) Real-time data processing, and 5) Integration with over 300 tools and platforms.",
        "sources": "To set up a new source in Segment: 1) Log in to your Segment workspace, 2) Navigate to Sources and click 'Add Source', 3) Select the source type you want to add, 4) Configure the source settings and authentication, 5) Implement the tracking code if required, and 6) Verify data is flowing correctly using the Debugger."
    },
    "mparticle": {
        "general": "mParticle is a Customer Data Platform that helps companies collect and connect their data across devices, channels, and partners. It enables businesses to build a unified view of the customer journey.",
        "features": "Key features of mParticle include: 1) Cross-platform data collection, 2) Identity management for customer recognition across touchpoints, 3) Audience segmentation tools, 4) Data filtering and validation, and 5) Real-time forwarding to over 300 integrations.",
        "profiles": "To create a user profile in mParticle: 1) Implement the mParticle SDK in your application, 2) Set user identities using identifyUser() or similar methods, 3) Add user attributes using setUserAttribute(), 4) Track user events with logEvent(), and 5) Configure identity resolution settings in the mParticle dashboard."
    },
    "lytics": {
        "general": "Lytics is a Customer Data Platform that uses machine learning to build unified customer profiles and predict customer behaviors. It helps companies deliver personalized marketing experiences across various channels.",
        "features": "Key features of Lytics include: 1) Behavioral scoring and predictive analytics, 2) Content affinity modeling, 3) Real-time personalization capabilities, 4) Machine learning for customer insights, and 5) Integration with major marketing platforms.",
        "segments": "To build an audience segment in Lytics: 1) Log in to your Lytics account, 2) Navigate to 'Audiences' and click 'Create Audience', 3) Define your segment criteria using Lytics' behavioral attributes, 4) Use the visual interface to combine multiple conditions with AND/OR logic, 5) Preview your audience size and composition, and 6) Save and activate the segment for use in marketing campaigns."
    },
    "zeotap": {
        "general": "Zeotap is a Customer Intelligence Platform that helps brands better understand their customers and predict behaviors. It provides identity resolution, audience segmentation, and insights for marketers.",
        "features": "Key features of Zeotap include: 1) Unified ID solution for identity resolution, 2) Deterministic data matching, 3) AI-powered customer analytics, 4) Consent management for privacy compliance, and 5) Integration with major advertising and marketing platforms.",
        "integration": "To integrate your data with Zeotap: 1) Set up a Zeotap account and access the dashboard, 2) Configure data source connections in the 'Integrations' section, 3) Map your customer data fields to Zeotap's schema, 4) Establish secure data transfer using SFTP, S3, or API connections, 5) Set up regular data syncing schedules, and 6) Validate data flow using Zeotap's data quality reports."
    }
}

# Comparison information
COMPARISONS = {
    "segment_mparticle": "Segment vs mParticle: Both are leading CDPs, but Segment tends to excel in developer-friendly workflows and has broader integration options, while mParticle offers stronger mobile capabilities and more advanced identity resolution. Segment's pricing is typically more accessible for smaller companies, while mParticle is often chosen by larger enterprises with complex mobile needs.",
    "segment_lytics": "Segment vs Lytics: Segment focuses primarily on data collection and routing with strong technical integrations, while Lytics emphasizes behavioral analysis and predictive modeling. Segment is better for companies that need to organize their data stack, while Lytics excels at turning customer data into actionable insights and personalization.",
    "segment_zeotap": "Segment vs Zeotap: Segment is primarily a data integration platform focused on first-party data collection, while Zeotap offers additional third-party data enrichment and has stronger identity resolution capabilities. Segment has broader integration options, while Zeotap provides more built-in customer intelligence features.",
    "mparticle_lytics": "mParticle vs Lytics: mParticle excels in mobile data collection and offers more granular data controls, while Lytics provides stronger predictive analytics and content affinity modeling. mParticle is typically chosen by mobile-first companies, while Lytics appeals to content-heavy businesses looking for deep behavioral insights.",
    "mparticle_zeotap": "mParticle vs Zeotap: mParticle is focused on first-party data orchestration with strong mobile capabilities, while Zeotap offers more comprehensive identity resolution and data enrichment features. mParticle has more technical flexibility, while Zeotap provides additional customer intelligence tools.",
    "lytics_zeotap": "Lytics vs Zeotap: Lytics specializes in behavioral analysis and predictive modeling for personalization, while Zeotap focuses on identity resolution and data enrichment across channels. Lytics is better for content personalization use cases, while Zeotap has stronger advertising and audience activation capabilities."
}

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
    """Process chat messages and return responses."""
    try:
        data = request.json
        
        if not data or "message" not in data:
            return jsonify({
                "error": "Invalid request. 'message' field is required."
            }), 400
        
        user_message = data["message"].lower()
        conversation_id = data.get("conversation_id")
        
        # Log incoming message
        logger.info(f"Received message: {user_message}")
        
        # Process the query and generate response
        response_text = generate_response(user_message)
        
        # Prepare API response
        api_response = {
            "response": {
                "type": "text",
                "content": response_text
            },
            "conversation_id": conversation_id,
            "message_id": hash(f"{conversation_id}_{user_message}")
        }
        
        return jsonify(api_response)
    
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return jsonify({
            "error": "An error occurred while processing your message."
        }), 500

def generate_response(query):
    """Generate a response based on the user query."""
    query = query.lower()
    
    # Check if it's a comparison question
    if any(word in query for word in ["compare", "vs", "versus", "difference", "differences"]):
        return handle_comparison_query(query)
    
    # Check for platform-specific questions
    for platform in CDP_INFO:
        if platform in query:
            return handle_platform_query(platform, query)
    
    # Default responses if no specific match
    if any(word in query for word in ["hello", "hi", "hey", "greetings"]):
        return "Hello! I'm the CDP Support Agent. How can I help you with Segment, mParticle, Lytics, or Zeotap today?"
    
    if "help" in query or "what can you do" in query:
        return "I can answer questions about Customer Data Platforms (CDPs) including Segment, mParticle, Lytics, and Zeotap. Try asking about specific features, how to perform tasks, or comparisons between platforms."
    
    # Generic response for CDP-related questions
    if any(word in query for word in ["cdp", "customer data", "platform"]):
        return "Customer Data Platforms (CDPs) help businesses collect, organize, and activate customer data across different channels. The main CDPs I can provide information about are Segment, mParticle, Lytics, and Zeotap. What specific aspect would you like to know more about?"
    
    # Fallback response
    return "I'm not sure I understand your question. Could you try asking about one of the CDP platforms like Segment, mParticle, Lytics, or Zeotap? For example, you could ask 'How do I set up a source in Segment?' or 'Compare mParticle and Lytics'."

def handle_platform_query(platform, query):
    """Handle a query about a specific platform."""
    platform_info = CDP_INFO.get(platform, {})
    
    # Check for how-to questions
    if any(phrase in query for phrase in ["how to", "how do i", "steps to", "guide for"]):
        if platform == "segment" and any(word in query for word in ["source", "set up", "setup", "configure"]):
            return platform_info.get("sources", platform_info.get("general"))
        
        if platform == "mparticle" and any(word in query for word in ["profile", "user", "identity"]):
            return platform_info.get("profiles", platform_info.get("general"))
        
        if platform == "lytics" and any(word in query for word in ["segment", "audience", "build"]):
            return platform_info.get("segments", platform_info.get("general"))
        
        if platform == "zeotap" and any(word in query for word in ["integrate", "integration", "connect"]):
            return platform_info.get("integration", platform_info.get("general"))
    
    # Check for feature questions
    if any(word in query for word in ["feature", "capabilities", "what can", "what does"]):
        return platform_info.get("features", platform_info.get("general"))
    
    # Default to general info about the platform
    return platform_info.get("general", f"I have information about {platform.capitalize()}, but I'm not sure what specific aspect you're asking about. You can ask about features, how-to guides, or comparisons with other platforms.")

def handle_comparison_query(query):
    """Handle a comparison query between platforms."""
    platforms = []
    
    for platform in CDP_INFO:
        if platform in query:
            platforms.append(platform)
    
    # If exactly two platforms are mentioned, provide specific comparison
    if len(platforms) == 2:
        platforms.sort()  # Sort to match the comparison key format
        comparison_key = f"{platforms[0]}_{platforms[1]}"
        return COMPARISONS.get(comparison_key, f"When comparing {platforms[0].capitalize()} and {platforms[1].capitalize()}, they have different strengths. Would you like to know about a specific aspect of these platforms?")
    
    # If only one platform is mentioned, suggest comparisons
    elif len(platforms) == 1:
        other_platforms = [p for p in CDP_INFO if p != platforms[0]]
        other_platform = random.choice(other_platforms)
        return f"I can compare {platforms[0].capitalize()} with other CDPs like {other_platform.capitalize()}. What specific aspect would you like me to compare?"
    
    # General comparison if no specific platforms mentioned
    else:
        return "Each CDP has different strengths: Segment excels in developer-friendly workflows and integration breadth; mParticle offers strong mobile capabilities and cross-device identity; Lytics focuses on behavioral analysis and content personalization; and Zeotap specializes in identity resolution and data enrichment. Which platforms would you like me to compare in more detail?"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging
import re
import random

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CDP knowledge base
CDP_INFO = {
    "segment": "Segment is a Customer Data Platform that helps businesses collect, clean, and control customer data. It provides easy integrations and can route data to various destinations.",
    "mparticle": "mParticle is a Customer Data Platform focused on mobile and cross-device identity. It helps companies collect and connect their data across devices, channels, and partners.",
    "lytics": "Lytics is a Customer Data Platform that uses machine learning for behavioral analysis and content personalization. It helps predict customer behaviors and deliver personalized experiences.",
    "zeotap": "Zeotap is a Customer Intelligence Platform that specializes in identity resolution and data enrichment. It helps brands better understand their customers across different touchpoints."
}

# How-to knowledge base
CDP_HOWTO = {
    "segment": {
        "source": "To set up a new source in Segment:\n\n1. Log in to your Segment workspace\n2. Navigate to Sources and click 'Add Source'\n3. Select the source type you want to add\n4. Configure the source settings and authentication\n5. Implement the tracking code if required\n6. Verify data is flowing correctly using the Debugger",
        "destination": "To connect a destination in Segment:\n\n1. Go to the Destinations section in your Segment workspace\n2. Click 'Add Destination'\n3. Search for and select the destination you want to connect\n4. Configure the destination settings including API keys\n5. Map your events and properties to the destination format\n6. Enable the destination and test the data flow",
        "tracking": "To implement tracking with Segment:\n\n1. Install the Segment SDK for your platform\n2. Initialize the SDK with your write key\n3. Track events using the analytics.track() method\n4. Identify users with analytics.identify()\n5. Use page/screen tracking for web or mobile views\n6. Add custom properties to enrich your events"
    },
    "mparticle": {
        "profile": "To create a user profile in mParticle:\n\n1. Implement the mParticle SDK in your application\n2. Use the identify API to set user identities\n3. Set user attributes to enrich the profile\n4. Track user events to build behavior history\n5. Configure identity resolution settings in the dashboard\n6. View and manage user profiles in the mParticle UI",
        "integration": "To set up an integration in mParticle:\n\n1. Navigate to Setup > Outputs in the mParticle dashboard\n2. Select the desired output platform\n3. Configure the connection settings and API credentials\n4. Set up data filtering and forwarding rules\n5. Configure event and user attribute mappings\n6. Activate the connection and verify data flow",
        "audience": "To create an audience in mParticle:\n\n1. Go to the Audiences section in the dashboard\n2. Click 'New Audience'\n3. Define your audience criteria using user attributes and events\n4. Configure the audience calculation frequency\n5. Select the output platforms to receive this audience\n6. Activate the audience and monitor its size"
    },
    "lytics": {
        "segment": "To build an audience segment in Lytics:\n\n1. Navigate to Audiences in the Lytics interface\n2. Click 'Create Audience'\n3. Use the visual builder to define your segment criteria\n4. Add behavioral conditions based on user actions\n5. Combine multiple conditions with AND/OR logic\n6. Preview your audience size and composition\n7. Save and activate the segment for use in campaigns",
        "campaign": "To create a campaign in Lytics:\n\n1. Go to the Campaigns section in Lytics\n2. Click 'Create Campaign'\n3. Select your target audience segment\n4. Choose the campaign channel and type\n5. Configure personalization settings and content\n6. Set the campaign schedule and frequency\n7. Activate the campaign and monitor its performance",
        "integration": "To integrate a data source with Lytics:\n\n1. Navigate to the Data section in Lytics\n2. Select 'Add Data Source'\n3. Choose the type of data source you want to connect\n4. Configure authentication and connection settings\n5. Map the incoming data fields to Lytics schema\n6. Set up data synchronization schedule\n7. Test and activate the data source"
    },
    "zeotap": {
        "integration": "To integrate your data with Zeotap:\n\n1. Set up a Zeotap account and access the dashboard\n2. Navigate to the Integrations section\n3. Select the data source type you want to connect\n4. Configure the connection settings and authentication\n5. Map your data fields to Zeotap's schema\n6. Set up a secure data transfer method (SFTP, S3, or API)\n7. Schedule regular data syncs and monitor data quality",
        "audience": "To create an audience in Zeotap:\n\n1. Go to the Audience Builder in the Zeotap platform\n2. Click 'Create New Audience'\n3. Define your audience using demographic and behavioral attributes\n4. Add rules for inclusion and exclusion criteria\n5. Preview the audience size and composition\n6. Save the audience definition\n7. Activate the audience for marketing campaigns",
        "identity": "To set up identity resolution in Zeotap:\n\n1. Navigate to the Identity section in Zeotap\n2. Configure your identity sources and types\n3. Set up matching rules and confidence thresholds\n4. Choose deterministic and/or probabilistic matching\n5. Configure privacy and consent settings\n6. Test the identity resolution with sample data\n7. Activate and monitor the identity graph"
    }
}

# Comparison knowledge base
CDP_COMPARISONS = {
    "segment_mparticle": "**Segment vs mParticle**\n\nSegment is known for its extensive integration library and developer-friendly approach. It excels at data collection and routing to hundreds of destinations.\n\nmParticle has stronger mobile capabilities and more advanced identity resolution features. It offers more granular data controls and filtering options.\n\nSegment's pricing is typically more accessible for smaller companies, while mParticle is often chosen by larger enterprises with complex mobile needs.",
    "segment_lytics": "**Segment vs Lytics**\n\nSegment focuses primarily on data collection and routing with strong technical integrations, serving as a central hub for your customer data infrastructure.\n\nLytics emphasizes behavioral analysis and predictive modeling, with built-in machine learning capabilities to drive personalization and customer insights.\n\nSegment is better for companies that need to organize their data stack, while Lytics excels at turning customer data into actionable insights for marketing initiatives.",
    "segment_zeotap": "**Segment vs Zeotap**\n\nSegment is primarily a data integration platform focused on first-party data collection and distribution to marketing and analytics tools.\n\nZeotap offers additional third-party data enrichment and has stronger identity resolution capabilities, specializing in creating comprehensive customer profiles across devices.\n\nSegment has broader integration options, while Zeotap provides more built-in customer intelligence features and compliance tools.",
    "mparticle_lytics": "**mParticle vs Lytics**\n\nmParticle excels in mobile data collection and offers more granular data controls, making it ideal for companies with complex mobile applications.\n\nLytics provides stronger predictive analytics and content affinity modeling, focusing on deriving insights from behavioral data to power personalization.\n\nmParticle is typically chosen by mobile-first companies, while Lytics appeals to content-heavy businesses looking for deep behavioral insights.",
    "mparticle_zeotap": "**mParticle vs Zeotap**\n\nmParticle is focused on first-party data orchestration with strong mobile capabilities and real-time data processing features.\n\nZeotap offers more comprehensive identity resolution and data enrichment features, with particular strength in compliance and consent management.\n\nmParticle has more technical flexibility and integration options, while Zeotap provides additional customer intelligence tools and third-party data access.",
    "lytics_zeotap": "**Lytics vs Zeotap**\n\nLytics specializes in behavioral analysis and predictive modeling for personalization, with strong content affinity capabilities.\n\nZeotap focuses on identity resolution and data enrichment across channels, with particular strengths in audience targeting for advertising.\n\nLytics is better for content personalization use cases, while Zeotap has stronger advertising and audience activation capabilities."
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/health")
def health_check():
    return jsonify({"status": "ok"})

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        message = data.get("message", "")
        logger.info(f"Received message: {message}")
        
        # Simple keyword matching for responses
        message_lower = message.lower()
        
        # Check for platform mentions
        platforms = []
        for platform in CDP_INFO:
            if platform in message_lower:
                platforms.append(platform)
        
        # Check for how-to keywords
        how_to_keywords = {
            "segment": ["source", "track", "destination", "integration"],
            "mparticle": ["profile", "user", "integration", "audience"],
            "lytics": ["segment", "audience", "campaign", "integration"],
            "zeotap": ["integration", "audience", "identity"]
        }
        
        # Handle comparison questions
        if "compare" in message_lower or "vs" in message_lower or "versus" in message_lower or "difference" in message_lower:
            if len(platforms) >= 2:
                platforms.sort()  # Sort to match the comparison key format
                comparison_key = f"{platforms[0]}_{platforms[1]}"
                response = CDP_COMPARISONS.get(comparison_key, f"When comparing {platforms[0].capitalize()} and {platforms[1].capitalize()}: \n\n**{platforms[0].capitalize()}**: {CDP_INFO[platforms[0]]}\n\n**{platforms[1].capitalize()}**: {CDP_INFO[platforms[1]]}")
            elif len(platforms) == 1:
                other_platform = random.choice([p for p in CDP_INFO if p != platforms[0]])
                comparison_key = f"{min(platforms[0], other_platform)}_{max(platforms[0], other_platform)}"
                response = CDP_COMPARISONS.get(comparison_key, f"When comparing {platforms[0].capitalize()} and {other_platform.capitalize()}: \n\n**{platforms[0].capitalize()}**: {CDP_INFO[platforms[0]]}\n\n**{other_platform.capitalize()}**: {CDP_INFO[other_platform]}")
            else:
                response = "Each CDP has different strengths: Segment excels in integration breadth, mParticle in mobile capabilities, Lytics in content personalization, and Zeotap in identity resolution. Which platforms would you like me to compare in more detail?"
        
        # Handle how-to questions
        elif any(word in message_lower for word in ["how", "steps", "guide", "tutorial", "steps to"]):
            if platforms:
                platform = platforms[0]
                found_how_to = False
                
                # Check for specific how-to topics
                for keyword, topic_keywords in how_to_keywords.items():
                    if platform == keyword:
                        for topic in topic_keywords:
                            if topic in message_lower:
                                response = CDP_HOWTO[platform].get(topic, CDP_INFO[platform])
                                found_how_to = True
                                break
                
                # If no specific how-to found, provide a general one
                if not found_how_to:
                    # Get first available how-to for that platform
                    first_topic = list(CDP_HOWTO[platform].keys())[0]
                    response = CDP_HOWTO[platform][first_topic]
            else:
                response = "To perform this action in a CDP, you typically need to:\n\n1. Log in to the platform\n2. Navigate to the relevant section\n3. Configure the settings according to your needs\n4. Save your changes and test the implementation\n\nFor platform-specific instructions, try asking about a specific CDP like Segment, mParticle, Lytics, or Zeotap."
        
        # Platform-specific questions
        elif platforms:
            platform = platforms[0]
            response = CDP_INFO[platform]
        
        # Default response
        else:
            response = "I can help you with questions about Customer Data Platforms (CDPs) including Segment, mParticle, Lytics, and Zeotap. Try asking about specific features, how to perform tasks, or comparisons between platforms."
        
        return jsonify({
            "response": {
                "type": "text",
                "content": response
            },
            "conversation_id": data.get("conversation_id"),
            "message_id": hash(f"{data.get('conversation_id')}_{message}")
        })
    
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return jsonify({
            "response": {
                "type": "text",
                "content": "Sorry, I encountered an error while processing your request."
            }
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

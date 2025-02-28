CDP Support Agent Chatbot
========================

A specialized chatbot that can answer "how-to" questions related to four Customer Data Platforms (CDPs): Segment, mParticle, Lytics, and Zeotap. The chatbot extracts relevant information from the official documentation to guide users on how to perform tasks within each platform.

Table of Contents
----------------

- Features
- Technologies Used
- Installation
- Usage
- Project Structure
- Implementation Details
- Example Queries
- Limitations and Future Improvements
- License

Features
--------

Core Features:

* How-to Question Answering: Provides step-by-step instructions for performing tasks in each CDP.
* Documentation Extraction: Retrieves relevant information from CDP documentation to answer user questions.
* Platform-Specific Knowledge: Contains specialized information about Segment, mParticle, Lytics, and Zeotap.
* Query Variation Handling: Understands different ways of asking the same question and handles lengthy questions gracefully.
* Irrelevant Query Detection: Identifies and properly responds to questions unrelated to CDPs.

Advanced Features:

* Cross-CDP Comparisons: Compares approaches or functionalities between different CDPs (e.g., "How does Segment's audience creation process compare to Lytics'?").
* Advanced How-to Guidance: Provides detailed instructions for complex platform-specific questions and configurations.
* Natural Language Understanding: Processes natural language questions to extract intent and relevant entities.
* Web-Based Interface: Offers an intuitive chat interface with markdown formatting support.

Technologies Used
----------------

Backend:
- Python 3.9+
- Flask (Web framework)
- NLTK and scikit-learn (Text processing)
- BeautifulSoup4 (Web scraping)
- TF-IDF Vectorization (Document retrieval)

Frontend:
- HTML/CSS/JavaScript
- Markdown rendering for formatted responses
- Responsive design for various device sizes

Installation
-----------

Prerequisites:
- Python 3.9 or higher
- pip (Python package manager)
- Git (optional, for cloning the repository)

Setup:

1. Clone the repository or download the source code:
   git clone https://github.com/yourusername/cdp-support-agent.git
   cd cdp-support-agent/cdp-enhanced

2. Create and activate a virtual environment (optional but recommended):
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate

3. Install the required dependencies:
   pip install -r requirements.txt

4. Download the required NLTK data:
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

Usage
-----

Running the Chatbot:

1. Start the server:
   # For the simplified version (recommended)
   python simple_app.py
   
   # For the full implementation
   python app.py

2. Open a web browser and go to:
   http://localhost:5000

3. Start asking questions about the CDP platforms!

Scraping Fresh Documentation (Optional):

If you want to refresh the documentation data:
python scraper.py
python indexer.py

Project Structure
----------------

cdp-enhanced/
├── app.py                      # Main application (full implementation)
├── simple_app.py               # Simplified application with hardcoded knowledge
├── scraper.py                  # Documentation scraper
├── indexer.py                  # Document indexing and TF-IDF creation
├── query_processor.py          # Query understanding and retrieval
├── response_generator.py       # Response formatting and generation
├── requirements.txt            # Project dependencies
├── data/                       # Data directory
│   ├── raw/                    # Raw scraped documentation
│   └── index/                  # Processed indices
├── static/                     # Static assets
│   ├── css/
│   │   └── styles.css          # CSS styles
│   └── js/
│       └── main.js             # JavaScript code
└── templates/                  # HTML templates
    └── index.html              # Main chat interface

Implementation Details
---------------------

Document Retrieval System:

The chatbot uses two alternative approaches:

1. TF-IDF Based Retrieval (app.py):
   - Scrapes documentation from CDP websites
   - Processes text and creates TF-IDF representations
   - Finds relevant documents using cosine similarity
   - Extracts and ranks relevant information

2. Structured Knowledge Base (simple_app.py):
   - Pre-processes documentation into structured knowledge bases
   - Uses keyword matching for query understanding
   - Retrieves information from organized data structures
   - Ensures consistent and reliable responses

Query Processing:

The system processes queries through several steps:
1. Query Classification: Determines if the query is a how-to question, comparison, or general inquiry
2. Platform Extraction: Identifies which CDP platforms are mentioned
3. Relevance Check: Determines if the query is relevant to CDPs
4. Retrieval: Fetches relevant information based on query type
5. Response Generation: Formats the retrieved information into a user-friendly response

Example Queries
--------------

The chatbot can handle various types of questions, such as:

How-to Questions:
- "How do I set up a new source in Segment?"
- "How can I create a user profile in mParticle?"
- "How do I build an audience segment in Lytics?"
- "How can I integrate my data with Zeotap?"

Comparison Questions:
- "How does Segment's audience creation process compare to Lytics'?"
- "What's the difference between mParticle and Zeotap?"
- "Compare Segment and mParticle for mobile applications."
- "Which is better for identity resolution, Zeotap or mParticle?"

General Information Questions:
- "What is Segment used for?"
- "Tell me about Lytics features."
- "What kind of integrations does mParticle support?"
- "How does Zeotap handle data privacy?"

Limitations and Future Improvements
----------------------------------

Current Limitations:
- Limited to information available in the scraped documentation
- Comparison knowledge focuses on high-level differences
- No context memory between conversation turns

Potential Improvements:
- Implement a more advanced NLP model for better query understanding
- Add conversation memory to handle follow-up questions
- Expand the knowledge base with more detailed platform information
- Implement a feedback mechanism to improve responses over time
- Add authentication for secure access

License
-------

This project is licensed under the MIT License - see the LICENSE file for details.

This project was developed as part of an assignment to demonstrate software engineering skills in building a specialized chatbot for CDP platforms.
/**
 * CDP Support Agent Chatbot
 * Main JavaScript file for the chat interface
 */

// DOM elements
const messageContainer = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
let conversationId = generateConversationId();

// Event listeners
userInput.addEventListener('keydown', handleKeyPress);
sendButton.addEventListener('click', sendMessage);
userInput.addEventListener('input', autoResizeTextarea);

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    scrollToBottom();
    userInput.focus();
});

/**
 * Handle keypress events in the input field
 * @param {KeyboardEvent} event - The keypress event
 */
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

/**
 * Auto-resize the textarea based on content
 */
function autoResizeTextarea() {
    userInput.style.height = 'auto';
    userInput.style.height = (userInput.scrollHeight) + 'px';
}

/**
 * Send the user message to the API
 */
function sendMessage() {
    const message = userInput.value.trim();
    
    if (!message) {
        return;
    }
    
    // Add user message to the chat
    addUserMessage(message);
    
    // Clear input and reset height
    userInput.value = '';
    userInput.style.height = 'auto';
    
    // Show typing indicator
    addTypingIndicator();
    
    // Send message to API
    sendMessageToAPI(message);
}

/**
 * Add a user message to the chat
 * @param {string} message - The user message
 */
function addUserMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message user-message';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const messageText = document.createElement('p');
    messageText.textContent = message;
    
    messageContent.appendChild(messageText);
    messageElement.appendChild(messageContent);
    
    messageContainer.appendChild(messageElement);
    scrollToBottom();
}

/**
 * Add a bot message to the chat
 * @param {string} message - The bot message
 */
function addBotMessage(message) {
    // Remove typing indicator
    removeTypingIndicator();
    
    const messageElement = document.createElement('div');
    messageElement.className = 'message bot-message';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Convert markdown to HTML
    messageContent.innerHTML = parseMarkdown(message);
    
    messageElement.appendChild(messageContent);
    messageContainer.appendChild(messageElement);
    scrollToBottom();
}

/**
 * Add typing indicator to the chat
 */
function addTypingIndicator() {
    const typingElement = document.createElement('div');
    typingElement.className = 'message bot-message typing-indicator-container';
    typingElement.id = 'typing-indicator';
    
    const typingContent = document.createElement('div');
    typingContent.className = 'typing-indicator';
    
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('span');
        typingContent.appendChild(dot);
    }
    
    typingElement.appendChild(typingContent);
    messageContainer.appendChild(typingElement);
    scrollToBottom();
}

/**
 * Remove typing indicator from the chat
 */
function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

/**
 * Send a message to the API
 * @param {string} message - The user message
 */
function sendMessageToAPI(message) {
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message,
            conversation_id: conversationId
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('API request failed');
        }
        return response.json();
    })
    .then(data => {
        // Process the response
        const responseContent = data.response.content;
        addBotMessage(responseContent);
    })
    .catch(error => {
        console.error('Error:', error);
        removeTypingIndicator();
        addBotMessage('Sorry, there was an error processing your request. Please try again.');
    });
}

/**
 * Scroll to the bottom of the message container
 */
function scrollToBottom() {
    messageContainer.scrollTop = messageContainer.scrollHeight;
}

/**
 * Generate a random conversation ID
 * @returns {string} - Random conversation ID
 */
function generateConversationId() {
    return 'conv_' + Math.random().toString(36).substring(2, 15);
}

/**
 * Parse markdown text to HTML
 * @param {string} text - The markdown text
 * @returns {string} - HTML formatted text
 */
function parseMarkdown(text) {
    // Basic markdown parsing
    let html = text;
    
    // Convert links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // Convert headers
    html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');
    
    // Convert bold and italic
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Convert code blocks
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // Convert inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Convert lists
    html = html.replace(/^\d+\. (.*$)/gm, '<li>$1</li>');
    html = html.replace(/^- (.*$)/gm, '<li>$1</li>');
    
    // Wrap lists in ul or ol tags
    html = html.replace(/<li>.*?<\/li>/g, function(match) {
        if (match.startsWith('<li>1. ')) {
            return '<ol>' + match + '</ol>';
        } else {
            return '<ul>' + match + '</ul>';
        }
    });
    
    // Convert paragraphs
    html = html.replace(/\n\n/g, '<br><br>');
    
    // Convert blockquotes
    html = html.replace(/^> (.*$)/gm, '<blockquote>$1</blockquote>');
    
    return html;
}
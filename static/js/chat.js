/**
 * Spark AI Chat Functionality
 * Handles all chat interactions and UI updates
 */

let isTyping = false;

// Auto-scroll to bottom of chat
function scrollToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Add message to chat
function addMessage(content, role, timestamp = null) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex justify-' + (role === 'user' ? 'end' : 'start');
    
    const messageContent = document.createElement('div');
    messageContent.className = role === 'user' 
        ? 'max-w-xs lg:max-w-md bg-blue-600 text-white rounded-2xl rounded-br-md px-4 py-3 shadow-sm'
        : 'max-w-sm lg:max-w-2xl bg-gray-100 text-gray-800 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm';
    
    if (role === 'user') {
        messageContent.innerHTML = `
            <p class="text-sm">${escapeHtml(content)}</p>
            <p class="text-xs text-blue-200 mt-1">${timestamp || new Date().toISOString().slice(0, 16)}</p>
        `;
    } else {
        messageContent.innerHTML = `
            <div class="prose prose-sm max-w-none">${content}</div>
            <p class="text-xs text-gray-500 mt-1">${timestamp || new Date().toISOString().slice(0, 16)}</p>
        `;
    }
    
    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Send message
async function sendMessage(message) {
    if (!message.trim() || isTyping) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.value = '';
    }
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        const response = await fetch('/chat/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Add AI response to chat
            addMessage(data.response, 'assistant');
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
        }
    } catch (error) {
        console.error('Error:', error);
        addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
    } finally {
        hideTypingIndicator();
    }
}

// Show typing indicator
function showTypingIndicator() {
    isTyping = true;
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.classList.remove('hidden');
    }
    scrollToBottom();
}

// Hide typing indicator
function hideTypingIndicator() {
    isTyping = false;
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.classList.add('hidden');
    }
}

// Clear chat history
async function clearChat() {
    if (!confirm('Are you sure you want to clear the chat history?')) return;
    
    try {
        const response = await fetch('/chat/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Reload the page to show fresh chat
            window.location.reload();
        }
    } catch (error) {
        console.error('Error clearing chat:', error);
        alert('Failed to clear chat history. Please try again.');
    }
}

// Send quick message
function sendQuickMessage(message) {
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.value = message;
        const chatForm = document.getElementById('chat-form');
        if (chatForm) {
            chatForm.dispatchEvent(new Event('submit'));
        }
    }
}

// Toggle voice input (placeholder for future implementation)
function toggleVoiceInput() {
    alert('Voice input feature coming soon!');
}

// Initialize chat functionality
function initializeChat() {
    // Handle form submission
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const messageInput = document.getElementById('message-input');
            if (messageInput) {
                const message = messageInput.value.trim();
                if (message) {
                    sendMessage(message);
                }
            }
        });
    }

    // Handle Enter key in input
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const message = this.value.trim();
                if (message) {
                    sendMessage(message);
                }
            }
        });
    }

    // Scroll to bottom on page load
    scrollToBottom();
}

// Export functions for global use
window.sendMessage = sendMessage;
window.clearChat = clearChat;
window.sendQuickMessage = sendQuickMessage;
window.toggleVoiceInput = toggleVoiceInput;
window.initializeChat = initializeChat;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeChat);

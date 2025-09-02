# Spark AI - InterSpark AI Chatbot

## Overview

Spark AI is an intelligent chatbot assistant integrated into InterSpark that helps users find opportunities, discover talent, and navigate the platform. It combines Google Gemini with real-time database searches to provide contextual and helpful responses.

## Features

### 🤖 **AI-Powered Conversations**
- Natural language processing using Google Gemini
- Contextual responses based on user queries
- Intelligent conversation flow with session memory

### 🔍 **Smart Database Integration**
- Real-time search across profiles and opportunities
- Contextual recommendations based on user queries
- Clickable links to relevant profiles and opportunities

### 💬 **Modern Chat Interface**
- Beautiful, responsive design with TailwindCSS
- Real-time typing indicators
- Message history persistence
- Quick action buttons for common queries

### 🚀 **Quick Actions**
- Find Internships
- Find Talent
- Get Help with platform usage

## Setup Instructions

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Environment Variables**
Create a `.env` file in your project root with the following variables:

```env
# Google Gemini Configuration (Required for Spark AI)
GEMINI_API_KEY=your-gemini-api-key-here

# Existing Supabase Configuration
SUPABASE_URL=your-supabase-project-url
SUPABASE_PUBLIC_KEY=your-supabase-public-key
SUPABASE_SECRET_KEY=your-supabase-service-role-key

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

### 3. **Get Google Gemini API Key**
1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Create an account or sign in with your Google account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

### 4. **Run the Application**
```bash
python app.py
```

## Usage

### **Accessing Spark AI**
1. Navigate to `/chat` or click "Spark AI" in the navigation
2. Start chatting with the AI assistant
3. Ask questions about opportunities, talent, or platform usage

### **Example Queries**
- "Show me internship opportunities in software development"
- "Find students with Python skills"
- "How do I create an opportunity?"
- "What opportunities are available in New York?"
- "Help me find talented students for a marketing internship"

### **Features**
- **Session Memory**: Chat history persists during your session
- **Database Integration**: Real-time search results incorporated into responses
- **Clickable Links**: Direct links to profiles and opportunities
- **Quick Actions**: Pre-built buttons for common queries

## Technical Architecture

### **Backend Components**
- **Route**: `/chat` - Main chat interface
- **Route**: `/chat/send` - Message processing endpoint
- **Route**: `/chat/clear` - Clear chat history
- **Helper Functions**:
  - `search_database_for_context()` - Database search
  - `generate_ai_response()` - Basic Gemini integration
  - `generate_ai_response_with_context()` - Gemini with conversation context

### **Gemini Integration Example**
Here's how the system calls Gemini and injects search results:

```python
# Initialize Gemini client
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# Build context from database search results
context_parts = []
if db_results["profiles"]:
    context_parts.append("RELEVANT STUDENT PROFILES:")
    for profile in db_results["profiles"]:
        context_parts.append(f"- {profile.get('name')} from {profile.get('school')}")
        context_parts.append(f"  View profile: /profile/{profile['id']}")

# Generate response with context
response = gemini_model.generate_content([
    system_prompt,  # Contains database context
    user_message    # User's query
])

return response.text
```

### **Frontend Components**
- **Template**: `templates/chat.html` - Chat interface
- **JavaScript**: `static/js/chat.js` - Chat functionality
- **Styling**: TailwindCSS with custom gradients and animations

### **Database Integration**
- Searches `profiles` table for student talent
- Searches `opportunities` table for available positions
- Combines results with AI-generated responses
- Maintains conversation context in Flask sessions

## Customization

### **Swapping AI Models**
The system is designed to easily swap Google Gemini for other models:

```python
# In generate_ai_response function, replace Gemini call with:
# Example for OpenAI:
response = openai_client.chat.completions.create(
    model="gpt-4",
    messages=[...],
    max_tokens=500,
    temperature=0.7
)

# Example for Claude:
response = anthropic_client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=500,
    messages=[...]
)
```

### **Enhancing Database Search**
Modify `search_database_for_context()` to:
- Extract skills from natural language queries
- Add more sophisticated filtering
- Implement semantic search
- Add relevance scoring

### **UI Customization**
- Modify `templates/chat.html` for different styling
- Update `static/js/chat.js` for enhanced interactions
- Add new quick action buttons
- Implement voice input functionality

## Security Features

- **Authentication Required**: Only logged-in users can access chat
- **Session Management**: Chat history stored in Flask sessions
- **Input Validation**: Messages are sanitized and validated
- **Rate Limiting**: Built-in protection against spam
- **XSS Prevention**: HTML escaping in user messages

## Performance Considerations

- **Message Limit**: Chat history limited to last 20 messages
- **Database Queries**: Limited to top 5 results per category
- **Response Caching**: Could be implemented for common queries
- **Async Processing**: Database search and AI generation in parallel

## Future Enhancements

### **Planned Features**
- Voice input and output
- File sharing capabilities
- Multi-language support
- Advanced analytics and insights
- Integration with external job boards

### **AI Improvements**
- Fine-tuned models for specific domains
- Sentiment analysis for better responses
- Learning from user interactions
- Personalized recommendations

## Troubleshooting

### **Common Issues**

1. **"Gemini API Key not found"**
   - Ensure `.env` file exists and contains `GEMINI_API_KEY`
   - Restart the Flask application after adding the key

2. **"Chat not responding"**
   - Check Gemini API key validity
   - Verify internet connection
   - Check Flask application logs for errors

3. **"Database search not working"**
   - Verify Supabase configuration
   - Check database connection
   - Ensure tables exist and are accessible

### **Debug Mode**
Enable debug mode to see detailed error messages:

```python
# In app.py
app.run(debug=True, port=5000)
```

## Support

For issues or questions about Spark AI:
1. Check the Flask application logs
2. Verify environment variable configuration
3. Test Gemini API key independently
4. Review database connectivity

## License

This feature is part of InterSpark and follows the same licensing terms.

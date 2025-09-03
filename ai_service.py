import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class AIService:
    """
    Service class to handle all AI-related functionality for InterSpark.
    """

    def __init__(self, api_key: str):
        """Initialize the AI service with Google Gemini client."""
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is required for AI functionality"
            )
        self.client = genai.Client(api_key=api_key)

    def search_database_for_context(
        self, query: str, supabase_service
    ) -> Dict[str, Any]:
        """
        Search database for relevant profiles and opportunities based on user query.
        Returns structured results that can be used in AI prompt.
        """
        try:
            results = {"profiles": [], "opportunities": [], "total_matches": 0}

            # Search in profiles table
            profile_results = supabase_service.search_students(
                search_query=query,
                skills="",  # Could be enhanced to extract skills from query
                school="",
                grade="",
                location="",
            )

            # Search in opportunities table
            opportunity_results = supabase_service.search_opportunities(
                search_query=query,
                opportunity_type="",
                category="",
                location="",
                skills_needed="",
            )

            # Limit results to top matches
            results["profiles"] = profile_results[:5]  # Top 5 profiles
            results["opportunities"] = opportunity_results[:5]  # Top 5 opportunities
            results["total_matches"] = len(profile_results) + len(opportunity_results)

            return results

        except Exception as e:
            logger.error(f"Error searching database: {str(e)}")
            return {"profiles": [], "opportunities": [], "total_matches": 0}

    def _build_database_context(self, db_results: Dict[str, Any]) -> List[str]:
        """
        Build context strings from database results.
        """
        context_parts = []

        if db_results["profiles"]:
            context_parts.append("RELEVANT STUDENT PROFILES:")
            for profile in db_results["profiles"]:
                context_parts.append(
                    f"- {profile.get('name', 'Unknown')} from {profile.get('school', 'Unknown school')}"
                )
                if profile.get("skills"):
                    skills = profile.get("skills", [])
                    if isinstance(skills, str):
                        try:
                            skills = json.loads(skills)
                        except:
                            skills = [skills]
                    context_parts.append(f"  Skills: {', '.join(skills[:5])}")
                context_parts.append(f"  View profile: /profile/{profile['id']}")

        if db_results["opportunities"]:
            context_parts.append("\nRELEVANT OPPORTUNITIES:")
            for opp in db_results["opportunities"]:
                org_name = "Unknown organization"
                if opp.get("profiles"):
                    org_name = opp["profiles"].get("name", org_name)

                context_parts.append(
                    f"- {opp.get('title', 'Unknown title')} at {org_name}"
                )
                context_parts.append(
                    f"  Type: {opp.get('type', 'Unknown')} | Location: {opp.get('location', 'Unknown')}"
                )
                context_parts.append(f"  View opportunity: /opportunity/{opp['id']}")

        return context_parts

    def _build_conversation_context(self, chat_history: List[Dict[str, Any]]) -> str:
        """
        Build conversation context from recent messages.
        """
        conversation_context = ""
        if len(chat_history) > 2:  # More than just current user message
            recent_messages = chat_history[-6:]  # Last 6 messages for context
            conversation_context = "\n\nCONVERSATION CONTEXT:\n"
            for msg in recent_messages:
                role = "User" if msg["role"] == "user" else "Assistant"
                conversation_context += f"{role}: {msg['content']}\n"

        return conversation_context

    def _build_system_prompt(
        self, context_parts: List[str], conversation_context: str
    ) -> str:
        """
        Build the system prompt for the AI assistant.
        """
        return f"""You are Spark AI, a helpful AI assistant for InterSpark - a platform connecting students with internship and volunteer opportunities.

Your role is to:
1. Provide helpful, conversational responses to user queries
2. When relevant, mention and link to matching profiles or opportunities from our database
3. Be encouraging and supportive, especially for students looking for opportunities
4. Keep responses concise but informative
5. Always format links as clickable URLs (e.g., /profile/123 or /opportunity/456)
6. Maintain conversation flow and context from previous messages

Current database context:
{chr(10).join(context_parts) if context_parts else "No specific matches found in database."}

{conversation_context}

Remember: You're helping users navigate InterSpark and find meaningful connections. Be friendly, professional, and always try to be helpful!"""

    def generate_response_with_context(
        self,
        user_message: str,
        db_results: Dict[str, Any],
        chat_history: List[Dict[str, Any]],
    ) -> str:
        """
        Generate AI response using Google Gemini with database context and conversation history.
        """
        try:
            # Build context components
            context_parts = self._build_database_context(db_results)
            conversation_context = self._build_conversation_context(chat_history)

            # Build the system prompt
            system_prompt = self._build_system_prompt(
                context_parts, conversation_context
            )

            # Build user message with context
            user_prompt = f"""User message: {user_message}

Please provide a helpful response. If there are relevant database matches above, incorporate them naturally into your response with clickable links. If no matches are found, reply naturally: I didn't find any matching profiles or opportunities. Want to try rephrasing your request?"""

            # Generate response using Google Gemini
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(system_instruction=system_prompt),
                contents=user_prompt,
            )

            return response.text

        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again later or contact support if the issue persists."

    def generate_simple_response(
        self, user_message: str, db_results: Dict[str, Any]
    ) -> str:
        """
        Generate AI response without conversation history (for backwards compatibility).
        """
        return self.generate_response_with_context(user_message, db_results, [])

    def extract_skills_from_query(self, query: str) -> List[str]:
        """
        Use AI to extract potential skills from a user query.
        This can be used to enhance database searches.
        """
        try:
            system_prompt = """You are a skill extraction assistant. Your job is to identify technical skills, programming languages, frameworks, tools, or other professional skills mentioned in user queries.

Return only a JSON array of skills found, or an empty array if none are found. Do not include explanatory text.

Examples:
- "I know Python and React" -> ["Python", "React"]
- "Looking for Java developers" -> ["Java"]
- "Need help with machine learning" -> ["Machine Learning"]
- "What opportunities are available?" -> []"""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(system_instruction=system_prompt),
                contents=f"Extract skills from this query: {query}",
            )

            # Try to parse the JSON response
            try:
                skills = json.loads(response.text.strip())
                return skills if isinstance(skills, list) else []
            except json.JSONDecodeError:
                return []

        except Exception as e:
            logger.error(f"Error extracting skills from query: {str(e)}")
            return []

    def enhance_search_query(self, query: str) -> Dict[str, Any]:
        """
        Use AI to analyze and enhance search queries by extracting:
        - Skills mentioned
        - Location references
        - Job types or categories
        - Other search filters
        """
        try:
            system_prompt = """You are a search query analyzer. Analyze user queries for InterSpark (a student internship platform) and extract structured information.

Return a JSON object with these fields:
- "skills": array of technical skills mentioned
- "locations": array of locations/cities mentioned
- "job_types": array of job types (internship, part-time, full-time, volunteer, etc.)
- "categories": array of categories (technology, marketing, design, etc.)
- "general_terms": array of other important search terms

Examples:
"Python developer internship in San Francisco" -> {
    "skills": ["Python"],
    "locations": ["San Francisco"],  
    "job_types": ["internship"],
    "categories": ["technology"],
    "general_terms": ["developer"]
}

Return only valid JSON, no explanatory text."""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(system_instruction=system_prompt),
                contents=f"Analyze this search query: {query}",
            )

            try:
                enhanced_query = json.loads(response.text.strip())
                return enhanced_query if isinstance(enhanced_query, dict) else {}
            except json.JSONDecodeError:
                return {}

        except Exception as e:
            logger.error(f"Error enhancing search query: {str(e)}")
            return {}

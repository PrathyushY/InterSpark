import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

import google.generativeai as genai

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
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def search_database_for_context(
        self, query: str, supabase_service
    ) -> Dict[str, Any]:
        """
        Search database for relevant profiles and opportunities based on user query.
        Uses AI to extract skills and enhance search parameters.
        Returns structured results that can be used in AI prompt.
        """
        try:
            results = {"profiles": [], "opportunities": [], "total_matches": 0}
            
            logger.info(f"Searching database for query: '{query}'")

            # Use AI to enhance the search query
            enhanced_query = self.enhance_search_query(query)
            logger.info(f"Enhanced query: {enhanced_query}")
            
            # Extract skills for more targeted search
            extracted_skills = enhanced_query.get("skills", [])
            skills_param = ",".join(extracted_skills) if extracted_skills else ""
            logger.info(f"Extracted skills: {extracted_skills}")
            
            # Extract locations for search
            locations = enhanced_query.get("locations", [])
            location_param = locations[0] if locations else ""
            
            # Search in profiles table with enhanced parameters
            profile_results = supabase_service.search_students_enhanced(
                search_query=query,
                skills=skills_param,
                school="",
                grade="",
                location=location_param,
            )
            logger.info(f"Found {len(profile_results)} profiles")

            # Search in opportunities table with enhanced parameters
            opportunity_results = supabase_service.search_opportunities(
                search_query=query,
                opportunity_type="",
                category="",
                location=location_param,
                skills_needed=skills_param,
            )
            logger.info(f"Found {len(opportunity_results)} opportunities")

            # Limit results to top matches
            results["profiles"] = profile_results[:5]  # Top 5 profiles
            results["opportunities"] = opportunity_results[:5]  # Top 5 opportunities
            results["total_matches"] = len(profile_results) + len(opportunity_results)

            logger.info(f"Total matches: {results['total_matches']}")
            return results

        except Exception as e:
            logger.error(f"Error searching database: {str(e)}")
            return {"profiles": [], "opportunities": [], "total_matches": 0}

    def _build_database_context(self, db_results: Dict[str, Any]) -> List[str]:
        """
        Build context strings from database results with enhanced profile information.
        """
        context_parts = []

        if db_results["profiles"]:
            context_parts.append("RELEVANT STUDENT PROFILES:")
            for profile in db_results["profiles"]:
                # Basic info
                name = profile.get('name', 'Unknown')
                school = profile.get('school', 'Unknown school')
                grade = profile.get('grade', '')
                location = profile.get('location', '')
                
                context_parts.append(f"- {name} from {school}")
                
                # Add grade and location if available
                if grade:
                    context_parts.append(f"  Grade: {grade}")
                if location:
                    context_parts.append(f"  Location: {location}")
                
                # Enhanced skills display
                if profile.get("skills"):
                    skills = profile.get("skills", [])
                    if isinstance(skills, str):
                        try:
                            skills = json.loads(skills)
                        except:
                            skills = [skills] if skills else []
                    if skills:
                        context_parts.append(f"  Skills: {', '.join(skills[:8])}")  # Show more skills
                
                # Add bio snippet if available
                bio = profile.get('bio', '')
                if bio and len(bio) > 10:
                    bio_snippet = bio[:150] + "..." if len(bio) > 150 else bio
                    context_parts.append(f"  Bio: {bio_snippet}")
                
                context_parts.append(f"  View profile: /profile/{profile['id']}")
                context_parts.append("")  # Add spacing between profiles

        if db_results["opportunities"]:
            context_parts.append("RELEVANT OPPORTUNITIES:")
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
                
                # Add description snippet
                description = opp.get('description', '')
                if description and len(description) > 10:
                    desc_snippet = description[:150] + "..." if len(description) > 150 else description
                    context_parts.append(f"  Description: {desc_snippet}")
                
                context_parts.append(f"  View opportunity: /opportunity/{opp['id']}")
                context_parts.append("")  # Add spacing between opportunities

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
        Build the system prompt for the AI assistant with enhanced capabilities.
        """
        return f"""You are Spark AI, a helpful AI assistant for InterSpark - a platform connecting students with internship and volunteer opportunities.

Your role is to:
1. Provide helpful, conversational responses to user queries
2. When relevant, mention and link to matching profiles or opportunities from our database
3. Be encouraging and supportive, especially for students looking for opportunities
4. Keep responses concise but informative
5. Always format links as clickable URLs (e.g., /profile/123 or /opportunity/456)
6. Maintain conversation flow and context from previous messages
7. **NEW CAPABILITIES:**
   - Summarize profiles when asked (extract key skills, projects, and background from bio)
   - Answer general questions about the platform, internships, career advice, etc.
   - Help users understand what they're looking at in profiles or opportunities
   - Provide career guidance and suggestions based on user interests

Current database context:
{chr(10).join(context_parts) if context_parts else "No specific matches found in database."}

{conversation_context}

Remember: You're helping users navigate InterSpark and find meaningful connections. Be friendly, professional, and always try to be helpful! You can now handle both specific searches AND general conversation about profiles, careers, and the platform."""

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
            response = self.model.generate_content([
                system_prompt,
                user_prompt
            ])

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

            response = self.model.generate_content([
                system_prompt,
                f"Extract skills from this query: {query}"
            ])

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

            response = self.model.generate_content([
                system_prompt,
                f"Analyze this search query: {query}"
            ])

            try:
                enhanced_query = json.loads(response.text.strip())
                return enhanced_query if isinstance(enhanced_query, dict) else {}
            except json.JSONDecodeError:
                return {}

        except Exception as e:
            logger.error(f"Error enhancing search query: {str(e)}")
            return {}

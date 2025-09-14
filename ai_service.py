import json
import logging
import os
from typing import Dict, List, Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

logger = logging.getLogger(__name__)

load_dotenv()

# Initialize the client - it will automatically pick up GEMINI_API_KEY environment variable
client = genai.Client()
MODEL = "gemini-2.5-flash"


# Pydantic models for structured output
class SkillsExtraction(BaseModel):
    skills: List[str]


class SearchAnalysis(BaseModel):
    skills: List[str]
    locations: List[str]
    job_types: List[str]
    categories: List[str]
    general_terms: List[str]
    names: List[str]


class AIService:
    """
    Service class to handle all AI-related functionality for InterSpark.
    Uses the modern Google GenAI SDK with Gemini 2.5 models.
    """

    def __init__(self, api_key: str = None):
        """Initialize the AI service with Google Gemini client."""
        # The modern SDK automatically picks up GEMINI_API_KEY from environment
        # api_key parameter is kept for backward compatibility but not needed
        if not os.getenv("GEMINI_API_KEY") and not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is required for AI functionality"
            )

        # Use the global client instance which is already initialized
        self.client = client

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

            # Extract skills and names for more targeted search
            extracted_skills = enhanced_query.get("skills", [])
            extracted_names = enhanced_query.get("names", [])

            # Always use fallback if AI extraction fails or returns empty results
            if not extracted_skills and not extracted_names:
                extracted_skills = self._extract_skills_fallback(query)
                logger.info(f"Using fallback skill extraction: {extracted_skills}")

            skills_param = ",".join(extracted_skills) if extracted_skills else ""
            logger.info(f"Final extracted skills: {extracted_skills}")
            logger.info(f"Final extracted names: {extracted_names}")

            # Extract locations for search
            locations = enhanced_query.get("locations", [])
            location_param = locations[0] if locations else ""

            # Search in profiles table with enhanced parameters
            # If we have extracted skills or names, use targeted search
            if extracted_skills:
                search_text = ""  # Focus on skills when any skills are detected
            elif extracted_names:
                search_text = " ".join(extracted_names)
            else:
                # Use full query for name/general searches
                search_text = query

            profile_results = supabase_service.search_students_enhanced(
                search_query=search_text,
                skills=skills_param,
                school="",
                grade="",
                location=location_param,
            )
            logger.info(f"Found {len(profile_results)} profiles")

            # Search in opportunities table with enhanced parameters
            # Always use technical skills for skills_needed, filtering out job types and general terms
            technical_skills = [s for s in extracted_skills if s not in ['internship', 'volunteer', 'part-time', 'full-time', 'remote', 'marketing', 'design', 'research', 'web development']]
            opp_skills_param = ",".join(technical_skills) if technical_skills else ""
            
            # Determine search strategy for opportunities
            opp_search_text = query  # Default to full query
            opp_type = ""
            
            # Check if this is an opportunity type-focused query
            job_types = enhanced_query.get("job_types", [])
            opp_type = ""
            
            # Check for opportunity types in job_types, extracted_skills, or query directly
            query_lower = query.lower()
            if job_types or any(term in extracted_skills for term in ['Internship', 'Volunteer', 'Part-time', 'Full-time']) or any(term in query_lower for term in ['internship', 'volunteer', 'part-time', 'full-time']):
                opp_search_text = ""  # Focus on type filtering
                # Map extracted terms to opportunity types (check multiple sources)
                if 'Internship' in job_types or 'Internship' in extracted_skills or 'internship' in query_lower:
                    opp_type = "Internship"
                elif 'Volunteer' in job_types or 'Volunteer' in extracted_skills or 'volunteer' in query_lower:
                    opp_type = "Volunteer"
                elif 'Part-time' in job_types or 'Part-time' in extracted_skills or 'part-time' in query_lower:
                    opp_type = "Part-time"
                elif 'Full-time' in job_types or 'Full-time' in extracted_skills or 'full-time' in query_lower:
                    opp_type = "Full-time"
            elif technical_skills:
                opp_search_text = ""  # Focus on skills search only
            else:
                opp_search_text = ""  # Empty search for general queries
            
            logger.info(f"Opportunity search parameters: search_query='{opp_search_text}', type='{opp_type}', location='{location_param}', skills='{opp_skills_param}'")
            
            opportunity_results = supabase_service.search_opportunities(
                search_query=opp_search_text,
                opportunity_type=opp_type,
                category="",
                location=location_param,
                skills_needed=opp_skills_param,
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
                name = profile.get("name", "Unknown")
                school = profile.get("school", "Unknown school")
                grade = profile.get("grade", "")
                location = profile.get("location", "")
                profile_id = profile.get("id", "")
                profile_image = profile.get("profile_image", "")

                context_parts.append(f"- {name} from {school}")
                context_parts.append(f"  ID: {profile_id}")

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
                        context_parts.append(
                            f"  Skills: {', '.join(skills[:8])}"
                        )  # Show more skills

                # Add bio snippet if available
                bio = profile.get("bio", "")
                if bio and len(bio) > 10:
                    bio_snippet = bio[:150] + "..." if len(bio) > 150 else bio
                    context_parts.append(f"  Bio: {bio_snippet}")

                # Add profile image if available
                if profile_image:
                    context_parts.append(f"  Profile Image: {profile_image}")

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
                context_parts.append(f"  ID: {opp.get('id', '')}")
                context_parts.append(
                    f"  Type: {opp.get('type', 'Unknown')} | Location: {opp.get('location', 'Unknown')}"
                )
                context_parts.append(
                    f"  Duration: {opp.get('duration', 'Not specified')}"
                )

                # Add description snippet
                description = opp.get("description", "")
                if description and len(description) > 10:
                    desc_snippet = (
                        description[:150] + "..."
                        if len(description) > 150
                        else description
                    )
                    context_parts.append(f"  Description: {desc_snippet}")

                # Add skills needed
                skills_needed = opp.get("skills_needed", [])
                if skills_needed:
                    if isinstance(skills_needed, str):
                        try:
                            skills_needed = json.loads(skills_needed)
                        except:
                            skills_needed = [skills_needed] if skills_needed else []
                    if skills_needed:
                        context_parts.append(
                            f"  Skills Needed: {', '.join(skills_needed[:5])}"
                        )

                context_parts.append(f"  View opportunity: /opportunity/{opp['id']}")
                context_parts.append("")  # Add spacing between opportunities

        return context_parts

    def _build_conversation_context(self, chat_history: List[Dict[str, Any]]) -> str:
        """
        Build conversation context from recent messages.
        """
        conversation_context = ""
        if len(chat_history) > 1:  # More than just current user message
            recent_messages = chat_history[-6:]  # Last 6 messages for context
            conversation_context = "\n\nRECENT CONVERSATION HISTORY:\n"
            
            for i, msg in enumerate(recent_messages):
                role = "User" if msg["role"] == "user" else "Assistant"
                content = msg['content']
                
                # Include recent messages for context, truncate very long ones
                if len(content) > 500:
                    content = content[:500] + "..."
                
                conversation_context += f"{role} Message {i+1}: {content}\n\n"
            
            logger.info(f"Built conversation context with {len(recent_messages)} messages")

        return conversation_context

    def _build_system_prompt(
        self, context_parts: List[str], conversation_context: str
    ) -> str:
        """
        Build the system prompt for the AI assistant with enhanced capabilities.
        """
        return f"""You are Spark Agent, a helpful AI assistant for InterSpark - a platform connecting students with internship and volunteer opportunities.

Your role is to:
1. Provide helpful, conversational responses to user queries
2. **CRITICAL: ONLY create HTML cards for profiles and opportunities that are EXPLICITLY provided in the "Current database context" section below**
3. **NEVER create fake or example profiles - only use actual data from the database context**
4. Be encouraging and supportive, especially for students looking for opportunities
5. Keep responses concise but informative
6. Maintain conversation flow and context from previous messages

**STRICT DATA USAGE RULES:**
- You can ONLY create HTML cards for profiles/opportunities that appear in the "RELEVANT STUDENT PROFILES" or "RELEVANT OPPORTUNITIES" sections below
- If no profiles are found in the database context, say "I didn't find any matching student profiles" - DO NOT create fake examples
- If no opportunities are found in the database context, say "I didn't find any matching opportunities" - DO NOT create fake examples
- Use ONLY the exact names, schools, skills, and other data provided in the database context

**PROFILE CARD FORMAT (ONLY when profiles exist in database context):**
   <div class="bg-white border border-gray-200 rounded-lg p-4 mb-3 hover:shadow-md transition-shadow cursor-pointer" onclick="window.open('/profile/[PROFILE_ID]', '_blank')">
     <div class="flex items-center space-x-3">
       <img src="[PROFILE_IMAGE_URL]" alt="[NAME]" class="w-12 h-12 rounded-full object-cover" onerror="this.src='https://via.placeholder.com/48x48/3B82F6/FFFFFF?text=[FIRST_INITIAL]'">
       <div class="flex-1">
         <h4 class="font-semibold text-gray-900">[NAME]</h4>
         <p class="text-sm text-gray-600">[GRADE] at [SCHOOL]</p>
         <p class="text-xs text-gray-500">[LOCATION]</p>
         <div class="flex flex-wrap gap-1 mt-2">
           [SKILLS_AS_BADGES]
         </div>
       </div>
       <i class="fas fa-external-link-alt text-gray-400"></i>
     </div>
   </div>
   
   For skills badges, use: <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">[SKILL]</span>

**OPPORTUNITY CARD FORMAT (ONLY when opportunities exist in database context):**
   <div class="bg-white border border-gray-200 rounded-lg p-4 mb-3 hover:shadow-md transition-shadow cursor-pointer" onclick="window.open('/opportunity/[OPPORTUNITY_ID]', '_blank')">
     <div class="flex items-start space-x-3">
       <div class="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
         <i class="fas fa-briefcase text-white text-lg"></i>
       </div>
       <div class="flex-1">
         <h4 class="font-semibold text-gray-900">[TITLE]</h4>
         <p class="text-sm text-gray-600">[TYPE] at [ORGANIZATION]</p>
         <p class="text-xs text-gray-500">[LOCATION] • [DURATION]</p>
         <p class="text-sm text-gray-700 mt-2 line-clamp-2">[DESCRIPTION_SNIPPET]</p>
         <div class="flex flex-wrap gap-1 mt-2">
           [SKILLS_AS_BADGES]
         </div>
       </div>
       <i class="fas fa-external-link-alt text-gray-400"></i>
     </div>
   </div>
   
   For skills badges, use: <span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">[SKILL]</span>

Current database context:
{chr(10).join(context_parts) if context_parts else "No specific matches found in database."}

{conversation_context}

**CRITICAL CONVERSATION HANDLING:**
- When users say "summarize the opportunity", "this opportunity", "the one you showed", "in your last message", etc., ALWAYS check the RECENT CONVERSATION HISTORY section
- Look for Assistant messages that contain opportunity or profile information
- If you see opportunity cards, profile cards, or detailed information in recent Assistant messages, use that information to answer follow-up questions
- Pay special attention to Assistant messages that mention specific opportunities like "Backend Developer", "Marketing Assistant", etc.
- When users ask for summaries or details about "the opportunity" or "this opportunity", refer back to what you previously shared in the conversation

**REMEMBER: NEVER create fake profiles or opportunities. Only use data that exists in the database context above!**"""

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

Please provide a helpful response. If there are relevant database matches above, incorporate them naturally into your response with clickable cards.

**IMPORTANT: For conversational references like "summarize the opportunity", "this opportunity", "the one you showed":**
1. FIRST check the RECENT CONVERSATION HISTORY section above
2. Look for Assistant messages that mentioned specific opportunities or profiles
3. If you find relevant information in the conversation history, use that to answer the user's question
4. Provide summaries or details based on what you previously shared in the conversation
5. If you previously showed an opportunity card for "Backend Developer" or any other opportunity, reference that specific information

If no matches are found and no relevant conversation history, reply naturally: I didn't find any matching profiles or opportunities. Want to try rephrasing your request?"""

            # Generate response using Google Gemini with modern SDK
            response = self.client.models.generate_content(
                model=MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    # Disable thinking for faster responses (can be enabled if quality is preferred over speed)
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
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
        Use AI to extract potential skills from a user query using structured output.
        This can be used to enhance database searches.
        """
        try:
            system_prompt = """You are a skill extraction assistant. Your job is to identify technical skills, programming languages, frameworks, tools, or other professional skills mentioned in user queries.

Return a structured response with the skills found. Use proper capitalization for skill names.

Examples:
- "I know Python and React" -> skills: ["Python", "React"]
- "Looking for Java developers" -> skills: ["Java"]
- "Need help with machine learning" -> skills: ["Machine Learning"]
- "Show me students with artificial intelligence projects" -> skills: ["Artificial Intelligence"]
- "Find someone with data science experience" -> skills: ["Data Science"]
- "Web development internships" -> skills: ["Web Development"]
- "What opportunities are available?" -> skills: []

IMPORTANT: Always extract skills even if they are multi-word (like "Machine Learning", "Artificial Intelligence", "Data Science", "Web Development", etc.)"""

            response = self.client.models.generate_content(
                model=MODEL,
                contents=f"Extract skills from this query: {query}",
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    response_mime_type="application/json",
                    response_schema=SkillsExtraction,
                ),
            )

            # Parse the structured JSON response
            try:
                result = json.loads(response.text)
                return result.get("skills", [])
            except json.JSONDecodeError:
                logger.error(f"Failed to parse structured response: {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error extracting skills from query: {str(e)}")
            return []

    def enhance_search_query(self, query: str) -> Dict[str, Any]:
        """
        Use AI to analyze and enhance search queries using structured output for reliability.
        """
        try:
            system_prompt = """You are a search query analyzer for InterSpark (a student internship platform). Analyze user queries and extract structured information.

Return structured data with these fields:
- skills: array of technical skills mentioned
- locations: array of locations/cities mentioned  
- job_types: array of job types (Internship, Part-time, Full-time, Volunteer, etc.)
- categories: array of categories (Technology, Marketing, Design, etc.)
- general_terms: array of other important search terms
- names: array of person names mentioned

Examples:
- "Python developer internship in San Francisco" -> skills: ["Python"], locations: ["San Francisco"], job_types: ["Internship"], categories: ["Technology"], general_terms: ["developer"], names: []
- "Show me internship opportunities" -> skills: [], locations: [], job_types: ["Internship"], categories: [], general_terms: ["opportunities"], names: []
- "Find volunteer work" -> skills: [], locations: [], job_types: ["Volunteer"], categories: [], general_terms: ["work"], names: []
- "Tell me about Hridhay's profile" -> skills: [], locations: [], job_types: [], categories: [], general_terms: ["profile"], names: ["Hridhay"]

IMPORTANT: Always extract job types like Internship, Volunteer, Part-time, Full-time when mentioned."""

            response = self.client.models.generate_content(
                model=MODEL,
                contents=f"Analyze this search query: {query}",
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    response_mime_type="application/json",
                    response_schema=SearchAnalysis,
                ),
            )

            logger.info(f"Gemini API response: {response.text}")

            try:
                enhanced_query = json.loads(response.text)
                logger.info(f"Parsed enhanced query: {enhanced_query}")
                return enhanced_query if isinstance(enhanced_query, dict) else {}
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}, response: {response.text}")
                return {}

        except Exception as e:
            logger.error(f"Error enhancing search query: {str(e)}")
            return {}

    def _extract_skills_fallback(self, query: str) -> List[str]:
        """
        Fallback skill extraction using keyword matching.
        Used when AI extraction fails or returns empty results.
        """
        query_lower = query.lower()

        # Common programming skills and technologies
        skill_keywords = {
            "Python": ["python", "py"],
            "JavaScript": ["javascript", "js", "node.js", "nodejs"],
            "React": ["react", "reactjs", "react.js"],
            "Java": ["java"],
            "HTML": ["html", "html5"],
            "CSS": ["css", "css3"],
            "SQL": ["sql", "mysql", "postgresql", "database"],
            "Machine Learning": [
                "machine learning",
                "ml",
                "artificial intelligence",
                "ai",
            ],
            "Data Science": ["data science", "data analysis", "analytics"],
            "Web Development": [
                "web development",
                "web dev",
                "frontend",
                "backend",
                "full stack",
            ],
            "C++": ["c++", "cpp"],
            "C#": ["c#", "csharp"],
            "PHP": ["php"],
            "Ruby": ["ruby"],
            "Swift": ["swift"],
            "Kotlin": ["kotlin"],
            "Go": ["golang", "go programming"],
            "Rust": ["rust"],
            "TypeScript": ["typescript", "ts"],
            "Vue": ["vue", "vue.js", "vuejs"],
            "Angular": ["angular", "angularjs"],
            "Django": ["django"],
            "Flask": ["flask"],
            "Spring": ["spring", "spring boot"],
            "Docker": ["docker"],
            "Kubernetes": ["kubernetes", "k8s"],
            "AWS": ["aws", "amazon web services"],
            "Git": ["git", "github", "version control"],
            "Artificial Intelligence": ["artificial intelligence", "ai", "machine learning", "ml"],
        }
        
        # Opportunity-specific terms
        opportunity_keywords = {
            "Internship": ["internship", "intern", "internships"],
            "Volunteer": ["volunteer", "volunteering"],
            "Part-time": ["part-time", "part time"],
            "Full-time": ["full-time", "full time"],
            "Remote": ["remote", "work from home"],
            "Marketing": ["marketing", "social media"],
            "Design": ["design", "ui", "ux", "graphic design"],
            "Research": ["research", "data analysis"],
        }

        found_skills = []
        
        # Check skill keywords first (prioritize exact matches for multi-word skills)
        for skill, keywords in skill_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                found_skills.append(skill)
        
        # Also check for opportunity-related terms
        for term, keywords in opportunity_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                found_skills.append(term)

        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in found_skills:
            if skill not in seen:
                seen.add(skill)
                unique_skills.append(skill)

        return unique_skills

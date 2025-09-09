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
            
            # Extract skills and names for more targeted search
            extracted_skills = enhanced_query.get("skills", [])
            extracted_names = enhanced_query.get("names", [])
            
            # Fallback: Use keyword matching if AI extraction fails
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
                search_text = ""
            elif extracted_names:
                search_text = " ".join(extracted_names)
            else:
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
            opportunity_results = supabase_service.search_opportunities(
                search_query=search_text,
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
                profile_id = profile.get('id', '')
                profile_image = profile.get('profile_image', '')
                
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
                        context_parts.append(f"  Skills: {', '.join(skills[:8])}")  # Show more skills
                
                # Add bio snippet if available
                bio = profile.get('bio', '')
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
2. When relevant, create interactive profile cards for matching students using HTML
3. Be encouraging and supportive, especially for students looking for opportunities
4. Keep responses concise but informative
5. **IMPORTANT: When showing student profiles, create HTML profile cards instead of just text links**
6. Maintain conversation flow and context from previous messages
7. **PROFILE CARD FORMAT:**
   When showing student profiles, create interactive HTML cards directly in your response (no code blocks).
   Use this exact HTML structure for each profile:
   
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
   
   **IMPORTANT: Generate the HTML directly in your response, NOT inside code blocks or backticks.**

Current database context:
{chr(10).join(context_parts) if context_parts else "No specific matches found in database."}

{conversation_context}

Remember: Always create interactive HTML profile cards when showing student profiles. Make them clickable and visually appealing!"""

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
                # Clean the response text by removing code block markers
                clean_text = response.text.strip()
                if clean_text.startswith('```json'):
                    clean_text = clean_text[7:]  # Remove ```json
                if clean_text.endswith('```'):
                    clean_text = clean_text[:-3]  # Remove ```
                clean_text = clean_text.strip()
                
                skills = json.loads(clean_text)
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
- "names": array of person names mentioned

Examples:
"Python developer internship in San Francisco" -> {
    "skills": ["Python"],
    "locations": ["San Francisco"],  
    "job_types": ["internship"],
    "categories": ["technology"],
    "general_terms": ["developer"],
    "names": []
}

"Tell me about Hridhay's profile" -> {
    "skills": [],
    "locations": [],
    "job_types": [],
    "categories": [],
    "general_terms": ["profile"],
    "names": ["Hridhay"]
}

Return only valid JSON, no explanatory text."""

            response = self.model.generate_content([
                system_prompt,
                f"Analyze this search query: {query}"
            ])

            logger.info(f"Gemini API response: {response.text}")
            
            try:
                # Clean the response text by removing code block markers
                clean_text = response.text.strip()
                if clean_text.startswith('```json'):
                    clean_text = clean_text[7:]  # Remove ```json
                if clean_text.endswith('```'):
                    clean_text = clean_text[:-3]  # Remove ```
                clean_text = clean_text.strip()
                
                enhanced_query = json.loads(clean_text)
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
            'python': ['python', 'py'],
            'javascript': ['javascript', 'js', 'node.js', 'nodejs'],
            'react': ['react', 'reactjs', 'react.js'],
            'java': ['java'],
            'html': ['html', 'html5'],
            'css': ['css', 'css3'],
            'sql': ['sql', 'mysql', 'postgresql', 'database'],
            'machine learning': ['machine learning', 'ml', 'ai', 'artificial intelligence'],
            'data science': ['data science', 'data analysis', 'analytics'],
            'web development': ['web development', 'web dev', 'frontend', 'backend', 'full stack'],
            'c++': ['c++', 'cpp'],
            'c#': ['c#', 'csharp'],
            'php': ['php'],
            'ruby': ['ruby'],
            'swift': ['swift'],
            'kotlin': ['kotlin'],
            'go': ['golang', 'go programming'],
            'rust': ['rust'],
            'typescript': ['typescript', 'ts'],
            'vue': ['vue', 'vue.js', 'vuejs'],
            'angular': ['angular', 'angularjs'],
            'django': ['django'],
            'flask': ['flask'],
            'spring': ['spring', 'spring boot'],
            'docker': ['docker'],
            'kubernetes': ['kubernetes', 'k8s'],
            'aws': ['aws', 'amazon web services'],
            'git': ['git', 'github', 'version control']
        }
        
        found_skills = []
        for skill, keywords in skill_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                found_skills.append(skill)
        
        return found_skills

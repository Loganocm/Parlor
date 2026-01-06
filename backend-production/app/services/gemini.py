import google.generativeai as genai
from typing import List, Dict
from app.config import settings
from app.models import Restaurant, AIGeneratedSummary
import json
import logging

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google Gemini API"""
    
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("Gemini API key is required")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-3-flash-preview')  # Use Gemini 3 Flash Preview as requested
    
    def rank_restaurants(
        self,
        restaurants: List[Restaurant],
        search_request
    ) -> List[Restaurant]:
        """
        Use Gemini AI to rank all restaurants in order of recommendation.
        
        Args:
            restaurants: List of restaurants to rank (typically 15)
            search_request: Original search request with user preferences
            
        Returns:
            List of restaurants in ranked order (best first)
        """
        if len(restaurants) <= 1:
            return restaurants
        
        try:
            # Create a concise prompt for Gemini
            prompt = self._create_ranking_prompt(restaurants, search_request)
            
            # Get response from Gemini with optimized settings for speed
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Lower temperature for more consistent results
                    max_output_tokens=500,  # Limit output for faster response
                    response_mime_type="application/json" # Enforce valid JSON response
                )
            )
            
            # Parse the response to get ranked restaurant IDs
            ranked_ids = self._parse_ranking_response(response.text, restaurants)
            
            # Return restaurants in ranked order
            if len(ranked_ids) >= len(restaurants):
                # Create a map for quick lookup
                restaurant_map = {r.id: r for r in restaurants}
                ranked_restaurants = [restaurant_map[rid] for rid in ranked_ids if rid in restaurant_map]
                
                # Add any missing restaurants at the end (fallback)
                ranked_ids_set = set(ranked_ids)
                for r in restaurants:
                    if r.id not in ranked_ids_set:
                        ranked_restaurants.append(r)
                
                return ranked_restaurants
            else:
                # If parsing failed, fall back to rating-based sorting
                logger.warning("Gemini ranking failed, falling back to rating sort")
                return sorted(restaurants, key=lambda x: (-x.rating, x.distance))
            
        except Exception as e:
            print(f"Gemini ranking error: {e}")
            # Fall back to simple sorting by rating and distance
            return sorted(restaurants, key=lambda x: (-x.rating, x.distance))
    
    def _create_ranking_prompt(
        self,
        restaurants: List[Restaurant],
        search_request
    ) -> str:
        """Create a concise prompt for restaurant ranking"""
        
        # Build compact restaurant list for prompt
        restaurant_info = []
        for i, r in enumerate(restaurants, 1):
            info = f"{i}. {r.name} | {r.rating}★ | {'$' * r.priceLevel} | {r.distance}mi | ID:{r.id}"
            restaurant_info.append(info)
        
        restaurants_text = "\n".join(restaurant_info)
        
        # Build preferences text
        preferences_text = "balanced quality and distance"
        if search_request.preferences:
            prefs = search_request.preferences
            pref_parts = []
            if prefs.dietaryRestrictions:
                pref_parts.append(f"dietary: {', '.join(prefs.dietaryRestrictions)}")
            if prefs.minRating:
                pref_parts.append(f"min {prefs.minRating}★")
            if prefs.maxDistance:
                pref_parts.append(f"max {prefs.maxDistance}mi")
            if pref_parts:
                preferences_text = ", ".join(pref_parts)
        
        prompt = f"""Rank these pizza restaurants from best to worst for a user prioritizing {preferences_text}.

Restaurants:
{restaurants_text}

Return ONLY a JSON array of restaurant IDs in ranked order (best first).
Format: ["id1", "id2", "id3", ...]

Response:"""
        
        return prompt
    
    def _parse_ranking_response(self, response_text: str, restaurants: List[Restaurant]) -> List[str]:
        """Parse Gemini's ranking response to extract ordered restaurant IDs"""
        try:
            # Try to extract JSON from the response
            # Remove any markdown code blocks
            cleaned = response_text.strip()
            if '```' in cleaned:
                # Extract content between code blocks
                parts = cleaned.split('```')
                for part in parts:
                    if '[' in part and ']' in part:
                        cleaned = part.strip()
                        if cleaned.startswith('json'):
                            cleaned = cleaned[4:].strip()
                        break
            
            # Parse JSON
            # Sometimes models return single quotes instead of double quotes
            cleaned = cleaned.replace("'", '"')
            
            ranked_ids = json.loads(cleaned)
            
            # Validate that these are actual restaurant IDs
            valid_ids = {r.id for r in restaurants}
            ranked_ids = [str(id) for id in ranked_ids] # Ensure all are strings
            ranked_ids = [id for id in ranked_ids if id in valid_ids]
            
            return ranked_ids
        except Exception as e:
            print(f"Error parsing Gemini ranking response: {e}")
            print(f"Original response: {response_text}") # Debug log
            return []
    
    def generate_restaurant_summary(
        self,
        restaurant: Restaurant,
        reviews: List[Dict] = None,
        preferences: List[str] = None
    ) -> AIGeneratedSummary:
        """
        Generate an AI-powered summary for a restaurant based on real-world reviews
        
        Args:
            restaurant: The restaurant to summarize
            reviews: List of user reviews from Google Places API
            preferences: User preferences to consider
            
        Returns:
            AI-generated summary
        """
        try:
            # Format reviews for the prompt
            reviews_text = "No reviews available."
            if reviews:
                # Take top 7 reviews as requested
                top_reviews = reviews[:7]
                reviews_list = []
                for r in top_reviews:
                    # distinct user, rating, text
                    text = r.get('text', {}).get('text', '') if isinstance(r.get('text'), dict) else str(r.get('text', ''))
                    rating = r.get('rating', 'N/A')
                    if text:
                        reviews_list.append(f"- {rating}/5 stars: {text}")
                
                if reviews_list:
                    reviews_text = "\n".join(reviews_list)

            prompt = f"""Create a focused, authentic summary for this pizza restaurant based heavily on the following real-world customer reviews.
            
Restaurant: {restaurant.name}
Details: {restaurant.rating}/5 stars, {'$' * restaurant.priceLevel}, {restaurant.distance} miles away, {restaurant.address}

Real Customer Reviews:
{reviews_text}

Provide:
1. A 2-3 sentence summary synthesizing the consensus from the reviews (be honest about pros and cons mentioned).
2. 2-3 key highlights mentioned repeatedly in reviews (array).
3. 1-2 specific food/drink recommendations mentioned in reviews (array).

Format your response as valid JSON with keys: "summary", "highlights" (array), "recommendations" (array)
Example:
{{
  "summary": "Reviews consistently praise the wood-fired crust but note the service can be slow...",
  "highlights": ["Amazing crust", "Loud atmosphere"],
  "recommendations": ["Pepperoni slice", "Garlic knots"]
}}
"""
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            # Parse response
            result = self._parse_summary_response(response.text)
            
            return AIGeneratedSummary(
                restaurantId=restaurant.id,
                summary=result.get('summary', 'A great pizza place worth trying!'),
                highlights=result.get('highlights', ['Great pizza', 'Good service']),
                recommendations=result.get('recommendations', ['Try their signature pizza'])
            )
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            # Return a default summary
            return AIGeneratedSummary(
                restaurantId=restaurant.id,
                summary=f"{restaurant.name} is a highly-rated pizza restaurant with a {restaurant.rating}/5 star rating.",
                highlights=[
                    f"Rated {restaurant.rating}/5 stars",
                    f"Only {restaurant.distance} miles away"
                ],
                recommendations=["Check out their menu online before visiting"]
            )
    
    def _parse_summary_response(self, response_text: str) -> Dict:
        """Parse the summary response from Gemini"""
        try:
            # Clean up the response
            cleaned = response_text.strip()
            if '```' in cleaned:
                parts = cleaned.split('```')
                for part in parts:
                    if '{' in part and '}' in part:
                        cleaned = part.strip()
                        if cleaned.startswith('json'):
                            cleaned = cleaned[4:].strip()
                        break
            
            # Parse JSON
            result = json.loads(cleaned)
            return result
        except Exception as e:
            print(f"Error parsing summary response: {e}")
            return {}


# Singleton instance - will be created on demand
_gemini_service_instance = None


def get_gemini_service() -> GeminiService:
    """Get or create the GeminiService singleton instance"""
    global _gemini_service_instance
    if _gemini_service_instance is None:
        _gemini_service_instance = GeminiService()
    return _gemini_service_instance


# For backward compatibility
gemini_service = None  # Will be set when get_gemini_service() is called

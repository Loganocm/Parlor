"""
Parlor Pizza Recommendation API.

This module provides the FastAPI application for pizza restaurant
recommendations using Google Places API and Gemini AI.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import logging
import uuid
import hashlib
import random

from app.config import settings
from app.models import (
    SearchRequest,
    Restaurant,
    GeocodeRequest,
    GeocodeResponse,
    AIGeneratedSummary,
    RecommendationsResponse
)
from app.services.google_places import get_google_places_service
from app.services.gemini import get_gemini_service
import requests
from fastapi.responses import StreamingResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory session cache for ranked restaurants
# Format: {session_id: {"restaurants": List[Restaurant], "search_params": dict}}
session_cache: Dict[str, Dict] = {}

# Create FastAPI app
app = FastAPI(
    title="Parlor Pizza Recommendation API",
    description="Backend API for AI-powered pizza restaurant recommendations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    Root endpoint providing API information.
    
    Returns:
        dict: API metadata and status
    """
    return {
        "message": "Parlor Pizza Recommendation API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/api/media/{resource_name:path}")
def get_photo_proxy(resource_name: str):
    """
    Proxy Google Places photos to avoid exposing API key on frontend.
    """
    if not resource_name:
         raise HTTPException(status_code=404, detail="Resource name required")
         
    try:
        api_key = settings.GOOGLE_PLACES_API_KEY
        # Places API New uses this format for media
        url = f"https://places.googleapis.com/v1/{resource_name}/media"
        
        params = {
            "key": api_key,
            "maxHeightPx": 400,
            "maxWidthPx": 400
        }
        
        # Stream the response
        external_req = requests.get(url, params=params, stream=True, timeout=10)
        
        if external_req.status_code != 200:
             logger.error(f"Error fetching photo: {external_req.status_code} {external_req.text}")
             raise HTTPException(status_code=404, detail="Photo not found")

        return StreamingResponse(
            external_req.iter_content(chunk_size=8192), 
            media_type=external_req.headers.get("content-type", "image/jpeg")
        )
    except Exception as e:
        logger.error(f"Photo proxy error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch photo")


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        dict: Health status
    """
    return {"status": "healthy"}


@app.get("/api/places/autocomplete")
def get_places_autocomplete(input: str, session_token: str = None):
    """
    Get autocomplete predictions for a search query.
    Proxies the request to Google Places API (New) to avoid frontend API key issues.
    """
    try:
        places_service = get_google_places_service()
        predictions = places_service.get_autocomplete_predictions(input, session_token)
        return predictions
    except Exception as e:
        logger.error(f"Autocomplete error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/places/details/{place_id}")
def get_place_details_proxy(place_id: str):
    """
    Get details for a specific place ID.
    Proxies to Google Places API (New).
    """
    try:
        places_service = get_google_places_service()
        # Ensure place_id doesn't have 'places/' prefix if passed in URL, 
        # but service handles it.
        details = places_service.get_place_details(place_id)
        return details
    except Exception as e:
        logger.error(f"Place details error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


import asyncio

@app.post("/api/pizza-recommendations", response_model=List[Restaurant])
def get_pizza_recommendations(search_request: SearchRequest):
    """
    Get AI-curated pizza restaurant recommendations.
    
    This endpoint:
    1. Geocodes the user's address if coordinates not provided
    2. Searches for nearby pizza restaurants using Google Places API (top 15)
    3. Uses Gemini AI to rank all 15 restaurants once
    4. Returns 3 restaurants at a time based on offset (0, 3, 6, 9, 12)
    5. Loops back to the start after showing all 5 sets
    
    Args:
        search_request: Search criteria including location, preferences, offset, and sessionId
        
    Returns:
        List[Restaurant]: 3 recommended restaurants at the current offset
        
    Raises:
        HTTPException: 400 for invalid input, 500 for server errors
    """
    try:
        google_places_service = get_google_places_service()
        gemini_service = get_gemini_service()
        
        # Determine user location
        if search_request.latitude is None or search_request.longitude is None:
            lat, lng = google_places_service.geocode_address(search_request.address)
            logger.info(f"Geocoded address '{search_request.address}' to ({lat}, {lng})")
        else:
            lat = search_request.latitude
            lng = search_request.longitude
        
        # Extract search parameters
        max_distance = 10.0
        min_rating = 3.0
        dietary_restrictions = []
        if search_request.preferences:
            max_distance = search_request.preferences.maxDistance
            min_rating = search_request.preferences.minRating
            dietary_restrictions = search_request.preferences.dietaryRestrictions
        
        # Create a search key for caching based on location and preferences
        search_key = hashlib.md5(
            f"{lat}_{lng}_{max_distance}_{min_rating}_{dietary_restrictions}".encode()
        ).hexdigest()
        
        # Check if we have cached results for this session
        session_id = search_request.sessionId
        ranked_restaurants = None
        
        if session_id and session_id in session_cache:
            cached_data = session_cache[session_id]
            # Verify the search parameters match
            if cached_data.get("search_key") == search_key:
                ranked_restaurants = cached_data["restaurants"]
                logger.info(f"Using cached results for session {session_id}")
        
        # If no cache hit, fetch and rank restaurants
        if ranked_restaurants is None:
            # Search for pizza places - get top 15 by rating
            places = google_places_service.search_pizza_places(
                latitude=lat,
                longitude=lng,
                radius_miles=max_distance,
                min_rating=min_rating,
                max_results=20,  # Get 20 to ensure we have enough after filtering
                dietary_restrictions=dietary_restrictions
            )
            
            logger.info(f"Found {len(places)} pizza places")
            
            if not places:
                logger.warning("No pizza places found matching criteria")
                return []
            
            # Convert to Restaurant models
            restaurants = [
                google_places_service.convert_to_restaurant_model(place, lat, lng)
                for place in places
            ]
            
            # Sort by rating (descending) and take top 7
            restaurants_sorted = sorted(restaurants, key=lambda x: (-x.rating, x.distance))
            top_7_restaurants = restaurants_sorted[:7]
            
            logger.info(f"Selected top 7 restaurants by rating from {len(restaurants)} total")
            
            # Select 3 random restaurants from the top 7
            # If we have fewer than 3, just take all of them
            if len(top_7_restaurants) <= 3:
                ranked_restaurants = top_7_restaurants
            else:
                ranked_restaurants = random.sample(top_7_restaurants, 3)
            
            logger.info(f"Randomly selected {len(ranked_restaurants)} restaurants from top 7")
            
            # Note: We no longer rank with Gemini here to avoid timeouts/errors.
            # Focused summaries will be generated on demand via /summary endpoint.
            
            # Create or update session
            if not session_id:
                session_id = str(uuid.uuid4())
            
            session_cache[session_id] = {
                "restaurants": ranked_restaurants,
                "search_key": search_key
            }
            
            logger.info(f"Ranked {len(ranked_restaurants)} restaurants and cached for session {session_id}")
        
        # Calculate the offset (loop back if needed)
        offset = search_request.offset % len(ranked_restaurants)
        
        # Return 3 restaurants starting from offset
        end_idx = offset + 3
        result = ranked_restaurants[offset:end_idx]
        
        # If we don't have enough restaurants, loop back to the start
        if len(result) < 3 and len(ranked_restaurants) > 0:
            remaining = 3 - len(result)
            result.extend(ranked_restaurants[:remaining])
        
        logger.info(f"Returning {len(result)} recommendations (offset: {offset})")
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@app.post("/api/geocode", response_model=GeocodeResponse)
def geocode_address(request: GeocodeRequest):
    """
    Convert an address to geographic coordinates.
    
    Args:
        request: Geocoding request with address
        
    Returns:
        GeocodeResponse: Latitude and longitude coordinates
        
    Raises:
        HTTPException: 400 if geocoding fails
    """
    try:
        google_places_service = get_google_places_service()
        lat, lng = google_places_service.geocode_address(request.address)
        logger.info(f"Successfully geocoded: {request.address}")
        return GeocodeResponse(latitude=lat, longitude=lng)
    except Exception as e:
        logger.error(f"Geocoding failed for '{request.address}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Geocoding failed: {str(e)}"
        )


@app.get("/api/restaurants/{restaurant_id}/summary", response_model=AIGeneratedSummary)
def get_restaurant_summary(restaurant_id: str):
    """
    Get an AI-generated summary for a specific restaurant.
    
    Retrieves detailed information from Google Places and generates
    a personalized summary using Gemini AI.
    
    Args:
        restaurant_id: Google Places restaurant ID
        
    Returns:
        AIGeneratedSummary: AI-generated restaurant summary
        
    Raises:
        HTTPException: 404 if restaurant not found, 500 for other errors
    """
    try:
        google_places_service = get_google_places_service()
        gemini_service = get_gemini_service()
        
        # Get place details from Google Places API
        place_details = google_places_service.get_place_details(restaurant_id)
        
        if not place_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found"
            )
        
        # Extract reviews if available
        reviews = place_details.get('reviews', [])
        
        # Create Restaurant object for summary generation
        location = place_details.get('location', {})
        display_name = place_details.get('displayName', {})
        name = display_name.get('text', 'Unknown') if isinstance(display_name, dict) else str(display_name)
        
        restaurant = Restaurant(
            id=restaurant_id,
            name=name,
            address=place_details.get('formattedAddress', 'N/A'),
            distance=0.0,  # Not relevant for summary
            rating=place_details.get('rating', 0.0),
            priceLevel=2,  # Default
            cuisine=['Pizza'],
            latitude=location.get('latitude', 0.0),
            longitude=location.get('longitude', 0.0)
        )
        
        # Generate AI summary using Gemini with reviews
        summary = gemini_service.generate_restaurant_summary(restaurant, reviews=reviews)
        logger.info(f"Generated summary for restaurant: {restaurant_id}")
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate summary for {restaurant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )

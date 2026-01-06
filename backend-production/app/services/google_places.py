"""
Google Places API service module.

This module provides integration with the Google Places API (New) for
searching pizza restaurants and retrieving location data.
"""

import requests
from typing import List, Dict, Optional, Tuple
from app.config import settings
from app.models import Restaurant
import logging
import math

logger = logging.getLogger(__name__)


class GooglePlacesService:
    """
    Service for interacting with Google Places API (New).
    
    This service provides methods for:
    - Geocoding addresses to coordinates
    - Searching for pizza restaurants
    - Retrieving detailed place information
    - Converting API responses to application models
    
    Attributes:
        BASE_URL (str): Base URL for Google Places API
        api_key (str): Google Places API key
        headers (dict): Default headers for API requests
    """
    
    BASE_URL = "https://places.googleapis.com/v1"
    
    def __init__(self):
        """
        Initialize the Google Places service.
        
        Raises:
            ValueError: If GOOGLE_PLACES_API_KEY is not configured
        """
        if not settings.GOOGLE_PLACES_API_KEY:
            raise ValueError("Google Places API key is required")
        self.api_key = settings.GOOGLE_PLACES_API_KEY
        self.headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key
        }
    
    def get_autocomplete_predictions(self, input_text: str, session_token: Optional[str] = None) -> List[Dict]:
        """
        Get place predictions for a given input text using Places API (New).
        
        Args:
            input_text: The text to search for
            session_token: Optional session token for billing grouping
            
        Returns:
            List of prediction dictionaries
        """
        url = f"{self.BASE_URL}/places:autocomplete"
        
        payload = {
            "input": input_text,
            # Restrict to US for now, or make configurable
            # "locationBias": ... 
        }
        
        if session_token:
            payload["sessionToken"] = session_token
            
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            # Transform response to a simpler format for frontend
            predictions = []
            for suggestion in data.get("suggestions", []):
                place_prediction = suggestion.get("placePrediction", {})
                if place_prediction:
                    predictions.append({
                        "place_id": place_prediction.get("placeId"),
                        "description": place_prediction.get("text", {}).get("text"),
                        "main_text": place_prediction.get("structuredFormat", {}).get("mainText", {}).get("text"),
                        "secondary_text": place_prediction.get("structuredFormat", {}).get("secondaryText", {}).get("text")
                    })
            
            return predictions
            
        except Exception as e:
            print(f"Error fetching autocomplete predictions: {e}")
            return []

    def geocode_address(self, address: str) -> Tuple[float, float]:
        """
        Convert an address to geographic coordinates.
        
        Uses the Google Geocoding API to convert a human-readable address
        into latitude and longitude coordinates.
        
        Args:
            address: The address string to geocode
            
        Returns:
            Tuple[float, float]: (latitude, longitude) coordinates
            
        Raises:
            ValueError: If the address cannot be geocoded
            requests.HTTPError: If the API request fails
        """
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": self.api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') != 'OK' or not data.get('results'):
            raise ValueError(f"Could not geocode address: {address}")
        
        location = data['results'][0]['geometry']['location']
        return location['lat'], location['lng']
    
    def search_pizza_places(
        self, 
        latitude: float, 
        longitude: float,
        radius_miles: float = 10.0,
        min_rating: float = 3.0,
        max_results: int = 20,
        dietary_restrictions: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Search for pizza restaurants near a location.
        
        Uses the Google Places API Text Search to find pizza restaurants
        within a specified radius of the given coordinates.
        
        Args:
            latitude: Latitude of the search center
            longitude: Longitude of the search center
            radius_miles: Search radius in miles (default: 10.0)
            min_rating: Minimum rating filter (default: 3.0)
            max_results: Maximum number of results (default: 20, max: 20)
            dietary_restrictions: List of dietary restrictions (e.g., ["Vegan", "Gluten-Free"])
            
        Returns:
            List[Dict]: List of place dictionaries from the API
            
        Raises:
            requests.HTTPError: If the API request fails
        """
        url = f"{self.BASE_URL}/places:searchText"
        
        # Convert miles to meters for the location bias
        radius_meters = int(radius_miles * 1609.34)
        
        # Construct text query dynamically
        base_query = "pizza restaurant"
        if dietary_restrictions and len(dietary_restrictions) > 0:
            # e.g., "Vegan Gluten-Free pizza restaurant"
            modifiers = " ".join(dietary_restrictions)
            text_query = f"{modifiers} {base_query}"
        else:
            text_query = base_query
        
        # Build request body
        request_body = {
            "textQuery": text_query,
            "locationBias": {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "radius": min(radius_meters, 50000)  # API max is 50km
                }
            },
            "maxResultCount": min(max_results, 20)  # Use maxResultCount instead of pageSize
        }
        
        # Specify fields to return - using Essential SKU for faster responses
        # Added places.types for cuisine identification
        field_mask = ",".join([
            "places.id",
            "places.displayName",
            "places.formattedAddress",
            "places.location",
            "places.rating",
            "places.userRatingCount",
            "places.priceLevel",
            "places.websiteUri",
            "places.nationalPhoneNumber",
            "places.currentOpeningHours",
            "places.photos",
            "places.types"
        ])
        
        headers = {
            **self.headers,
            "X-Goog-FieldMask": field_mask
        }
        
        response = requests.post(url, json=request_body, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        places = data.get('places', [])
        
        # Debug logging to check for photos
        if places:
            has_photos = sum(1 for p in places if 'photos' in p)
            logger.info(f"DEBUG_PHOTOS: Found {len(places)} places. {has_photos} have photos.")
            if has_photos > 0:
                first_with_photo = next(p for p in places if 'photos' in p)
                logger.info(f"DEBUG_PHOTOS: Sample photo data: {first_with_photo.get('photos')[0]['name']}")
            else:
                 logger.info("DEBUG_PHOTOS: No photos found in any results for this search.")
        else:
            logger.info("DEBUG_PHOTOS: No places found in API response")
            
        return places
    
    def get_place_details(self, place_id: str) -> Dict:
        """
        Get detailed information about a specific place.
        
        Retrieves comprehensive details about a restaurant using the
        Google Places API Place Details endpoint.
        
        Args:
            place_id: Google Places ID (may include 'places/' prefix)
            
        Returns:
            Dict: Detailed place information
            
        Raises:
            requests.HTTPError: If the API request fails
        """
        # Ensure place_id is in correct format
        if not place_id.startswith('places/'):
            place_id = f"places/{place_id}"
        
        url = f"{self.BASE_URL}/{place_id}"
        
        # Specify fields to return
        field_mask = ",".join([
            "id",
            "displayName",
            "formattedAddress",
            "location",
            "rating",
            "userRatingCount",
            "priceLevel",
            "websiteUri",
            "nationalPhoneNumber",
            "internationalPhoneNumber",
            "currentOpeningHours",
            "regularOpeningHours",
            "types",
            "editorialSummary",
            "reviews"
        ])
        
        headers = {
            **self.headers,
            "X-Goog-FieldMask": field_mask
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate the great-circle distance between two points.
        
        Uses the Haversine formula to calculate the distance between
        two points on Earth given their latitude and longitude.
        
        Args:
            lat1: Latitude of the first point
            lon1: Longitude of the first point
            lat2: Latitude of the second point
            lon2: Longitude of the second point
            
        Returns:
            float: Distance in miles, rounded to 2 decimal places
        """
        # Earth's radius in miles
        EARTH_RADIUS_MILES = 3959.0
        
        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        distance = EARTH_RADIUS_MILES * c
        return round(distance, 2)
    
    def convert_to_restaurant_model(
        self,
        place: Dict,
        user_lat: float,
        user_lon: float
    ) -> Restaurant:
        """
        Convert Google Places API response to Restaurant model.
        
        Transforms the raw API response dictionary into a structured
        Restaurant model object with all necessary fields populated.
        
        Args:
            place: Raw place dictionary from Google Places API
            user_lat: User's latitude for distance calculation
            user_lon: User's longitude for distance calculation
            
        Returns:
            Restaurant: Populated restaurant model instance
        """
        # Extract location
        location = place.get('location', {})
        place_lat = location.get('latitude', 0)
        place_lng = location.get('longitude', 0)
        
        # Calculate distance
        distance = self.calculate_distance(user_lat, user_lon, place_lat, place_lng)
        
        # Extract display name
        display_name = place.get('displayName', {})
        name = display_name.get('text', 'Unknown') if isinstance(display_name, dict) else str(display_name)
        
        # Determine cuisine types
        cuisine = ['Pizza']
        types = place.get('types', [])
        
        if 'italian_restaurant' in types:
            cuisine.append('Italian')
        if 'vegan_restaurant' in types:
            cuisine.append('Vegan')
        if 'vegetarian_restaurant' in types:
            cuisine.append('Vegetarian')
        
        # Get opening hours
        open_now = None
        current_hours = place.get('currentOpeningHours', {})
        if current_hours:
            open_now = current_hours.get('openNow')
        
        # Extract price level (convert from text to number)
        price_level = 2  # default
        price_level_text = place.get('priceLevel')
        if price_level_text:
            price_map = {
                'PRICE_LEVEL_FREE': 1,
                'PRICE_LEVEL_INEXPENSIVE': 1,
                'PRICE_LEVEL_MODERATE': 2,
                'PRICE_LEVEL_EXPENSIVE': 3,
                'PRICE_LEVEL_VERY_EXPENSIVE': 4
            }
            price_level = price_map.get(price_level_text, 2)
        
        # Extract phone number
        phone = place.get('nationalPhoneNumber') or place.get('internationalPhoneNumber')
        
        # Extract website
        website = place.get('websiteUri')
        
        # Get the place ID (remove 'places/' prefix if present)
        place_id = place.get('id', place.get('name', ''))
        if place_id.startswith('places/'):
            place_id = place_id[7:]  # Remove 'places/' prefix
            
        # Extract photo URL if available
        photo_url = None
        photos = place.get('photos', [])
        if photos and len(photos) > 0:
            photo_name = photos[0].get('name')
            if photo_name:
                # Use our proxy endpoint to avoid exposing API key
                photo_url = f"{settings.BASE_URL}/api/media/{photo_name}"

        return Restaurant(
            id=place_id,
            name=name,
            address=place.get('formattedAddress', 'N/A'),
            distance=distance,
            rating=place.get('rating', 0.0),
            priceLevel=price_level,
            cuisine=cuisine,
            phone=phone,
            website=website,
            openNow=open_now,
            latitude=place_lat,
            longitude=place_lng,
            photoUrl=photo_url
        )


# Singleton instance
_google_places_service_instance = None


def get_google_places_service() -> GooglePlacesService:
    """
    Get or create the GooglePlacesService singleton instance.
    
    Returns:
        GooglePlacesService: The singleton service instance
    """
    global _google_places_service_instance
    if _google_places_service_instance is None:
        _google_places_service_instance = GooglePlacesService()
    return _google_places_service_instance

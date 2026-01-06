from pydantic import BaseModel, Field
from typing import List, Optional


class UserPreferences(BaseModel):
    """User preferences for restaurant search"""
    maxDistance: int = Field(default=10, description="Maximum distance in miles")
    minRating: float = Field(default=3.0, description="Minimum rating")
    dietaryRestrictions: List[str] = Field(default_factory=list)
    favoriteStyles: List[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    """Request model for pizza recommendations"""
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    preferences: Optional[UserPreferences] = None
    offset: int = Field(default=0, description="Offset for pagination (0, 3, 6, 9, 12)")
    sessionId: Optional[str] = None



class AIGeneratedSummary(BaseModel):
    """AI-generated summary for a restaurant"""
    restaurantId: str
    summary: str
    highlights: List[str]
    recommendations: List[str]


class Restaurant(BaseModel):
    """Restaurant model"""
    id: str
    name: str
    address: str
    distance: float
    rating: float
    priceLevel: int = Field(ge=1, le=4)
    cuisine: List[str]
    phone: Optional[str] = None
    website: Optional[str] = None
    openNow: Optional[bool] = None
    latitude: float
    longitude: float
    photoUrl: Optional[str] = None
    aiSummary: Optional[AIGeneratedSummary] = None


class GeocodeRequest(BaseModel):
    """Request model for geocoding"""
    address: str


class GeocodeResponse(BaseModel):
    """Response model for geocoding"""
    latitude: float
    longitude: float


class RecommendationsResponse(BaseModel):
    """Response model for restaurant recommendations"""
    restaurants: List[Restaurant]
    sessionId: str
    totalCount: int
    currentOffset: int

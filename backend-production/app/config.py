import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings and configuration"""
    
    # API Keys
    
    class Config:
        env_file = ".env"

    GOOGLE_PLACES_API_KEY: str = os.getenv("GOOGLE_PLACES_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    
    # API Configuration
    # IMPORTANT: Add your production frontend URL here for CORS
    # Example: "http://your-frontend-s3-bucket.s3-website-us-east-1.amazonaws.com,http://yourdomain.com"
    # For development, include localhost. For production, include your actual frontend domain.
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:4200,http://localhost:3000,https://parlor-mu.vercel.app").split(",")

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Google Places API Configuration
    GOOGLE_PLACES_SEARCH_RADIUS: int = 50000  # meters (about 31 miles)
    
    # Recommendation Settings
    MAX_RECOMMENDATIONS: int = 3
    
    @classmethod
    def validate(cls):
        """Validate that required settings are present"""
        if not cls.GOOGLE_PLACES_API_KEY:
            raise ValueError("GOOGLE_PLACES_API_KEY is required")
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required")


settings = Settings()

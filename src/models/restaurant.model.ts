export interface Restaurant {
  id: string;
  name: string;
  address: string;
  distance: number;
  rating: number;
  priceLevel: number;
  cuisine: string[];
  phone?: string;
  website?: string;
  openNow?: boolean;
  latitude: number;
  longitude: number;
}

export interface UserPreferences {
  maxDistance: number;
  minRating: number;
  dietaryRestrictions: string[];
  favoriteStyles: string[];
}

export interface UserChoice {
  restaurantId: string;
  restaurantName: string;
  cuisine: string[];
  priceLevel: number;
  rating: number;
  timestamp: Date;
}

export interface SearchRequest {
  address: string;
  latitude?: number;
  longitude?: number;
  preferences?: UserPreferences;
  offset?: number;
  sessionId?: string;
}

export interface AIGeneratedSummary {
  restaurantId: string;
  summary: string;
  highlights: string[];
  recommendations: string[];
}

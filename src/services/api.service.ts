import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Restaurant, SearchRequest, AIGeneratedSummary, UserChoice } from '../models/restaurant.model';
import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getPizzaRecommendations(searchRequest: SearchRequest): Observable<Restaurant[]> {
    return this.http.post<Restaurant[]>(`${this.apiUrl}/pizza-recommendations`, searchRequest);
  }

  searchRestaurants(searchRequest: SearchRequest): Observable<Restaurant[]> {
    return this.http.post<Restaurant[]>(`${this.apiUrl}/restaurants/search`, searchRequest);
  }

  getRestaurantDetails(id: string): Observable<Restaurant> {
    return this.http.get<Restaurant>(`${this.apiUrl}/restaurants/${id}`);
  }

  getAISummary(restaurantId: string, preferences?: string[]): Observable<AIGeneratedSummary> {
    let params = new HttpParams();
    if (preferences) {
      params = params.set('preferences', preferences.join(','));
    }
    return this.http.get<AIGeneratedSummary>(
      `${this.apiUrl}/restaurants/${restaurantId}/summary`,
      { params }
    );
  }

  geocodeAddress(address: string): Observable<{ latitude: number; longitude: number }> {
    return this.http.post<{ latitude: number; longitude: number }>(
      `${this.apiUrl}/geocode`,
      { address }
    );
  }

  recordUserChoice(choice: UserChoice): Observable<void> {
    return this.http.post<void>(`${this.apiUrl}/user/choices`, choice);
  }

  getUserPreferences(): Observable<{ dietaryRestrictions: string[]; favoriteStyles: string[] }> {
    return this.http.get<{ dietaryRestrictions: string[]; favoriteStyles: string[] }>(
      `${this.apiUrl}/user/preferences`
    );
  }
}

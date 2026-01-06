import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Restaurant, AIGeneratedSummary, SearchRequest } from '../../models/restaurant.model';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './results.component.html',
  styleUrls: ['./results.component.css']
})
export class ResultsComponent implements OnChanges {
  @Input() restaurants: Restaurant[] = [];
  @Input() lastSearchRequest: SearchRequest | null = null;
  @Output() onReroll = new EventEmitter<SearchRequest>();
  
  selectedRestaurant: Restaurant | null = null;
  aiSummary: AIGeneratedSummary | null = null;
  loadingSummary: boolean = false;
  loading: boolean = false;

  constructor(private apiService: ApiService) {}

  ngOnChanges(changes: SimpleChanges) {
    if (changes['restaurants'] && this.restaurants && this.restaurants.length > 0) {
      // Logic moved to main.ts to support loading overlay
    }
  }

  preloadSummaries() {
    console.log('🔄 Preloading AI summaries in background...');
    this.restaurants.forEach(restaurant => {
      if (!restaurant.aiSummary) {
        this.apiService.getAISummary(restaurant.id).subscribe({
          next: (summary) => {
            console.log(`✅ Summary loaded for ${restaurant.name}`);
            restaurant.aiSummary = summary;
          },
          error: (error) => {
            console.error(`❌ Error loading summary for ${restaurant.name}:`, error);
          }
        });
      }
    });
  }

  selectRestaurant(restaurant: Restaurant) {
    this.selectedRestaurant = restaurant;
    
    // Use pre-generated summary if available
    if (restaurant.aiSummary) {
      this.aiSummary = restaurant.aiSummary;
      this.loadingSummary = false;
    } else {
      this.loadAISummary(restaurant.id);
    }
  }

  closeDetails() {
    this.selectedRestaurant = null;
    this.aiSummary = null;
  }

  loadAISummary(restaurantId: string) {
    this.loadingSummary = true;
    this.aiSummary = null;

    this.apiService.getAISummary(restaurantId).subscribe({
      next: (summary) => {
        this.aiSummary = summary;
        this.loadingSummary = false;
      },
      error: (error) => {
        console.error('Error loading AI summary:', error);
        this.loadingSummary = false;
      }
    });
  }

  getPriceSymbol(priceLevel: number): string {
    return '$'.repeat(priceLevel);
  }

  getStars(rating: number): string {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    let stars = '⭐'.repeat(fullStars);
    if (hasHalfStar) stars += '✨';
    return stars;
  }

  rerollRecommendations() {
    if (this.lastSearchRequest && !this.loading) {
      this.loading = true;
      this.onReroll.emit(this.lastSearchRequest);
      // Reset loading after a delay (will be set by parent component)
      setTimeout(() => this.loading = false, 2000);
    }
  }
}

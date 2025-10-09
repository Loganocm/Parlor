import { Component } from '@angular/core';
import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { SearchComponent } from './components/search/search.component';
import { ResultsComponent } from './components/results/results.component';
import { Restaurant, SearchRequest } from './models/restaurant.model';
import { ApiService } from './services/api.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, SearchComponent, ResultsComponent],
  template: `
    <div class="app-container">
      <app-search (onSearch)="handleSearch($event)"></app-search>
      <app-results [restaurants]="restaurants"></app-results>
    </div>
  `,
  styles: [`
    .app-container {
      min-height: 100vh;
      background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
  `]
})
export class App {
  restaurants: Restaurant[] = [];

  constructor(private apiService: ApiService) {}

  handleSearch(searchRequest: SearchRequest) {
    this.apiService.searchRestaurants(searchRequest).subscribe({
      next: (results) => {
        this.restaurants = results;
      },
      error: (error) => {
        console.error('Error fetching restaurants:', error);
        this.restaurants = [];
      }
    });
  }
}

bootstrapApplication(App, {
  providers: [provideHttpClient()]
});

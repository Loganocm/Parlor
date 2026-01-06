import { Component } from '@angular/core';
import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { SearchComponent } from './components/search/search.component';
import { ResultsComponent } from './components/results/results.component';
import { Restaurant, SearchRequest, AIGeneratedSummary } from './models/restaurant.model';
import { ApiService } from './services/api.service';
import { environment } from './environments/environment';
import { forkJoin, of, Observable } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, SearchComponent, ResultsComponent],
  template: `
    <!-- Landing Page -->
    <div class="landing-container" *ngIf="!started">
      <div class="landing-content">
        <h1>🍕 Parlor</h1>
        <p>Find your next pizza adventure with AI-powered summaries!</p>
        <button (click)="started = true" class="start-btn">Start</button>
      </div>
    </div>

    <!-- Main App -->
    <div class="app-container" *ngIf="started">
      <app-search (onSearch)="handleSearch($event)"></app-search>
      
      <div class="loading-overlay" *ngIf="loading">
        <div class="loading-spinner">
          <div class="pizza-spinner">🍕</div>
          <p class="loading-text">{{ loadingMessage }}</p>
        </div>
      </div>

      <app-results 
        [restaurants]="restaurants"
        [lastSearchRequest]="lastSearchRequest"
        (onReroll)="handleSearch($event)">
      </app-results>
    </div>
  `,
  styles: [`
    /* Landing Page Styles */
    .landing-container {
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
      color: white;
      text-align: center;
    }

    .landing-content h1 {
      font-size: 4rem;
      margin-bottom: 0.5rem;
      text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }

    .landing-content p {
      font-size: 1.5rem;
      margin-bottom: 2rem;
      opacity: 0.9;
    }

    .start-btn {
      padding: 1rem 3rem;
      font-size: 1.5rem;
      border: none;
      border-radius: 50px;
      background: white;
      color: #FF6B6B;
      font-weight: bold;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
    }

    .start-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    .app-container {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    .loading-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.7);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 9999;
      animation: fadeIn 0.3s ease-in;
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    .loading-spinner {
      text-align: center;
      background: white;
      padding: 40px 60px;
      border-radius: 20px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    }

    .pizza-spinner {
      font-size: 80px;
      animation: spin 1s linear infinite;
      display: inline-block;
    }

    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }

    .loading-text {
      margin-top: 20px;
      font-size: 18px;
      color: #333;
      font-weight: 600;
      animation: pulse 1.5s ease-in-out infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
  `]
})
export class App {
  started: boolean = false;
  restaurants: Restaurant[] = [];
  lastSearchRequest: SearchRequest | null = null;
  loading: boolean = false;
  loadingMessage: string = 'Finding the perfect pizza spots...';

  constructor(private apiService: ApiService) {
    this.loadGoogleMaps();
  }

  loadGoogleMaps() {
    if ((window as any).googleMapsLoaded) return;

    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${environment.googleMapsApiKey}&libraries=places&loading=async&callback=initGoogleMaps`;
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
  }

  handleSearch(searchRequest: SearchRequest) {
    this.lastSearchRequest = searchRequest;
    this.loading = true;
    this.loadingMessage = 'Finding the perfect pizza spots...';
    this.restaurants = []; // Clear previous results
    
    // Animate messages while searching
    const messageInterval = this.startMessageCycle();
    
    this.apiService.getPizzaRecommendations(searchRequest).subscribe({
      next: (results: Restaurant[]) => {
        // Recommendations found, now fetch metadata
        this.loadingMessage = 'Gathering photos and getting AI summaries...';
        
        const tasks: Observable<any>[] = [];

        // 1. Fetch AI Summaries
        const summaryTasks = results.map(r => 
          this.apiService.getAISummary(r.id).pipe(
            map(summary => {
              r.aiSummary = summary;
              return summary;
            }),
            catchError(err => of(null)) // Continue even if summary fails
          )
        );
        tasks.push(...summaryTasks);

        // 2. Preload Images
        const imageTasks = results.map(r => 
          new Observable<boolean>(observer => {
            if (!r.photoUrl) {
              observer.next(true);
              observer.complete();
              return;
            }
            const img = new Image();
            img.onload = () => {
              console.log(`✅ Image loaded for ${r.name}`);
              observer.next(true);
              observer.complete();
            };
            img.onerror = () => {
              console.warn(`❌ Failed to load image for ${r.name}`);
              observer.next(false);
              observer.complete();
            };
            img.src = r.photoUrl;
          })
        );
        tasks.push(...imageTasks);
        
        this.loadingMessage = 'Finalizing your personalized menu...';

        console.log(`⏳ Waiting for ${tasks.length} tasks to complete...`);

        // Wait for ALL tasks (summaries + images) to complete
        forkJoin(tasks).subscribe({
            next: () => {
                console.log('✅ All data and media loaded!');
                clearInterval(messageInterval);
                this.loadingMessage = 'Almost ready...';
                
                // Final delay to ensure smooth transition
                setTimeout(() => {
                    this.restaurants = results;
                    this.loading = false;
                }, 1500); 
            }
        });
      },
      error: (error: any) => {
        clearInterval(messageInterval);
        console.error('Error fetching restaurants:', error);
        alert('Error: ' + (error.error?.detail || 'Unable to fetch recommendations. Please try again.'));
        this.restaurants = [];
        this.loading = false;
      }
    });
  }

  private startMessageCycle(): any {
    const messages = [
      "Finding the perfect pizza spots...",
      "Analyzing recent reviews...",
      "Comparing crust thickness...",
      "Measuring cheese stretch..."
    ];
    let index = 0;
    
    return setInterval(() => {
        index = (index + 1) % messages.length;
        // Only update if we are still in the finding phase
        if (this.loadingMessage !== 'Gathering photos and getting AI summaries...' && 
            this.loadingMessage !== 'Finalizing your personalized menu...' &&
            this.loadingMessage !== 'Almost ready...') {
             this.loadingMessage = messages[index];
        }
    }, 1500);
  }
}

bootstrapApplication(App, {
  providers: [provideHttpClient()]
});


import { Component, EventEmitter, Output, ViewChild, ElementRef, AfterViewInit, CUSTOM_ELEMENTS_SCHEMA, NgZone, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { ApiService } from '../../services/api.service';
import { LocationService } from '../../services/location.service';
import { SearchRequest, UserPreferences } from '../../models/restaurant.model';

declare var google: any;

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [CommonModule, FormsModule],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.css']
})
export class SearchComponent implements AfterViewInit, OnInit, OnDestroy {
  @Output() onSearch = new EventEmitter<SearchRequest>();
  @ViewChild('placeInput') placeInput!: ElementRef;

  address: string = '';
  loading: boolean = false;
  showDietaryDropdown: boolean = false;
  predictions: any[] = [];
  showPredictions: boolean = false;
  activePredictionIndex: number = -1;
  errorMessage: string = '';
  
  private selectedPlace: any = null;
  private autocompleteService: any = null;
  private placesService: any = null;
  private sessionToken: any = null;
  private searchSubject = new Subject<string>();
  private searchSubscription!: Subscription;

  preferences: UserPreferences = {
    maxDistance: 10,
    minRating: 3.0,
    dietaryRestrictions: [],
    favoriteStyles: []
  };

  availableDietaryRestrictions = ['Vegetarian', 'Vegan', 'Gluten-Free', 'Dairy-Free'];

  get selectedDietaryCount(): number {
    return this.preferences.dietaryRestrictions.length;
  }

  validateDistance(event: any) {
    if (event) {
      event.target.blur(); // Remove focus when Enter is pressed
    }
    
    // Clamp the value between 1 and 50
    let dist = this.preferences.maxDistance;
    if (!dist || dist < 1) dist = 1;
    if (dist > 50) dist = 50;
    
    this.preferences.maxDistance = dist;
    console.log('✅ Distance validated and set to:', dist);
  }

  constructor(
    private apiService: ApiService,
    private locationService: LocationService,
    private ngZone: NgZone
  ) {}

  ngOnInit() {
    this.searchSubscription = this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged()
    ).subscribe(query => {
      this.fetchPredictions(query);
    });

    // Global handler for Google Maps authentication failures
    (window as any).gm_authFailure = () => {
      console.error('🔥 Google Maps Auth Failure Detected');
      this.ngZone.run(() => {
        this.errorMessage = 'Error: Enable "Places API" (Legacy) in Google Cloud Console. You likely only have "Places API (New)" enabled.';
        this.showPredictions = true;
      });
    };
  }

  ngOnDestroy() {
    if (this.searchSubscription) {
      this.searchSubscription.unsubscribe();
    }
  }

  ngAfterViewInit() {
    // No longer needed for backend proxy
  }

  // Removed waitForGoogleMaps and initAutocompleteService

  onInputChange() {
    console.log('📝 Input changed:', this.address);
    this.searchSubject.next(this.address);
  }

  onKeydown(event: KeyboardEvent) {
    if (!this.showPredictions || this.predictions.length === 0) return;

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      this.activePredictionIndex = (this.activePredictionIndex + 1) % this.predictions.length;
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      this.activePredictionIndex = (this.activePredictionIndex - 1 + this.predictions.length) % this.predictions.length;
    } else if (event.key === 'Enter') {
      event.preventDefault();
      if (this.activePredictionIndex >= 0) {
        this.selectPrediction(this.predictions[this.activePredictionIndex]);
      }
    } else if (event.key === 'Escape') {
      this.showPredictions = false;
    }
  }

  fetchPredictions(query: string) {
    this.errorMessage = ''; 

    if (!query || query.length < 3) {
      this.predictions = [];
      this.showPredictions = false;
      return;
    }

    console.log('📤 Fetching predictions via Backend Proxy for:', query);
    
    this.apiService.getAutocompletePredictions(query, this.sessionToken).subscribe({
      next: (predictions) => {
        this.ngZone.run(() => {
          console.log('✅ Predictions received:', predictions.length);
          this.predictions = predictions;
          this.showPredictions = predictions.length > 0;
          this.activePredictionIndex = -1;
        });
      },
      error: (err) => {
        console.error('❌ Backend Autocomplete Error:', err);
        this.ngZone.run(() => {
           // Don't show error to user for autocomplete failures, just hide dropdown
           this.predictions = [];
        });
      }
    });
  }

  selectPrediction(prediction: any) {
    this.address = prediction.description;
    this.showPredictions = false;
    
    console.log('📍 Fetching details for:', prediction.place_id);
    
    this.apiService.getGooglePlaceDetails(prediction.place_id).subscribe({
      next: (place) => {
         this.ngZone.run(() => {
           this.handlePlaceSelection(place);
           this.sessionToken = crypto.randomUUID();
         });
      },
      error: (err) => {
         console.error('❌ Place Details Error:', err);
         alert('Failed to get location details.');
      }
    });
  }

  closePredictions() {
    setTimeout(() => {
      this.showPredictions = false;
    }, 200);
  }

  handlePlaceSelection(place: any) {
    console.log('💾 Updating component state...');
    this.selectedPlace = place;
    
    // Handle Google Places API (New) response format
    // It returns { location: { latitude: 123, longitude: 456 }, formattedAddress: "..." }
    const lat = place.location?.latitude;
    const lng = place.location?.longitude;
    const address = place.formattedAddress;

    console.log('✅ Place selected:', address);
    console.log('📍 Location:', lat, lng);
    
    if (lat && lng) {
      console.log('🚀 AUTO-TRIGGERING SEARCH with coordinates:', lat, lng);
      this.loading = true;
      
      const searchRequest: SearchRequest = {
        address: address || this.address,
        latitude: lat,
        longitude: lng,
        preferences: this.preferences
      };
      
      this.performSearch(searchRequest);
    } else {
      console.error('❌ Missing location data in place details:', place);
      alert('Could not retrieve location coordinates for this place.');
    }
  }

  // Helper method to get the current input value
  getInputValue(): string {
    return this.address;
  }

  useCurrentLocation() {
    console.log('🔍 Getting current location...');
    this.loading = true;
    this.locationService.getCurrentPosition().subscribe({
      next: (position) => {
        console.log('✅ Location received:', position.coords.latitude, position.coords.longitude);
        const searchRequest: SearchRequest = {
          address: 'Current Location',
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          preferences: this.preferences
        };
        console.log('📤 Sending search request:', searchRequest);
        this.performSearch(searchRequest);
      },
      error: (error) => {
        console.error('❌ Error getting location:', error);
        
        let msg = 'Unable to get your location. Please enter an address manually.';
        if (error.code === 1) {
          msg = 'Location permission denied. Please allow access in browser settings.';
        } else if (error.code === 2) {
          msg = 'Location unavailable. Ensure GPS is on and try again.';
        } else if (error.code === 3) {
           msg = 'Location request timed out. Please try again.';
        }

        alert(msg);
        this.loading = false;
      }
    });
  }

  searchByAddress() {
    console.log('🔍 Manual search triggered');
    
    // PlaceAutocompleteElement does NOT expose typed input
    // User must select a place from the autocomplete dropdown
    // which will populate this.selectedPlace and this.address
    
    if (!this.address || !this.address.trim()) {
      console.error('❌ No address selected');
      alert('Please select an address from the autocomplete suggestions');
      return;
    }

    this.loading = true;

    // If user selected from autocomplete, use those coordinates
    if (this.selectedPlace && this.selectedPlace.location) {
      // Check if lat/lng are methods or properties
      const lat = typeof this.selectedPlace.location.lat === 'function' ? this.selectedPlace.location.lat() : this.selectedPlace.location.lat;
      const lng = typeof this.selectedPlace.location.lng === 'function' ? this.selectedPlace.location.lng() : this.selectedPlace.location.lng;
      console.log('✅ Using autocomplete coordinates:', lat, lng);
      
      const searchRequest: SearchRequest = {
        address: this.address,
        latitude: lat,
        longitude: lng,
        preferences: this.preferences
      };
      console.log('📤 Sending search request:', searchRequest);
      this.performSearch(searchRequest);
      return;
    }

    // This shouldn't happen since address is only set via autocomplete selection
    console.log('🔍 Geocoding address:', this.address);
    this.apiService.geocodeAddress(this.address).subscribe({
      next: (coords) => {
        console.log('✅ Geocoded to:', coords);
        const searchRequest: SearchRequest = {
          address: this.address,
          latitude: coords.latitude,
          longitude: coords.longitude,
          preferences: this.preferences
        };
        console.log('📤 Sending search request:', searchRequest);
        this.performSearch(searchRequest);
      },
      error: (error) => {
        console.error('❌ Geocoding error:', error);
        alert('Unable to find location. Please check your address.');
        this.loading = false;
      }
    });
  }


  toggleDietaryDropdown() {
    this.showDietaryDropdown = !this.showDietaryDropdown;
  }

  toggleDietaryRestriction(restriction: string) {
    const index = this.preferences.dietaryRestrictions.indexOf(restriction);
    if (index > -1) {
      this.preferences.dietaryRestrictions.splice(index, 1);
    } else {
      this.preferences.dietaryRestrictions.push(restriction);
    }
  }

  isDietaryRestrictionSelected(restriction: string): boolean {
    return this.preferences.dietaryRestrictions.includes(restriction);
  }

  private updateLoadingMessage() {
    // Message handling moved to main.ts for better coordination with API states
  }

  private performSearch(searchRequest: SearchRequest) {
    // Start the message cycle
    this.updateLoadingMessage();
    
    // We don't set this.loading = false here because the parent component handles the actual API call
    // and sets its own loading state.
    // However, looking at previous code, this component just emits onSearch.
    
    this.onSearch.emit(searchRequest);
    
    // IMPORTANT: Reset loading state locally after a short delay so the user can search again if needed.
    // In a real app, the parent should tell us when the search is done.
    // But for now, we unlock the input after 1 second so the user isn't stuck.
    setTimeout(() => {
        this.loading = false;
    }, 1000);
  }
}

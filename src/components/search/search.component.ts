import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { LocationService } from '../../services/location.service';
import { SearchRequest, UserPreferences } from '../../models/restaurant.model';

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.css']
})
export class SearchComponent {
  @Output() onSearch = new EventEmitter<SearchRequest>();

  address: string = '';
  loading: boolean = false;
  showDietaryDropdown: boolean = false;

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

  constructor(
    private apiService: ApiService,
    private locationService: LocationService
  ) {}

  useCurrentLocation() {
    this.loading = true;
    this.locationService.getCurrentPosition().subscribe({
      next: (position) => {
        const searchRequest: SearchRequest = {
          address: 'Current Location',
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          preferences: this.preferences
        };
        this.performSearch(searchRequest);
      },
      error: (error) => {
        console.error('Error getting location:', error);
        alert('Unable to get your location. Please enter an address manually.');
        this.loading = false;
      }
    });
  }

  searchByAddress() {
    if (!this.address.trim()) {
      alert('Please enter an address');
      return;
    }

    this.loading = true;
    this.apiService.geocodeAddress(this.address).subscribe({
      next: (coords) => {
        const searchRequest: SearchRequest = {
          address: this.address,
          latitude: coords.latitude,
          longitude: coords.longitude,
          preferences: this.preferences
        };
        this.performSearch(searchRequest);
      },
      error: (error) => {
        console.error('Geocoding error:', error);
        alert('Unable to find location. Please check your address.');
        this.loading = false;
      }
    });
  }

  private performSearch(searchRequest: SearchRequest) {
    this.loading = false;
    this.onSearch.emit(searchRequest);
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
}

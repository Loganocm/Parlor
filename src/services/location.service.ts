import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class LocationService {
  getCurrentPosition(): Observable<GeolocationPosition> {
    return new Observable((observer) => {
      if (!navigator.geolocation) {
        observer.error(new Error('Geolocation is not supported by this browser.'));
        return;
      }

      // Options for low accuracy (GPS off or weak signal) - faster and more reliable indoors
      const lowAccuracyOptions = {
        enableHighAccuracy: false,
        timeout: 10000,
        maximumAge: 0
      };

      console.log('📍 Requesting location (Low Accuracy Mode)...');

      navigator.geolocation.getCurrentPosition(
        (position) => {
          console.log('✅ Location received');
          observer.next(position);
          observer.complete();
        },
        (error) => {
          console.error('❌ Location request failed:', error.message);
          observer.error(error);
        },
        lowAccuracyOptions
      );
    });
  }
}

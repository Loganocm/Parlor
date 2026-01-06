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

      // Options for high accuracy attempt
      const highAccuracyOptions = {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 0
      };

      // Options for low accuracy fallback (GPS off or weak signal)
      const lowAccuracyOptions = {
        enableHighAccuracy: false,
        timeout: 10000,
        maximumAge: 0
      };

      console.log('📍 Requesting high-accuracy location...');

      // 1. Try High Accuracy first
      navigator.geolocation.getCurrentPosition(
        (position) => {
          console.log('✅ High accuracy location received');
          observer.next(position);
          observer.complete();
        },
        (error) => {
          // If permission denied, fail immediately (don't retry)
          if (error.code === 1) { // PERMISSION_DENIED
             console.error('❌ Location permission denied');
             observer.error(error);
             return;
          }

          console.warn('⚠️ High accuracy failed (timeout/unavailable). Falling back to low accuracy...', error.message);

          // 2. Fallback to Low Accuracy (Wifi/Cellular/IP)
          navigator.geolocation.getCurrentPosition(
            (position) => {
              console.log('✅ Low accuracy location received');
              observer.next(position);
              observer.complete();
            },
            (fallbackError) => {
              console.error('❌ Low accuracy location also failed:', fallbackError.message);
              observer.error(fallbackError);
            },
            lowAccuracyOptions
          );
        },
        highAccuracyOptions
      );
    });
  }
}

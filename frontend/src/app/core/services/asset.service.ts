import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AssetProperties {
  cluster: false;
  id: number;
  name: string;
  category: string;
  category_display: string;
  status: string;
  status_display: string;
  created_at: string;
}

export interface ClusterProperties {
  cluster: true;
  count: number;
  categories: string[];
}

export interface AssetFeature {
  type: 'Feature';
  geometry: { type: 'Point'; coordinates: [number, number] };
  properties: AssetProperties | ClusterProperties;
}

export interface FeatureCollection {
  type: 'FeatureCollection';
  features: AssetFeature[];
}

export interface AssetFilters {
  zoom?: number;
  category?: string;
  bbox?: string;
  lat?: number;
  lng?: number;
  radius?: number;
  polygon?: string;
}

@Injectable({ providedIn: 'root' })
export class AssetService {
  private readonly apiUrl = 'http://localhost:8000/api/assets/';
  private http = inject(HttpClient);

  getAll(filters: AssetFilters = {}): Observable<FeatureCollection> {
    let params = new HttpParams();
    if (filters.zoom != null)     params = params.set('zoom', filters.zoom);
    if (filters.category)         params = params.set('category', filters.category);
    if (filters.bbox)             params = params.set('bbox', filters.bbox);
    if (filters.lat != null)      params = params.set('lat', filters.lat);
    if (filters.lng != null)      params = params.set('lng', filters.lng);
    if (filters.radius != null)   params = params.set('radius', filters.radius);
    if (filters.polygon)          params = params.set('polygon', filters.polygon);
    return this.http.get<FeatureCollection>(this.apiUrl, { params });
  }
}

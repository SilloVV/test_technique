import { Component, AfterViewInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import * as L from 'leaflet';

import {
  AssetService,
  AssetFeature,
  AssetProperties,
  ClusterProperties,
} from '../../core/services/asset.service';

const NANCY: L.LatLngTuple = [48.6921, 6.1844];

const CATEGORY_COLORS: Record<string, string> = {
  BOUCHE:  '#ef4444',
  ARMOIRE: '#3b82f6',
  PANNEAU: '#f59e0b',
  REGARD:  '#22c55e',
  AUTRE:   '#8b5cf6',
};

const CATEGORY_LABELS: Record<string, string> = {
  BOUCHE:  'Bouche incendie',
  ARMOIRE: 'Armoire technique',
  PANNEAU: 'Panneau',
  REGARD:  'Regard',
  AUTRE:   'Autre équipement',
};

function dotIcon(color: string, size = 14): L.DivIcon {
  return L.divIcon({
    className: '',
    html: `<div style="background:${color};width:${size}px;height:${size}px;border-radius:50%;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4)"></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -(size / 2 + 2)],
  });
}

function clusterIcon(count: number): L.DivIcon {
  const size = count < 10 ? 34 : count < 100 ? 40 : 48;
  return L.divIcon({
    className: '',
    html: `<div style="background:#1e40af;color:#fff;width:${size}px;height:${size}px;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.3);display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700">${count}</div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

@Component({
  selector: 'app-asset-map',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './asset-map.component.html',
  styleUrl: './asset-map.component.scss',
})
export class AssetMapComponent implements AfterViewInit, OnDestroy {
  private assetService = inject(AssetService);

  totalAssets = 0;
  loading = true;
  error = false;

  private map!: L.Map;
  private markersLayer = L.layerGroup();

  get legendEntries() {
    return Object.entries(CATEGORY_COLORS).map(([key, color]) => ({
      key, color, label: CATEGORY_LABELS[key],
    }));
  }

  ngAfterViewInit(): void {
    this.initMap();
    this.loadAssets();
  }

  ngOnDestroy(): void {
    this.map?.remove();
  }

  private initMap(): void {
    this.map = L.map('asset-map', { zoomControl: true }).setView(NANCY, 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(this.map);

    this.markersLayer.addTo(this.map);

    // Recharge les données à chaque fin de mouvement de carte
    this.map.on('moveend zoomend', () => this.loadAssets());
  }

  private loadAssets(): void {
    const zoom = this.map.getZoom();
    const bounds = this.map.getBounds();
    const bbox = [
      bounds.getWest(), bounds.getSouth(),
      bounds.getEast(), bounds.getNorth(),
    ].join(',');

    this.assetService.getAll({ zoom, bbox }).subscribe({
      next: (fc) => {
        this.markersLayer.clearLayers();
        this.totalAssets = fc.features.filter(
          f => !(f.properties as ClusterProperties).cluster
        ).length;
        fc.features.forEach(f => this.addFeature(f));
        this.loading = false;
        this.error = false;
      },
      error: () => {
        this.loading = false;
        this.error = true;
      },
    });
  }

  private addFeature(feature: AssetFeature): void {
    const [lng, lat] = feature.geometry.coordinates;
    const props = feature.properties;

    if ((props as ClusterProperties).cluster) {
      const cp = props as ClusterProperties;
      L.marker([lat, lng], { icon: clusterIcon(cp.count) })
        .addTo(this.markersLayer)
        .on('click', () => this.map.setView([lat, lng], this.map.getZoom() + 2));
    } else {
      const ap = props as AssetProperties;
      const color = CATEGORY_COLORS[ap.category] ?? '#6b7280';
      L.marker([lat, lng], { icon: dotIcon(color) })
        .addTo(this.markersLayer)
        .bindPopup(`
          <div class="asset-popup">
            <strong>${ap.name}</strong>
            <span>${ap.category_display}</span>
            <span class="status">${ap.status_display}</span>
            <small>${new Date(ap.created_at).toLocaleDateString('fr-FR')}</small>
          </div>
        `, { maxWidth: 220 });
    }
  }
}

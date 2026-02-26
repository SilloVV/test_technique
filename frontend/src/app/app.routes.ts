import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'carte', pathMatch: 'full' },
  {
    path: 'carte',
    loadComponent: () =>
      import('./pages/asset-map/asset-map.component').then(m => m.AssetMapComponent),
  },
];

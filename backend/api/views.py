from django.db import connection
from django.contrib.gis.geos import Point, GEOSGeometry, Polygon
from django.contrib.gis.measure import D
from rest_framework import viewsets
from rest_framework.response import Response

from .models import Asset
from .serializers import AssetSerializer

# Niveau de zoom à partir duquel on affiche les points individuels.
# En dessous de ce seuil, les points sont regroupés en clusters.
# Zoom 15 correspond à une échelle ~(niveau rue).
CLUSTER_ZOOM_THRESHOLD = 15

# Epsilon de clustering par niveau de zoom, exprimé en degrés (SRID 4326).
# Représente le rayon maximum dans lequel deux points sont fusionnés en cluster.
# La valeur est divisée par deux à chaque niveau de zoom supplémentaire,
# ce qui suit la logique des tuiles cartographiques (chaque zoom double la résolution).
# Exemples : zoom 10 ≈ 670 m, zoom 12 ≈ 165 m, zoom 14 ≈ 45 m.
ZOOM_EPS: dict[int, float] = {
    10: 0.006,
    11: 0.003,
    12: 0.0015,
    13: 0.0008,
    14: 0.0004,
}

# Dictionnaires de correspondance code → libellé, construits depuis les TextChoices du modèle.
# Utilisés dans _cluster() pour enrichir les features sans faire de requête ORM supplémentaire.
CATEGORY_DISPLAY = dict(
    Asset.Category.choices
)  # ex: {'BOUCHE': 'Bouche incendie', ...}
STATUS_DISPLAY = dict(Asset.Status.choices)  # ex: {'OP': 'Opérationnel', ...}


def zoom_to_eps(zoom: int) -> float:
    return ZOOM_EPS.get(zoom, 0.0002)


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all().order_by("-created_at")
    serializer_class = AssetSerializer

    def list(self, request, *args, **kwargs):
        zoom = int(request.query_params.get("zoom", 13))
        qs = self._apply_filters(request)

        if zoom >= CLUSTER_ZOOM_THRESHOLD:
            features = [self._to_feature(a) for a in qs.iterator()]
        else:
            features = self._cluster(qs, zoom)

        return Response({"type": "FeatureCollection", "features": features})

    # ------------------------------------------------------------------ #
    # Filtres                                                              #
    # ------------------------------------------------------------------ #

    def _apply_filters(self, request):
        qs = Asset.objects.all()

        # ?category=BOUCHE,REGARD
        category = request.query_params.get("category")
        if category:
            cats = [c.strip() for c in category.split(",") if c.strip()]
            if cats:
                qs = qs.filter(category__in=cats)

        # ?bbox=minlng,minlat,maxlng,maxlat
        bbox = request.query_params.get("bbox")
        if bbox:
            try:
                minlng, minlat, maxlng, maxlat = map(float, bbox.split(","))
                viewport = Polygon.from_bbox((minlng, minlat, maxlng, maxlat))
                viewport.srid = 4326
                qs = qs.filter(location__within=viewport)
            except Exception:
                pass

        # ?lat=48.69&lng=6.18&radius=500  (radius en mètres)
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        radius = request.query_params.get("radius")
        if lat and lng and radius:
            try:
                center = Point(float(lng), float(lat), srid=4326)
                qs = qs.filter(location__dwithin=(center, D(m=float(radius))))
            except Exception:
                pass

        # ?polygon={"type":"Polygon","coordinates":[...]}  (GeoJSON depuis Leaflet Draw)
        polygon = request.query_params.get("polygon")
        if polygon:
            try:
                poly = GEOSGeometry(polygon, srid=4326)
                qs = qs.filter(location__within=poly)
            except Exception:
                pass

        return qs

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _to_feature(self, asset: Asset) -> dict:
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [asset.location.x, asset.location.y],
            },
            "properties": {
                "cluster": False,
                "id": asset.id,
                "name": asset.name,
                "category": asset.category,
                "category_display": asset.get_category_display(),
                "status": asset.status,
                "status_display": asset.get_status_display(),
                "created_at": asset.created_at.isoformat(),
            },
        }

    def _cluster(self, qs, zoom: int) -> list:
        asset_ids = list(qs.values_list("id", flat=True))
        if not asset_ids:
            return []

        eps = zoom_to_eps(zoom)
        table = Asset._meta.db_table

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    ST_ClusterDBSCAN(location::geometry, eps := %s, minpoints := 1) OVER () AS cid,
                    id,
                    ST_X(location::geometry) AS lng,
                    ST_Y(location::geometry) AS lat,
                    name, category, status
                FROM {table}
                WHERE id = ANY(%s)
            """,
                [eps, asset_ids],
            )
            rows = cursor.fetchall()

        clusters: dict = {}
        for cid, aid, lng, lat, name, category, status_val in rows:
            if cid not in clusters:
                clusters[cid] = {"points": [], "items": []}
            clusters[cid]["points"].append((lat, lng))
            clusters[cid]["items"].append(
                {"id": aid, "name": name, "category": category, "status": status_val}
            )

        features = []
        for data in clusters.values():
            n = len(data["items"])
            avg_lat = sum(p[0] for p in data["points"]) / n
            avg_lng = sum(p[1] for p in data["points"]) / n
            geom = {"type": "Point", "coordinates": [avg_lng, avg_lat]}

            if n == 1:
                item = data["items"][0]
                features.append(
                    {
                        "type": "Feature",
                        "geometry": geom,
                        "properties": {
                            "cluster": False,
                            "id": item["id"],
                            "name": item["name"],
                            "category": item["category"],
                            "category_display": CATEGORY_DISPLAY.get(
                                item["category"], ""
                            ),
                            "status": item["status"],
                            "status_display": STATUS_DISPLAY.get(item["status"], ""),
                        },
                    }
                )
            else:
                features.append(
                    {
                        "type": "Feature",
                        "geometry": geom,
                        "properties": {
                            "cluster": True,
                            "count": n,
                            "categories": list({i["category"] for i in data["items"]}),
                        },
                    }
                )

        return features

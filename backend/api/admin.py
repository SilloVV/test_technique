from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin

from .models import Asset


@admin.register(Asset)
class AssetAdmin(LeafletGeoAdmin):
    list_display = ("name", "category", "status", "created_at")
    list_filter = ("category", "status")
    search_fields = ("name",)

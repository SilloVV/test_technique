from rest_framework import serializers
from rest_framework_gis.fields import GeometryField
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Asset


class AssetSerializer(serializers.ModelSerializer):
    location = GeometryField()
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "name",
            "category",
            "category_display",
            "status",
            "status_display",
            "location",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                e.message_dict if hasattr(e, "message_dict") else {"detail": e.messages}
            )

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.contrib.gis.measure import D


class Asset(models.Model):
    # Définition des catégories
    class Category(models.TextChoices):
        BOUCHE_INCENDIE = "BOUCHE", "Bouche incendie"
        ARMOIRE_TECHNIQUE = "ARMOIRE", "Armoire technique"
        PANNEAU = "PANNEAU", "Panneau"
        REGARD = "REGARD", "Regard"
        AUTRE = "AUTRE", "Autre équipement"

    # Définition des Statuts
    class Status(models.TextChoices):
        OPERATIONAL = "OP", "Opérationnel"
        TO_CHECK = "CH", "À vérifier"
        OUT_OF_SERVICE = "OS", "Hors service"

    name = models.CharField(max_length=150, unique=True, verbose_name="Nom de l'actif")

    # Categories
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.AUTRE
    )

    # Statuts
    status = models.CharField(
        max_length=2, choices=Status.choices, default=Status.OPERATIONAL
    )

    # en Geography pour la précision des 5m avec un SRID choisi
    location = models.PointField(srid=4326, geography=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Validation spatiale de 5m par catégorie."""
        if self.location and self.category:
            limit = 5
            duplicates = Asset.objects.filter(
                category=self.category,
                location__dwithin=(
                    self.location,
                    D(m=limit),
                ),  # si un element existe deja a moins de 5m : d_within pour GiST
            )
            if self.pk:
                duplicates = duplicates.exclude(pk=self.pk)

            if duplicates.exists():
                raise ValidationError(
                    f"Un actif de type '{self.get_category_display()}' est déjà présent dans un rayon de {limit}m."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

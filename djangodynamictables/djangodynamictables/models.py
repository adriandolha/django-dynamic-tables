from django.contrib.auth.models import User
from django.db import models


class DynamicModelMetadata(models.Model):
    model_name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    fields = models.JSONField(
        verbose_name="Model fields",
        null=False,
        blank=False,
    )

    class Meta:
        managed = True
        indexes = [
            models.Index(fields=["model_name"]),
        ]

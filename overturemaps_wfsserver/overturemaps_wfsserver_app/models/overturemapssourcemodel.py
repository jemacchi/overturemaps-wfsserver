from django.contrib.gis.db import models

class OverturemapsSourceModel(models.Model):
    property = models.CharField(max_length=100, blank=True, null=True)
    dataset = models.CharField(max_length=100, blank=True, null=True)
    record_id = models.CharField(max_length=100, blank=True, null=True)
    confidence = models.FloatField(null=True)
    
    def __str__(self):
        return self.record_id
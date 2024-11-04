from django.contrib import admin

from django.contrib import admin
from .models import BBOXRequestBuildingModel, OverturemapsBuildingModel, OverturemapsSourceModel

admin.site.register(BBOXRequestBuildingModel)
admin.site.register(OverturemapsBuildingModel)
admin.site.register(OverturemapsSourceModel)


from django.shortcuts import render

from gisserver.features import FeatureType, ServiceDescription
from gisserver.geometries import CRS, WGS84
from gisserver.views import WFSView
from .models import Location

RD_NEW = CRS.from_srid(28992)

class LocationWFSView(WFSView):

    xml_namespace = "http://example.org/gisserver"

    # The service metadata
    service_description = ServiceDescription(
        title="Locations",
        abstract="Unittesting",
        keywords=["django-gisserver"],
        provider_name="Django",
        provider_site="https://www.example.com/",
        contact_person="django-gisserver",
    )

    # Each Django model is listed here as a feature.
    feature_types = [
        FeatureType(
            Location.objects.all(),
            fields="__all__",
            other_crs=[RD_NEW]
        ),
    ]

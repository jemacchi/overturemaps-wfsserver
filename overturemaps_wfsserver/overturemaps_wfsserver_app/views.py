import os
import logging
import xml.etree.ElementTree as ET

from django.shortcuts import render
from django.templatetags.static import static
from gisserver.features import FeatureType, ServiceDescription
from gisserver.geometries import CRS, WGS84
from gisserver.views import WFSView
from .models import OverturemapsBuildingModel, OverturemapsBuildingFeatureType
from django.conf import settings
from gisserver.geometries import CRS, BoundingBox

RD_NEW = CRS.from_srid(3857)
logger = logging.getLogger('wfsserver')

class BoundingBoxExtractor:
    def __init__(self, xml_content):
        self.root = ET.fromstring(xml_content)
        
    def get_bbox(self):
        namespaces = {
            'fes': 'http://www.opengis.net/fes/2.0',
            'gml': 'http://www.opengis.net/gml/3.2'
        }
        
        # Encontrar los elementos de las esquinas inferior y superior
        lower_corner = self.root.find('.//gml:lowerCorner', namespaces).text
        upper_corner = self.root.find('.//gml:upperCorner', namespaces).text
        
        # Convertir los valores a una lista de flotantes
        lower_coords = list(map(float, lower_corner.split()))
        upper_coords = list(map(float, upper_corner.split()))
        
        # Retornar los valores como una secuencia
        return (lower_coords[0], lower_coords[1], upper_coords[0], upper_coords[1])

class OverturemapsWFSView(WFSView):

    xml_namespace = "http://geotekne.com.ar/wfsserver"

    service_description = ServiceDescription(
        title="Overturemaps",
        abstract="Unittesting",
        keywords=["django-gisserver"],
        provider_name="Geotekne",
        provider_site="https://www.geotekne.com.ar/",
        contact_person="Jose Macchi",
    )

    buildings_ft = OverturemapsBuildingFeatureType(OverturemapsBuildingModel.objects.all(),fields="__all__",other_crs=[RD_NEW])
    
    feature_types = [
        buildings_ft,
    ]
    
    def get(self, request, *args, **kwargs):
        logger.debug('Get call entrypoint')
        # Convert to WFS key-value-pair format.
        self.KVP = {key.upper(): value for key, value in request.GET.items()}
        req = self.KVP.get("REQUEST")
        if req == "GetFeature":
            # get BBOX from filter (only in PoC)
            filter = self.KVP.get("FILTER")
            if filter is not None:
                extractor = BoundingBoxExtractor(filter)
                bbox = extractor.get_bbox()                
                # update BBOX on FeatureTypes
                self.buildings_ft.set_data(bbox)

        # then call the get in super
        ret = super().get(request,args,kwargs)
        return ret

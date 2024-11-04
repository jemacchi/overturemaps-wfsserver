import logging

from django.shortcuts import render
from django.templatetags.static import static
from gisserver.features import ServiceDescription
from gisserver.geometries import CRS 
from gisserver.views import WFSView
from .models import OverturemapsBuildingModel, OverturemapsBuildingFeatureType
from .utils import BoundingBoxExtractor

RD_NEW = CRS.from_srid(3857)

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

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

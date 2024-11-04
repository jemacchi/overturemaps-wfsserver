import geojson
import io

from overturemaps import record_batch_reader

from django.contrib.gis.db import models
from django.contrib.gis.geos import MultiPolygon, Polygon
from gisserver.features import FeatureType
from django.db import transaction
from .overturemapssourcemodel import OverturemapsSourceModel
from .overturemapsutils import is_bbox_contained, get_writer, copy

import logging

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)

class OverturemapsBuildingModel(models.Model):
    geo_id = models.CharField(max_length=100)
    version = models.IntegerField()
    update_time = models.DateTimeField()
    has_parts = models.BooleanField()
    sources = models.ManyToManyField(OverturemapsSourceModel)
    geometry = models.MultiPolygonField()

    def __str__(self):
        return self.geo_id

class BBOXRequestBuildingModel(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    min_x = models.FloatField()
    min_y = models.FloatField()
    max_x = models.FloatField()
    max_y = models.FloatField()

    def __str__(self):
        return f"BBOX({self.min_x}, {self.min_y}, {self.max_x}, {self.max_y}) at {self.timestamp}"

class OverturemapsBuildingFeatureType(FeatureType):

    bbox = None

    def set_data(self, bb):
        self.bbox = bb
        logger.debug('Bbox %s',str(bb))
        min_x, min_y, max_x, max_y = bb
        if is_bbox_contained(BBOXRequestBuildingModel, min_x, min_y, max_x, max_y):
            logger.debug('BBOX is already contained in database')
            return
        else:
            logger.debug('BBOX is not completly contained in database')
            self.dump_to_database()
            # save the bbox after dump of objects
            bbox_request = BBOXRequestBuildingModel.objects.create(min_x=min_x,min_y=min_y,max_x=max_x,max_y=max_y)

    def _load_overturemaps(self):
        # locality|locality_area|administrative_boundary|building|building_part|division|division_area|place|segment|connector|infrastructure|land|land_cover|land_use|water
        datatype = 'building'
        output_format = 'geojson'
        output = io.StringIO()
        reader = record_batch_reader(datatype, self.bbox)
        with get_writer(output_format, output, schema=reader.schema) as writer:
            copy(reader, writer)
        output.seek(0)
        gj = geojson.loads(output.getvalue())
        return gj

    def get_queryset(self):
        logger.debug('Get queryset')
        return super().get_queryset()

    def dump_to_database(self):
        # load from overturemaps
        logger.debug('Request to overturemaps')
        self.data = self._load_overturemaps()
        # dump to database
        features = self.data['features']
        logger.debug('Dumping')
        instances = []
        with transaction.atomic():
            for feature in features:
                properties = feature['properties']
                geom = feature['geometry']
                
                geometry = ''
                if geom['type'] == "Polygon":
                  try: 
                    geomPoly = Polygon(geom['coordinates'][0])
                    geometry = MultiPolygon(geomPoly)
                    geometry.srid = 4326
                  except (ValueError, TypeError) as e:
                    logger.error(f"Error creating Polygon from feature {properties['id']},{geom}: {e}")
                    continue
                else:
                  if geom['type'] == "MultiPolygon":
                    try:
                      ccount = len(geom['coordinates'])
                      holes = []
                      for i in range(1, ccount):
                        holes.append(Polygon(geom['coordinates'][i]))
                      geomPoly = Polygon(geom['coordinates'][0])
                      geometry = MultiPolygon(geomPoly, holes)
                      geometry.srid = 4326
                    except (ValueError, TypeError) as e:
                      logger.error(f"Error creating MultiPolygon from feature {properties['id']},{geom}: {e}")
                      continue
                  else:
                      logger.error(f"Feature {properties['id']} does not contains a valid geometry type {geom}")
                      continue

                if not geometry.valid:
                    logger.error(f"Feature {properties['id']} does not contains a valid geometry {geom}")
                    continue

                try:
                    instance, created = OverturemapsBuildingModel.objects.update_or_create(
                        geo_id=properties['id'],
                        defaults={
                            'version': properties['version'],
                            'update_time': properties['update_time'],
                            'has_parts': properties['has_parts'],
                            'geometry': geometry,
                        }
                    )

                    if not created:
                        instance.sources.clear()

                    for source in properties['sources']:
                        source_instance = OverturemapsSourceModel.objects.create(
                            property=source['property'],
                            dataset=source['dataset'],
                            record_id=source['record_id'],
                            confidence=source['confidence']
                        )
                        instance.sources.add(source_instance)
                    instances.append(instance)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error saving feature {properties['id']}: {e}")
                    continue
        return instances

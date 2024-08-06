import geojson
import geopandas as gpd
import os
import json
import sys
import io
import shapely.wkb

from overturemaps import record_batch_reader

from django.contrib.gis.db import models
from django.contrib.gis.geos import Polygon
from django.contrib.gis.db.models.functions import MakeValid
from gisserver.features import FeatureType
from django.db import transaction
from django.conf import settings

import logging
logger = logging.getLogger('wfsserver')

def get_writer(output_format, path, schema):
    if output_format == "geojson":
        writer = GeoJSONWriter(path)
    return writer

def copy(reader, writer):
    while True:
        try:
            batch = reader.read_next_batch()
        except StopIteration:
            break
        if batch.num_rows > 0:
            writer.write_batch(batch)

class BaseGeoJSONWriter:
    """
    A base feature writer that manages either a file handle
    or output stream. Subclasses should implement write_feature()
    and finalize() if needed
    """

    def __init__(self, where):
        self.file_handle = None
        if isinstance(where, str):
            self.file_handle = open(os.path.expanduser(where), "w")
            self.writer = self.file_handle
        else:
            self.writer = where
        self.is_open = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, value, traceback):
        self.close()

    def close(self):
        if not self.is_open:
            return
        self.finalize()
        if self.file_handle:
            self.file_handle.close()
        self.is_open = False

    def write_batch(self, batch):
        if batch.num_rows == 0:
            return

        for row in batch.to_pylist():
            feature = self.row_to_feature(row)
            self.write_feature(feature)

    def write_feature(self, feature):
        pass

    def finalize(self):
        pass

    def row_to_feature(self, row):
        geometry = shapely.wkb.loads(row.pop("geometry"))
        row.pop("bbox")
        # This only removes null values in the top-level dictionary but will leave in
        # nulls in sub-properties
        properties = {k: v for k, v in row.items() if k != "bbox" and v is not None}
        return {
            "type": "Feature",
            "geometry": geometry.__geo_interface__,
            "properties": properties,
        }

class GeoJSONWriter(BaseGeoJSONWriter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._has_written_feature = False

        self.writer.write('{"type": "FeatureCollection", "features": [\n')

    def write_feature(self, feature):
        if self._has_written_feature:
            self.writer.write(",\n")
        self.writer.write(json.dumps(feature, separators=(",", ":")))
        self._has_written_feature = True

    def finalize(self):
        self.writer.write("]}")


class OverturemapsSourceModel(models.Model):
    property = models.CharField(max_length=100, blank=True, null=True)
    dataset = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100)
    confidence = models.FloatField(null=True)
    
    def __str__(self):
        return self.geo_id

class OverturemapsBuildingModel(models.Model):
    geo_id = models.CharField(max_length=100)
    version = models.IntegerField()
    update_time = models.DateTimeField()
    has_parts = models.BooleanField()
    sources = models.ManyToManyField(OverturemapsSourceModel)
    geometry = models.PolygonField()

    def __str__(self):
        return self.geo_id

class OverturemapsBuildingFeatureType(FeatureType):

    bbox = None
    # deprecated
    geojson_path = os.path.join(settings.BASE_DIR, 'overturemaps_wfsserver/static/geojson/tandil.json')

    def set_data(self, bb):
        self.bbox = bb
        logger.debug(bb)
        self.dump_to_database()

    def _load_overturemaps(self):
        datatype = 'building'
        output_format = 'geojson'
        output = io.StringIO()
        reader = record_batch_reader(datatype, self.bbox)
        with get_writer(output_format, output, schema=reader.schema) as writer:
            copy(reader, writer)
        output.seek(0)
        gj = geojson.loads(output.getvalue())
        return gj

    def _load_geojson(self):
        with open(self.geojson_path) as f:
            gj = geojson.load(f)
        return gj

    def get_queryset(self):
        logger.debug('DEBUG: get queryset')
        return super().get_queryset()

    def dump_to_database(self):
        # load from overturemaps
        self.data = self._load_overturemaps()
        #self.data = self._load_geojson()
        # dump to database
        features = self.data['features']
        logger.debug('DEBUG: dumping')
        instances = []
        with transaction.atomic():
            for feature in features:
                properties = feature['properties']
                geom = feature['geometry']
                polygon = Polygon(geom['coordinates'][0])

                polygon.srid = 4326
                polygon = MakeValid(polygon)

                instance, created = OverturemapsBuildingModel.objects.update_or_create(
                    geo_id=properties['id'],
                    defaults={
                        'version': properties['version'],
                        'update_time': properties['update_time'],
                        'has_parts': properties['has_parts'],
                        'geometry': polygon,
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
        return instances

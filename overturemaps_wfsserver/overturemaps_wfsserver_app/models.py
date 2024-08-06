import geojson
import geopandas as gpd
import os
import json
import sys
import io
import shapely.wkb

from overturemaps import record_batch_reader

from django.contrib.gis.db import models
from django.contrib.gis.geos import Polygon, LinearRing, GEOSGeometry
from gisserver.features import FeatureType
from django.db import transaction
from django.conf import settings

import logging
logger = logging.getLogger('wfsserver')

def is_bbox_contained(new_min_x, new_min_y, new_max_x, new_max_y):
    bbox_requests = BBOXRequestBuildingModel.objects.all()
    for bbox in bbox_requests:
        if (bbox.min_x <= new_min_x <= bbox.max_x and
            bbox.min_y <= new_min_y <= bbox.max_y and
            bbox.min_x <= new_max_x <= bbox.max_x and
            bbox.min_y <= new_max_y <= bbox.max_y):
            return True
    return False

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
    dataset = models.CharField(max_length=100, blank=True, null=True)
    record_id = models.CharField(max_length=100, blank=True, null=True)
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
        logger.debug(bb)
        min_x, min_y, max_x, max_y = bb
        if is_bbox_contained(min_x, min_y, max_x, max_y):
            logger.debug('DEBUG: BBOX is already contained in database')
            return
        else:
            self.dump_to_database()
            bbox_request = BBOXRequestBuildingModel.objects.create(min_x=min_x,min_y=min_y,max_x=max_x,max_y=max_y)

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

    def get_queryset(self):
        logger.debug('DEBUG: get queryset')
        return super().get_queryset()

    def dump_to_database(self):
        # load from overturemaps
        self.data = self._load_overturemaps()
        # dump to database
        features = self.data['features']
        logger.debug('DEBUG: dumping')
        instances = []
        with transaction.atomic():
            for feature in features:
                properties = feature['properties']
                geom = feature['geometry']
                try:
                    exterior_ring = LinearRing(geom['coordinates'][0])
                    polygon = Polygon(exterior_ring)
                    polygon.srid = 4326

                    if not polygon.valid:
                        continue

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
                except (ValueError, TypeError) as e:
                    print(f"DEBUG: Error al crear el polígono para el feature {properties['id']}: {e}")
                    continue
        return instances

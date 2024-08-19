import asyncio
from aiopmtiles import Reader
import mercantile
import mapbox_vector_tile  
import geojson  
import os
import io
import gzip
import math

async def save_tiles_for_bbox(reader, bbox, zoom, output_dir):
    tiles = list(mercantile.tiles(bbox[0], bbox[1], bbox[2], bbox[3], [zoom]))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for tile in tiles:
        data = await reader.get_tile(tile.z, tile.x, tile.y)
        if data:
            tile_filename = f"tile_{tile.z}_{tile.x}_{tile.y}.pbf"
            tile_path = os.path.join(output_dir, tile_filename)
            with open(tile_path, 'wb') as f:
                f.write(data)
            print(f"Saved tile {tile.z}/{tile.x}/{tile.y} to {tile_path}")

def transform_tile_coords_to_geojson(tile, feature):
    tile_size = 4096
    world_extent = 2 ** tile.z * tile_size
    def transform_point(px, py):
        world_x = tile.x * tile_size + px
        world_y = tile.y * tile_size + (tile_size - py)
        lon = (world_x / world_extent) * 360.0 - 180.0
        n = math.pi - 2.0 * math.pi * world_y / world_extent
        lat = math.degrees(math.atan(math.sinh(n)))
        return [lon, lat]

    if feature['geometry']['type'] == 'Point':
        px, py = feature['geometry']['coordinates']
        feature['geometry']['coordinates'] = transform_point(px, py)

    elif feature['geometry']['type'] in ['LineString', 'MultiPoint']:
        transformed_coords = [
            transform_point(x, y)
            for x, y in feature['geometry']['coordinates']
        ]
        feature['geometry']['coordinates'] = transformed_coords
    elif feature['geometry']['type'] in ['Polygon', 'MultiLineString']:
        transformed_coords = [
            [
                transform_point(x, y)
                for x, y in ring
            ]
            for ring in feature['geometry']['coordinates']
        ]
        feature['geometry']['coordinates'] = transformed_coords
    elif feature['geometry']['type'] == 'MultiPolygon':
        transformed_coords = [
            [
                [
                    transform_point(x, y)
                    for x, y in ring
                ]
                for ring in polygon
            ]
            for polygon in feature['geometry']['coordinates']
        ]
        feature['geometry']['coordinates'] = transformed_coords
    return feature
       
async def get_geojson_for_bbox(reader, bbox, zoom):
    tiles = list(mercantile.tiles(bbox[0], bbox[1], bbox[2], bbox[3], [zoom]))
    #print(tiles)
    features = []
    for tile in tiles:
        data = await reader.get_tile(tile.z, tile.x, tile.y)
        if data:
            zip_bytes = io.BytesIO(data)
            with gzip.GzipFile(fileobj=zip_bytes, mode='rb') as f:
                mvt_data = f.read()
                decoded_tile = mapbox_vector_tile.decode(mvt_data)
            
                for layer_name, layer in decoded_tile.items():
                    for feature in layer['features']:
                        geom = transform_tile_coords_to_geojson(tile, feature)
                        geojson_feature = geojson.Feature(
                            geometry=geom['geometry'],
                            properties=feature['properties'],
                            id=feature.get('id', None)
                        )
                        features.append(geojson_feature)

    feature_collection = geojson.FeatureCollection(features)
    return feature_collection

async def main():
    output_dir = 'tiles'
    async with Reader("https://overturemaps-tiles-us-west-2-beta.s3.amazonaws.com/2024-07-22/buildings.pmtiles") as src:
        #bbox = (-77.05, 38.85, -77.00, 38.90)  # sample bbox (xmin, ymin, xmax, ymax)
        bbox = (2.876294,51.199333,2.932827,51.222203)  #belgium
        zoom = 14  # zoom level
        geojson_data = await get_geojson_for_bbox(src, bbox, zoom)
        print(geojson.dumps(geojson_data, indent=2))
        
        #await save_tiles_for_bbox(src, bbox, zoom, output_dir)

asyncio.run(main())

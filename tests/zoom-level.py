import math

def calculate_zoom_level(bbox, tile_size=4096, max_zoom=14):
    min_lon, min_lat, max_lon, max_lat = bbox
    
    earth_circumference = 40075017  # earth circunference
    initial_resolution = earth_circumference / tile_size  
    
    width = max_lon - min_lon
    height = max_lat - min_lat
    
    bbox_resolution = max(width, height)
    
    zoom_level = math.log2(initial_resolution / bbox_resolution)
    
    zoom_level = max(0, min(max_zoom, int(zoom_level)))
    
    return zoom_level

bbox = [2.876294,51.199333,2.932827,51.222203]
#bbox = [-0.3216,43.3589,19.3074,50.6545]
zoom_level = calculate_zoom_level(bbox)
print(f"Best zoom level based on bbox : {zoom_level}")


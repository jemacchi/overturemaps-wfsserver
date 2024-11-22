import logging
import xml.etree.ElementTree as ET
from gisserver.geometries import CRS

RD_NEW = CRS.from_srid(3857)

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

class BoundingBoxExtractor:
        
    def get_bbox_from_filter(self, xml_content):
        root = ET.fromstring(xml_content)

        namespaces = {
            'fes': 'http://www.opengis.net/fes/2.0',
            'gml': 'http://www.opengis.net/gml/3.2'
        }
        
        lower_corner = root.find('.//gml:lowerCorner', namespaces).text
        upper_corner = root.find('.//gml:upperCorner', namespaces).text
        
        lower_coords = list(map(float, lower_corner.split()))
        upper_coords = list(map(float, upper_corner.split()))
        
        return (lower_coords[0], lower_coords[1], upper_coords[0], upper_coords[1])

    def get_bbox_from_param(self, bbox):

        try:
            coords = list(map(float, bbox.split(',')))
            if len(coords) != 4:
                raise ValueError("BBox should have 4 parameters")
        except ValueError as e:
            logger.error(f"Error parsing bbox: {e}")
            return None

        return tuple(coords)
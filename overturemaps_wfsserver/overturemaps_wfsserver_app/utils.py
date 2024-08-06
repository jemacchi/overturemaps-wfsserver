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
    def __init__(self, xml_content):
        self.root = ET.fromstring(xml_content)
        
    def get_bbox(self):
        namespaces = {
            'fes': 'http://www.opengis.net/fes/2.0',
            'gml': 'http://www.opengis.net/gml/3.2'
        }
        
        lower_corner = self.root.find('.//gml:lowerCorner', namespaces).text
        upper_corner = self.root.find('.//gml:upperCorner', namespaces).text
        
        lower_coords = list(map(float, lower_corner.split()))
        upper_coords = list(map(float, upper_corner.split()))
        
        return (lower_coords[0], lower_coords[1], upper_coords[0], upper_coords[1])

from shapely.geometry import Polygon


class Building:

    def __init__(self, id, uuid, geometry_type, geometry):
        self.id = id
        self.uuid = uuid
        self.geometry_type = geometry_type
        self.polygon = Polygon(geometry)
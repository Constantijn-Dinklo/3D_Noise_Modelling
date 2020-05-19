
from shapely.geometry import Polygon


class GroundType:

    def __init__(self, id, uuid, geometry, absp_index, holes=[]):
        self.id = id
        self.uuid = uuid
        self.polygon = Polygon(geometry)
        self.index = absp_index

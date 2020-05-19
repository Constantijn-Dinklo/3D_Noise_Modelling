
from shapely.geometry import shape


class GroundType:

    def __init__(self, id, uuid, geometry, absp_index):
        self.id = id
        self.uuid = uuid
        self.polygon = shape(geometry)
        self.index = absp_index

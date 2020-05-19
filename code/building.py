
from shapely.geometry import shape


class Building:

    def __init__(self, id, bag_id, geometry, ground_level, roof_level):
        self.id = id
        self.bag_id = bag_id
        self.polygon = shape(geometry)
        self.ground_level = ground_level
        self.roof_level = roof_level

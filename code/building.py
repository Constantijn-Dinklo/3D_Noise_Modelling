
from shapely.geometry import shape, Polygon, MultiPolygon, LineString


class Building:

    def __init__(self, id, bag_id, geometry, ground_level, roof_level):
        self.id = id
        self.bag_id = bag_id
        self.shape = shape(geometry)
        self.polygon = None
        self.ground_level = ground_level
        self.roof_level = roof_level

        self.underground = False
        if (self.ground_level > self.roof_level):
            self.underground = True
        
        self.walls = []
        
        b_geom_coord = geometry['coordinates']
        b_geom_type = geometry['type']
        if b_geom_type == 'Polygon':
            self.polygon = Polygon(b_geom_coord[0])
            for polygon_index in range(len(b_geom_coord)):
                polygon_object = b_geom_coord[polygon_index]
                for coord_index in range(len(polygon_object[:(len(polygon_object)-1)])):
                    a = list(polygon_object[coord_index])
                    b = list(polygon_object[coord_index+1])
                    wall_2D = (a[:len(a)-1], b[:len(b)-1])
                    self.walls.append(wall_2D)
        
        elif b_geom_type == 'MultiPolygon':
            for multi_polygon_index in range(len(b_geom_coord)):
                multi_polygon_object = b_geom_coord[multi_polygon_index]
                for polygon_index in range(len(multi_polygon_object)):
                    polygon_object = multi_polygon_object[polygon_index]
                    for coord_index in range(len(polygon_object[:(len(polygon_object)-1)])):
                        a = list(polygon_object[coord_index])
                        b = list(polygon_object[coord_index+1])
                        wall_2D = (a[:len(a)-1], b[:len(b)-1])
                        self.walls.append(wall_2D)
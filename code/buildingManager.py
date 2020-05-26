from building import Building
import fiona

class BuildingManager:

    def __init__(self):
        self.buildings = {}

    def read_buildings_shp(self, path_to_shp):
        with fiona.open(path_to_shp) as records:
            for building_info in records:
                building_id = building_info['id']
                building_bag_id = building_info['properties']['bag_id']
                b_geom_shape = building_info['geometry']
                b_geom_coord = building_info['geometry']['coordinates']
                b_geom_type = building_info['geometry']['type']
                if b_geom_type == 'Polygon':
                    for polygon_index in range(len(b_geom_coord)):
                        polygon_object = b_geom_coord[polygon_index]
                        walls = []
                        for coord_index in range(len(polygon_object[:(len(polygon_object)-1)])):
                            a = list(polygon_object[coord_index])
                            b = list(polygon_object[coord_index+1])
                            wall_2D = [a[:len(a)-1],b[:len(b)-1]]
                            walls.append(wall_2D)
                if b_geom_type == 'MultiPolygon':
                    for multi_polygon_index in range(len(b_geom_coord)):
                        multi_polygon_object = b_geom_coord[multi_polygon_index]
                        for polygon_index in range(len(multi_polygon_object)):
                            polygon_object = multi_polygon_object[polygon_index]
                            walls = []
                            for coord_index in range(len(polygon_object[:(len(polygon_object)-1)])):
                                a = list(polygon_object[coord_index])
                                b = list(polygon_object[coord_index+1])
                                wall_2D = [a[:len(a)-1],b[:len(b)-1]]
                                walls.append(wall_2D)             
                b_ground_level = building_info['properties']['h_maaiveld']
                b_roof_level = building_info['properties']['h_dak']

                building = Building(building_id, building_bag_id, b_geom_shape, b_ground_level, b_roof_level, walls)

                self.buildings[building_id] = building

    def add_building(self, building_id, building_bag_id, geometry, ground_level, roof_level, walls):
        building = Building(building_id, building_bag_id, geometry, ground_level, roof_level, walls)
        self.buildings[building_id] = building
    
    def get_building(self, id):
        return self.buildings[id]


if __name__ == "__main__":
    buildingManager = BuildingManager()
    buildingManager.read_buildings_shp('input/lod13.shp')
    # print(buildingManager.buildings)

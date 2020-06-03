import fiona

from building import Building
from shapely.strtree import STRtree

class BuildingManager:

    def __init__(self):
        self.buildings = {}
        self.polygon_id_to_building_id = {}
        self.buildings_geometry = []
        self.buildings_tree = None

    def read_buildings_shp(self, path_to_shp):
        with fiona.open(path_to_shp) as records:
            for building_info in records:
                building_id = building_info['id']
                building_bag_id = building_info['properties']['bag_id']
                b_geom_shape = building_info['geometry']
                b_ground_level = building_info['properties']['h_maaiveld']
                b_roof_level = building_info['properties']['h_dak']

                self.add_building(building_id, building_bag_id, b_geom_shape, b_ground_level, b_roof_level)

    def add_building(self, building_id, building_bag_id, geometry, ground_level, roof_level):
        building = Building(building_id, building_bag_id, geometry, ground_level, roof_level)
        self.buildings[building_id] = building
        self.buildings_geometry.append(building.polygon)
        self.polygon_id_to_building_id[id(building.polygon)] = building_id

    def create_rtree(self):
        self.buildings_tree = STRtree(self.buildings_geometry)

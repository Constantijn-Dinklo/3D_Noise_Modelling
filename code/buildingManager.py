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
                b_ground_level = building_info['properties']['h_maaiveld']
                b_roof_level = building_info['properties']['h_dak']

                building = Building(building_id, building_bag_id, b_geom_shape, b_ground_level, b_roof_level)

                self.buildings[building_id] = building

    def get_building(self, id):
        return self.buildings[id]


if __name__ == "__main__":
    buildingManager = BuildingManager()
    buildingManager.read_buildings_shp('input/lod13.shp')
    # print(buildingManager.buildings)


from building import Building

import fiona

class BuildingManager:

    def __init__(self):
        self.buildings = {}

    def read_buildings_gpkg(self, path_to_gpkg):
        with fiona.open(path_to_gpkg) as pkg:
            for building_info in pkg:

                feature_id = building_info['id']
                building_id = building_info['properties']['id']
                building_uuid = building_info['properties']['uuid']
                b_geom_type = building_info['geometry']['type']
                b_geom_coord = building_info['geometry']['coordinates']
                b_geom_shape = b_geom_coord[0][0]
                
                building = Building(building_id, building_uuid, b_geom_type, b_geom_shape)

                self.buildings[building_id] = building

    def get_building(self, id):
        return self.buildings[id]

if __name__ == "__main__":

    buildingManager = BuildingManager()
    buildingManager.read_buildings_gpkg('input/37fz1_bodemvlakken_6.0.gpkg')
    #print(buildingManager.buildings)
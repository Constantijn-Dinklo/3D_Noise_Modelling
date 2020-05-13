from groundType import GroundType

import fiona


class GroundTypeManager:

    def __init__(self):
        self.grd_division = {}

    def read_grd_type_gpkg(self, path_to_gpkg):
        with fiona.open(path_to_gpkg) as pkg:
            for ground_info in pkg:
                ground_id = ground_info['id']
                ground_uuid = ground_info['properties']['uuid']
                g_geom_shape = ground_info['geometry']
                g_absp_index = ground_info['properties']['bodemfactor']

                ground = GroundType(ground_id, ground_uuid, g_geom_shape, g_absp_index)

                self.grd_division[ground_id] = ground

    def read_grd_type_shp(self, path_to_shp):
        with fiona.open(path_to_shp) as records:
            for ground_info in records:
                ground_id = ground_info['id']
                ground_uuid = ground_info['properties']['uuid']
                g_geom_shape = ground_info['geometry']
                g_absp_index = ground_info['properties']['bodemfacto']

                ground = GroundType(ground_id, ground_uuid, g_geom_shape, g_absp_index)

                self.grd_division[ground_id] = ground

    def get_ground(self, id):
        return self.grd_division[id]


if __name__ == "__main__":
    groundTypeManager = GroundTypeManager()
    groundTypeManager.read_grd_type_gpkg('input/37fz1_bodemvlakken_6.0.gpkg')

    # print(groundTypeManager.grd_division)

import fiona

from groundType import GroundType

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

                self.add_ground_type(ground_id, ground_uuid, g_geom_shape, g_absp_index)

    def read_grd_type_shp(self, path_to_shp):
        with fiona.open(path_to_shp) as records:
            for ground_info in records:
                ground_id = ground_info['id']
                ground_uuid = ground_info['properties']['uuid']
                g_geom_shape = ground_info['geometry']
                g_absp_index = ground_info['properties']['bodemfacto']

                self.add_ground_type(ground_id, ground_uuid, g_geom_shape, g_absp_index)

    def add_ground_type(self, ground_id, uuid, geometry, absp_index, holes=[]):
        ground = GroundType(ground_id, uuid, geometry, absp_index, holes)
        self.grd_division[ground_id] = ground

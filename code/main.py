import fiona
import groundTin as TIN
import misc
import sys
import numpy as np
from pprint import pprint

from xmlParserManager import XmlParserManager
from buildingManager import BuildingManager
from groundTypeManager import GroundTypeManager
from sourceReceiver import ReceiverPoints
from simpleReflection import ReflectionPath
from crossSectionManager import CrossSectionManager
from reflectionManager import ReflectionManager

#This should be a temporary input type
#def read_ground_objects()


def main(sys_args):
    print(sys_args[0])

    constraint_tin_file_path = sys_args[1]
    ground_type_file_path = ""#sys_args[2]
    building_file_path = ""#sys_args[3]

    building_gpkg_file = "input/buildings_lod_13.gpkg"

    tin = TIN.read_from_objp(constraint_tin_file_path)

    ground_type_manager = GroundTypeManager()
    building_manager = BuildingManager()

    #Read in the buildings and ground types
    #This should be removed and moved to the files individually
    with fiona.open("input/semaantics_test_part_id.shp") as semantics:
        for record in semantics:
            #Not sure if this does anything right now
            if record['properties']['uuid'] is not None and record['properties']['bodemfacto'] is None:
                continue
            elif record['properties']['h_dak'] is not None and record['properties']['h_maaiveld'] is None:
                continue
            elif (record['properties']['h_dak'] is not None and
                  record['properties']['h_maaiveld'] > record['properties']['h_dak']):
                continue
            
            record_id = int(record['id'])
            record_id = record_id * 100

            record_index = 1
            
            if record['properties']['bag_id'] is not None:
                #print("=== Adding a building ===")
                part_id = 'b' + record['properties']['part_id']
                bag_id = record['properties']['bag_id']
                geometry = record['geometry']
                geom_coord = record['geometry']['coordinates']
                geom_type = record['geometry']['type']
                if geom_type == 'Polygon':
                    for polygon_index in range(len(geom_coord)):
                        polygon_object = geom_coord[polygon_index]
                        walls = []
                        for coord_index in range(len(polygon_object[:(len(polygon_object)-1)])):
                            a = list(polygon_object[coord_index])
                            b = list(polygon_object[coord_index+1])
                            wall_2D = [a[:len(a)-1],b[:len(b)-1]]
                            walls.append(wall_2D)
                if geom_type == 'MultiPolygon':
                    for multi_polygon_index in range(len(geom_coord)):
                        multi_polygon_object = geom_coord[multi_polygon_index]
                        for polygon_index in range(len(multi_polygon_object)):
                            polygon_object = multi_polygon_object[polygon_index]
                            walls = []
                            for coord_index in range(len(polygon_object[:(len(polygon_object)-1)])):
                                a = list(polygon_object[coord_index])
                                b = list(polygon_object[coord_index+1])
                                wall_2D = [a[:len(a)-1],b[:len(b)-1]]
                                walls.append(wall_2D)             
                ground_level = record['properties']['h_maaiveld']
                roof_level = record['properties']['h_dak']
                building_manager.add_building(record_id + record_index, bag_id, geometry, ground_level, roof_level, walls)
            
            elif record['properties']['uuid'] is not None:
                #print("=== Adding a ground type ===")

                uuid = record['properties']['uuid']
                part_id = 'g' + uuid
                absp_index = record['properties']['bodemfacto']
                
                if record['geometry']['type'] == 'MultiPolygon':
                    for p in record['geometry']['coordinates']:
                        geometry = p[0]
                        holes = []
                        for i in range(1, len(p)):
                            holes.append(p[i])
                        ground_type_manager.add_ground_type(part_id, uuid, geometry, absp_index, holes)
                        record_index = record_index + 1
                else:
                    geometry = record['geometry']['coordinates'][0]
                    ground_type_manager.add_ground_type(part_id, uuid, geometry, absp_index)

    hard_coded_receiver_point = [((93550, 441900))]

    # Input variables:
    cnossos_radius = 2000.0 # should be 2000.0 --> 2km, for now 100 is used to test
    cnossos_angle = 2.0
    source_height = 0.05
    receiver_height = 2

    #Create a Receiver Point to which the sound should travel
    receiver_point = ReceiverPoints(cnossos_radius, cnossos_angle)
    receiver_point.return_list_receivers('input/receivers_END2016_testarea.shp')
    receiver_point.return_segments_source('input/test_2.gml')
    #Get all the source points that are within range of this receiver point
    source_points_dict = receiver_point.return_intersection_points()

    # Get first order reflections
    reflected_paths = ReflectionManager()
    reflected_paths.get_reflection_paths(source_points_dict, tin, building_manager, building_gpkg_file)
    
    cross_section_manager = CrossSectionManager()
    cross_section_manager.get_cross_sections(source_points_dict, reflected_paths.reflection_manager, source_height, receiver_height, tin, ground_type_manager, building_manager)
    cross_section_manager.write_obj("test_object_reflect_01.obj")

    #sections, extensions, materials = cross_section_manager.get_paths_and_extensions()
    print("xml_parser")
    xml_manager = XmlParserManager()
    xml_manager.write_xml_files(cross_section_manager)

if __name__ == "__main__":
    main(sys.argv)
    # call all functions etc.
    #xml_parser(vts, mat)
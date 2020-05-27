import fiona
import groundTin as TIN
import misc
import sys
import numpy as np
from pprint import pprint

from xmlParserManager import XmlParserManager
from buildingManager import BuildingManager
from groundTypeManager import GroundTypeManager
from sourceReceiver import ReceiverPoint
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
                ground_level = record['properties']['h_maaiveld']
                roof_level = record['properties']['h_dak']
                building_manager.add_building(part_id, bag_id, geometry, ground_level, roof_level)

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

    """
    Format for data:
    === INPUT ===
    TIN.objp:
        vertices:
        "v float(x) float(y) float(z)"
        faces / triangles:
        "f int(id_1) int(id_2) int(id_2) int(nb1) int(nb2) int(nb3)"
        Attributes:
        "a float(attribute ID)" <- why not integer?
    
    semaantics_test.shp:
        [describe this file]
        Holds all buildings and groundtypes in shapefile
    
    Buildings.shp:
        idem

    groundTypes.shp:
        idem
    
    receivers.xxx:
        receiver file
    
    === Algoritmic structures ===
    building_manager: dictionary with buildings
        building_manager = {
            int(building_id) = Building object,
            ...
        }
    
    Building (class):
        id: (super key / unique) (also key in dictionary)
        bag_id: building ID from BAG (not unique)
        polygon = shapely.shape object with polygon
        ground_level = height of ground NAP
        roof_level = roof height NAP
    
    ground_type_manager: dicitonary with groundTypes
        building_manager = {
            int(ground_id) = GroundType object,
            ...
        }

    GroundType (class):
        id = (super key / unique) (also key in dictionary)
        uuid: unique key from original file
        polygon = shapely.shape object with polygon
        index = absorbtion index 

    source_points_dict:
        dictionary with receivers and their sources
        {
            receiver_i: [dir_1, dir_2, ..., dir_n],
            receiver_n: ...
        }
        where:
            receiver: tuple(x,y)
            dir_i: list of found sources (in order of distance) along one direction
            dir_i = [source_1, source_2 ...]
            note: dir_i does not exist if that direction does not have instersections
            note_2: dir_i can have only 1 source, but it is still a list
        
    propagations_paths:
        dictionary with propagations paths holding the location of the source / receiver / reflection
        {
            receiver_i: [path_1, path_2, ..., path_n],
            receiver_n: ...
        }
        where:
            receiver_i: (float(x), float(y))
            path_i: [source] or [reflection, source]
            where:"
                source = [float(x), float(y)]
                reflection = [float(x), float(y)]
            note: There can be multiple path_i with the same source since there can be more reflections. 
    
    reflection_heights:
        dictionary with a list per receiver.
        {
            receiver_i: [height_1, height_2, ..., height_n],
            receiver_n: ...
        }
        where:
            receiver_i: (float(x), float(y))
            height_i: [height_r_1, height_r_2, ...m height_r_n]
            where:
                height_r_1 = [float(x), float(y)]
            note: for each reflection there is one height

    cross_section:
        dictionary with the paths per receiver
        {
            receiver_i: [path_1, path_2, ..., path_n]
            receiver_n: ...
        }
        where: 
            receiver_i: (float(x), float(y))
            path_i: [point_1, point_2, ..., point_n]
            where:
                point_1 = [(float(x), float(y), float(z)), mat]
                where:
                    mat: string "C" / "G" / "A0" defining the material
            note: both direct and reflected paths are the same.
    
    extension:
        dictionary with extension per receiver
        {
            receiver_i: [ext_1, ext_2, ..., ext_n]
            receiver_n: ...
        }
        where:
            receiver_i: (float(x), float(y))
            ext_1: {
                point_i: [type, height above TIN, (material)],
                point_n: ...
            }
            where:
                type: string - "source" / "receiver" / "wall" / "edge" / "barrier"
                height above TIN: float - relative height above the point
                optional:
                    material: string - the material of the extension
            note: material is only supplied when the type != "source" or "receiver"     
    
    === Output ===
    xml output:
        xml file with all information.
    """

    hard_coded_receiver_point = [((93550, 441900))]

    # Input variables:
    cnossos_radius = 2000.0 # should be 2000.0 --> 2km, for now 100 is used to test
    cnossos_angle = 2.0
    source_height = 0.05
    receiver_height = 2

    #Create a Receiver Point to which the sound should travel
    receiver_point = ReceiverPoint(hard_coded_receiver_point, cnossos_radius, cnossos_angle)
    receiver_point.return_segments_source('input/test_2.gml')
    #Get all the source points that are within range of this receiver point
    source_points_dict = receiver_point.return_intersection_points()

    # Get first order reflections
    reflected_paths = ReflectionManager()
    reflected_paths.get_reflection_paths(source_points_dict, tin, building_manager, building_gpkg_file)
    
    cross_section_manager = CrossSectionManager(source_points_dict, reflected_paths.reflection_manager,
                                                source_height, receiver_height)
    cross_section_manager.get_cross_sections(tin, ground_type_manager, building_manager)
    cross_section_manager.write_obj("test_object_reflect_01.obj")

    sections, extensions, materials = cross_section_manager.get_paths_and_extensions()
    
    xml_manager = XmlParserManager(sections, extensions, materials)
    #xml_manager.write_xml_files()

    
if __name__ == "__main__":
    main(sys.argv)
    # call all functions etc.
    #xml_parser(vts, mat)
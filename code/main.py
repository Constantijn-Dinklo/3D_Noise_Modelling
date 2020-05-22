import fiona
import groundTin as TIN
import misc
import sys
from pprint import pprint
#import xmlParser as xml

from buildingManager import BuildingManager
from groundTypeManager import GroundTypeManager
from sourceReceiver import ReceiverPoint
from simpleReflection import ReflectionPath
import crossSectionManager

#This should be a temporary input type
#def read_ground_objects()


def main(sys_args):
    print(sys_args[0])

    constraint_tin_file_path = sys_args[1]
    ground_type_file_path = ""#sys_args[2]
    building_file_path = ""#sys_args[3]

    tin = TIN.read_from_objp(constraint_tin_file_path)

    ground_type_manager = GroundTypeManager()
    building_manager = BuildingManager()

    #Read in the buildings and ground types
    #This should be removed and moved to the files individually
    with fiona.open("input/semaantics_test.shp") as semantics:
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
                
                bag_id = record['properties']['bag_id']
                geometry = record['geometry']
                ground_level = record['properties']['h_maaiveld']
                roof_level = record['properties']['h_dak']
                building_manager.add_building(record_id + record_index, bag_id, geometry, ground_level, roof_level)

            elif record['properties']['uuid'] is not None:
                #print("=== Adding a ground type ===")

                uuid = record['properties']['uuid']
                absp_index = record['properties']['bodemfacto']
                
                if record['geometry']['type'] == 'MultiPolygon':
                    for p in record['geometry']['coordinates']:
                        geometry = p[0]
                        holes = []
                        for i in range(1, len(p)):
                            holes.append(p[i])
                        ground_type_manager.add_ground_type(record_id + record_index, uuid, geometry, absp_index, holes)
                        record_index = record_index + 1
                else:
                    geometry = record['geometry']['coordinates'][0]
                    ground_type_manager.add_ground_type(record_id + record_index, uuid, geometry, absp_index)

    hard_coded_receiver_point = ((93550, 441900))
    cnossos_radius = 2000.0 # should be 2000.0 --> 2km, for now 100 is used to test
    cnossos_angle = 2.0

    #Create a Receiver Point to which the sound should travel
    receiver_point = ReceiverPoint(hard_coded_receiver_point, cnossos_radius, cnossos_angle)
    receiver_point.return_segments_source('input/test_2.gml')

    #Get all the source points that are within range of this receiver point
    source_points_dict = receiver_point.return_intersection_points()
    #source_points = source_points_dict[hard_coded_receiver_point] no need for this

    #cross_sections = CrossSectionManager()
    #cross_sections.cross_sections = source_points_dict

    for receiver, sources_list in source_points_dict.items():
        receiver_triangle = tin.find_receiver_triangle(2, receiver)
        receiver_section = crossSectionManager.CrossSectionManager(hard_coded_receiver_point, receiver_triangle, sources_list)

        receiver_paths = receiver_section.get_cross_sections(tin, ground_type_manager, building_manager)
        receiver_section.write_obj("output/test_object_02.obj")
        # optimise the start triangle (default at 2 right now)
        
    #Find all the reflected paths for now.
    #reflection_path = ReflectionPath(s_dict,r_dict,f_dict)
    #for source_point in source_points:
    #    source_point_list = [source_point]
    #    receiver_point_list = [receiver_point] CrossSectionManager

if __name__ == "__main__":
    main(sys.argv)
    # call all functions etc.
    #xml_parser(vts, mat)
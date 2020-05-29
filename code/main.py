import fiona
import groundTin as TIN
import misc
import sys
import numpy as np
import xml.etree.cElementTree as ET

from pprint import pprint

from xmlParserManager import XmlParserManager
from buildingManager import BuildingManager
from groundTypeManager import GroundTypeManager
from receiverPoint import ReceiverPoint
from reflectionPath import ReflectionPath
from crossSectionManager import CrossSectionManager
from reflectionManager import ReflectionManager

#This should be a temporary input type
#def read_ground_objects()

def return_segments_source(path):
    """
    Explanation: Changes the data structure of the coordinates from strings to floats in tuples
    ---------------
    Input:
    path : string - the path of the XML file
    ---------------
    Output:
    list : list - a list of all the coordinates are saved as (x, y), line segments with every next point in list
    """
    count = 0
    sets = []
    line_string = []
    line_float = []
    line_segments = []

    tree = ET.parse(path)
    root = tree.getroot()
    for child in root.iter():
        if "coordinates" in child.tag:
            coordinates = child.text
            line_string = coordinates.split()
            if len(line_string) > 1:
                for point in line_string:
                    coord = point.split(',')
                    sets.append((float(coord[0]), float(coord[1])))
                    count += 1
                if len(line_string) == count:
                    line_float.append(sets)
                    count = 0
                    sets = []
    for elem in line_float:
        if len(elem) == 2:
            line_segments.append(elem)
        if len(elem) > 2:
            for i in range(len(elem) - 1):
                first_el = elem[i]
                next_el = elem[i + 1]
                line_segments.append([first_el, next_el])
    return line_segments

def read_building_and_ground(building_manager, ground_type_manager):
    
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
                print(part_id)
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

def main(sys_args):
    print(sys_args[0])

    constraint_tin_file_path = sys_args[1]
    ground_type_file_path = ""#sys_args[2]
    building_file_path = ""#sys_args[3]

    tin = TIN.read_from_objp(constraint_tin_file_path)

    ground_type_manager = GroundTypeManager()
    building_manager = BuildingManager()

    read_building_and_ground(building_manager, ground_type_manager)
    
    #COS: Till now we have a:
    #   - Constrained Tin
    #   - Building Manager
    #   - Ground Type Manager
    
    hard_coded_receiver_point = [((93550, 441900))]

    # Input variables:
    cnossos_radius = 2000.0 # should be 2000.0 --> 2km, for now 100 is used to test
    cnossos_angle = 2.0
    source_height = 0.05
    receiver_height = 2

    receiver_points = {} #COS: Might make another manager from this, but might not be needed.
    road_lines = [] #COS: Find a better place for this?

    #Create a Receiver Point to which the sound should travel
    with fiona.open('input/receiver_points_scenario_000.shp') as shape: #Open the receiver points shapefile
        for elem in shape:
            geometry = elem["geometry"]
            rec_pt_coords = geometry["coordinates"]
            print(rec_pt_coords)
            rec_pt = ReceiverPoint(rec_pt_coords)
            receiver_points[rec_pt_coords] = rec_pt

    road_lines = return_segments_source('input/test_2.gml') #Read in the roads

    #COS: Till now we have a:
    #   - Constrained Tin
    #   - Building Manager
    #   - Ground Type Manager
    #   - The receiver points
    #   - The line segments

    source_points = {}
    #source_points structure!
    #For each receiver, there is a set of rays
    #For each ray, there is a list of sources
    #{receiver:{ray_1:[source_1, source_2], ray_2:[source_3, source_4]}}

    #Go through all the receiver points and get their possible source points
    #count = 0
    for rec_pt_coords in receiver_points:
        rec_pt = receiver_points[rec_pt_coords]
        int_pts = rec_pt.return_intersection_points(road_lines)
        
        #Set all the intersection points as possible source points, not this list (int_pts) could be empty
        if len(int_pts.keys()) > 0:
            source_points[rec_pt_coords] = int_pts
        
        #if count == 100:
        #    break

        #count = count + 1
    
    for building in building_manager.buildings:
        print(building)

    #Create the cross sections for all the direct paths
    cross_section_manager = CrossSectionManager()
    cross_section_manager.get_cross_sections_direct(source_points, source_height, tin, ground_type_manager, building_manager, receiver_height)
    
    # Get first order reflections
    reflected_paths = ReflectionManager()
    reflected_paths.get_reflection_paths(source_points, building_manager)

    #Loop through all the reflection paths
    for receiver, ray_paths in reflected_paths.reflection_paths.items():
        for ray_end, source_paths in ray_paths.items():
            for source, path in source_paths.items():
                cross_section_manager.create_cross_section_rp(path, tin, ground_type_manager, building_manager, receiver_height)
    

    cross_section_manager.write_obj("test_object_reflect_01.obj")

    #sections, extensions, materials = cross_section_manager.get_paths_and_extensions()
    print("xml_parser")
    xml_manager = XmlParserManager()
    xml_manager.write_xml_files(cross_section_manager)

if __name__ == "__main__":
    main(sys.argv)
    # call all functions etc.
    #xml_parser(vts, mat)
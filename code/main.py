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
    with fiona.open('input/receivers_END2016_testarea.shp') as shape: #Open the receiver points shapefile
        for elem in shape:
            geometry = elem["geometry"]
            rec_pt_coords = geometry["coordinates"]
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

    #Go through all the receiver points and get their possible source points
    for rec_pt_coords in receiver_points:
        rec_pt = receiver_points[rec_pt_coords]
        int_pts = rec_pt.return_intersection_points(road_lines)
        
        #Set all the intersection points as possible source points, not this list (int_pts) could be empty
        source_points[rec_pt_coords] = int_pts

    #print(source_points)

    
    
    #receiver_point = ReceiverPoint((0,0), cnossos_radius, cnossos_angle)
    #receiver_point.return_list_receivers('input/receivers_END2016_testarea.shp')
    #receiver_point.return_segments_source('input/test_2.gml')
    #Get all the source points that are within range of this receiver point
    #source_points_dict = receiver_point.return_intersection_points()

    # Get first order reflections
    reflected_paths = ReflectionManager()
    reflected_paths.get_reflection_paths(source_points, tin, building_manager, building_gpkg_file)
    exit()
    
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
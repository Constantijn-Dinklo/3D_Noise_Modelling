import fiona
import groundTin as TIN
import misc
import numpy as np
import sys
import xml.etree.cElementTree as ET

from buildingManager import BuildingManager
from crossSectionManager import CrossSectionManager
from groundTypeManager import GroundTypeManager
from receiverPoint import ReceiverPoint
from reflectionManager import ReflectionManager
from reflectionPath import ReflectionPath
from xmlParserManager import XmlParserManager

from pprint import pprint
from shapely.geometry import Polygon, LineString, Point
from shapely.strtree import STRtree
from time import time


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
            line_segments.append(LineString((elem[0], elem[1])))
        if len(elem) > 2:
            for i in range(len(elem) - 1):
                first_el = elem[i]
                next_el = elem[i + 1]
                line_segments.append(LineString((first_el, next_el)))
    return line_segments

def read_building_and_ground(file_path, building_manager, ground_type_manager):
    
    #Read in the buildings and ground types
    #This should be removed and moved to the files individually
    with fiona.open(file_path) as semantics:
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

def main(sys_args):
    start = time()
    print("Running {}".format(sys_args[0]))

    #Input files
    constraint_tin_file_path = "input/constrainted_tin_clean_semantics.objp"
    building_and_ground_file_path = "input/semaantics_test_part_id.shp"
    receiver_point_file_path = "input/test_receivers_simple_case.shp"
    road_lines_file_path = "input/scen_000_one_road.gml"

    #Output files
    cross_section_obj_file_path = "test_object_reflect_01.obj"

    tin = TIN.read_from_objp(constraint_tin_file_path)

    print("read dtm in {:.2f} seconds".format(time() - start))
    watch = time()

    ground_type_manager = GroundTypeManager()
    building_manager = BuildingManager()

    read_building_and_ground(building_and_ground_file_path, building_manager, ground_type_manager)
    building_manager.create_rtree()
    
    print("read buildings in: {:.2f} seconds".format(time() - watch))
    watch = time()
    
    receiver_points = {} #COS: Might make another manager from this, but might not be needed.
    road_lines = [] #COS: Find a better place for this?

    #Create a Receiver Point to which the sound should travel
    with fiona.open(receiver_point_file_path) as shape: #Open the receiver points shapefile
        for elem in shape:
            geometry = elem["geometry"]
            rec_pt_coords = geometry["coordinates"]
            rec_pt = ReceiverPoint(rec_pt_coords)
            receiver_points[rec_pt_coords] = rec_pt

    road_lines = return_segments_source(road_lines_file_path) #Read in the roads

    print("read receiver points in: {:.2f}\nFind sources...".format(time() - watch))
    watch = time()

    #source_points structure!
    #For each receiver, there is a set of rays
    #For each ray, there is a list of sources
    #{receiver:{ray_1:[source_1, source_2], ray_2:[source_3, source_4]}}
    source_points = {}

    # create a tree for roads
    tree_roads = STRtree(road_lines)

    number_of_sources = 0
    #Go through all the receiver points and get their possible source points
    for rec_pt_coords in receiver_points:
        rec_pt = receiver_points[rec_pt_coords]
        int_pts = rec_pt.return_intersection_points(tree_roads)
        number_of_sources += len(int_pts)
        #Set all the intersection points as possible source points, not this list (int_pts) could be empty
        if len(int_pts.keys()) > 0:
            source_points[rec_pt_coords] = int_pts

    print("found {} sources in {:.2f} seconds \nGet direct cross sections...".format(number_of_sources, time() - watch))
    watch = time()

    # set variables to play with
    source_height = 0.05
    receiver_height = 2.0
    defaulf_noise_levels = {
        "sourceType"         : "LineSource",
        "measurementType"    : "OmniDirectionnal",
        "frequencyWeighting" : "LIN",
        "power"              : np.array([78.2, 74.1, 71.6, 74.2, 78, 73.8, 69, 55.9])
    }
    minimal_building_height_threshold = 1.0 # this is the minimal height difference for a building to be reflective

    #Create the cross sections for all the direct paths
    cross_section_manager = CrossSectionManager(source_height, receiver_height)
    cross_section_manager.get_cross_sections_direct(source_points, tin, ground_type_manager, building_manager, source_height, receiver_height)
    
    print("ran direct cross_sections in: {:.2f} seconds\nGet refelcted paths...".format(time() - watch))
    watch = time()

    # Get first order reflections   
    reflected_paths = ReflectionManager()
    reflected_paths.get_reflection_paths(source_points, building_manager, tin, minimal_building_height_threshold)
    
    print("ran reflected paths in: {:.2f}\nGet reflected cross sections...".format(time() - watch))
    watch = time()

    #Loop through all the reflection paths
    for receiver, ray_paths in reflected_paths.reflection_paths.items():
        for ray_end, source_paths in ray_paths.items():
            for source, path in source_paths.items():
                cross_section_manager.get_cross_sections_reflection(path, tin, ground_type_manager, building_manager, source_height, receiver_height)
    

    #cross_section_manager.write_obj(cross_section_obj_file_path)
   
    print("ran reflected cross sections in: {:.2f}".format(time() - watch))
    watch = time()

    xml_manager = XmlParserManager()
    xml_manager.write_xml_files(cross_section_manager, defaulf_noise_levels, source_height)

    print("write xml in: {:.2f}".format(time() - watch))
    watch = time()
    
    print("total runtime in: {}".format(time() - start))


if __name__ == "__main__":
    main(sys.argv)
import fiona
import groundTin as TIN
import misc
import numpy as np
import sys
import xml.etree.cElementTree as ET

from buildingManager import BuildingManager
from crossSectionManager import CrossSectionManager
from groundTypeManager import GroundTypeManager
from receiverManager import ReceiverManager
from receiverPoint import ReceiverPoint
from reflectionManager import ReflectionManager
from reflectionPath import ReflectionPath
from xmlParserManager import XmlParserManager

from pprint import pprint
from shapely.geometry import Polygon, LineString, Point
from shapely.strtree import STRtree
from time import time

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
    constraint_tin_file_path = "input/area_00.objp"
    building_and_ground_file_path = "input/semaantics_test_part_id.shp"
    receiver_point_file_path = "input/receiver_points_scenario_000.shp"
    #receiver_point_file_path = "input/receiver_grid_v2_clipped.shp"
    road_lines_file_path = "input/scen_000_one_road.gml"

    #Output files
    # the output xml files is split up to put the receiver_dict one folder up.
    output_folder_xml_files = ("output/", "xml/")


    tin = TIN.read_from_objp(constraint_tin_file_path)

    print("read dtm in {:.2f} seconds".format(time() - start))
    watch = time()

    ground_type_manager = GroundTypeManager()
    building_manager = BuildingManager()

    read_building_and_ground(building_and_ground_file_path, building_manager, ground_type_manager)
    building_manager.create_rtree()
    
    print("read {} buildings in: {:.2f} seconds".format(len(building_manager.buildings), time() - watch))
    watch = time()
    
    receiver_manager = ReceiverManager()
    receiver_manager.read_receiver_points(receiver_point_file_path)

    road_lines = [] #COS: Find a better place for this?
    road_lines = return_segments_source(road_lines_file_path) #Read in the roads
    tree_roads = STRtree(road_lines) # create a tree for roads

    print("read receiver points in: {:.2f}\nFind sources for each receiver...".format(time() - watch))
    watch = time()

    #Get the source points for each receiver
    receiver_manager.determine_source_points(tree_roads)   
    
    print("found sources in {:.2f} seconds \nGet direct cross sections...".format(time() - watch))
    watch = time()

    # set variables to play with
    source_height = 0.05
    receiver_height = 2.0
    minimal_building_height_threshold = 1.0 # this is the minimal height difference for a building to be reflective
    default_noise_levels = {
        "sourceType"         : "LineSource",
        "measurementType"    : "OmniDirectionnal",
        "frequencyWeighting" : "LIN",
        "power"              : np.array([78.2, 74.1, 71.6, 74.2, 78, 73.8, 69, 55.9])
    }

    #Create the cross sections for all the direct paths
    cross_section_manager = CrossSectionManager(source_height, receiver_height)
    #print("=== get direct cross sections ===")
    cross_section_manager.get_cross_sections_direct(receiver_manager.receiver_points, tin, ground_type_manager, building_manager, source_height, receiver_height)
    
    print("ran direct cross_sections in: {:.2f} seconds\nGet reflected paths...".format(time() - watch))
    watch = time()

    # Get first order reflections   
    reflection_manager = ReflectionManager()
    reflection_manager.get_reflection_paths(receiver_manager.receiver_points, building_manager, tin, minimal_building_height_threshold)
    
    print("ran reflected paths in: {:.2f} seconds\nGet reflected cross sections...".format(time() - watch))
    watch = time()

    #Loop through all the reflection paths
    for receiver_coords, ray_paths in reflection_manager.reflection_paths.items():
        for ray_end, source_paths in ray_paths.items():
            for source, reflection_path in source_paths.items():
                cross_section_manager.get_cross_sections_reflection(reflection_path, tin, ground_type_manager, building_manager, source_height, receiver_height)

    print("ran reflected cross sections in: {:.2f}".format(time() - watch))
    watch = time()

    #Optionally write an obj with all the cross sections
    #write_obj_paths_per_receiver = True
    #cross_section_manager.write_obj(write_obj_paths_per_receiver)
   
    print("wrote cross sections in: {:.2f} seconds\nWrite xml files...".format(time() - watch))
    watch = time()

    xml_manager = XmlParserManager()
    xml_manager.write_xml_files(cross_section_manager, default_noise_levels, output_folder_xml_files)

    print("wrote xml files in: {:.2f} seconds".format(time() - watch))
    watch = time()
    
    print("total runtime in: {}".format(time() - start))


if __name__ == "__main__":
    main(sys.argv)
import bisect
from crossSection import CrossSection
from pprint import pprint
import numpy as np
from misc import interpolate_edge, reverse_bisect_left, write_cross_section_to_obj


class CrossSectionManager:

    def __init__(self):
        self.cross_sections = {}
        self.receiver_triangles = {}
    
    def get_cross_section(self, receiver, path, tin, ground_type_manager, building_manager, source_height, receiver_height, reflection_heights=0):
        cross_section = CrossSection(path, receiver, reflection_heights)

        #Find the triangle of the tin in which the receiver is located.
        if receiver in self.receiver_triangles.keys():
            receiver_triangle = self.receiver_triangles[receiver]
        else:
            init_tr = tin.find_init_triangle(receiver)
            receiver_triangle = tin.find_receiver_triangle(init_tr, receiver)
            self.receiver_triangles[receiver] = receiver_triangle

        #Create the cross section from the receiver to the source point        
        cross_section.get_cross_section(receiver_triangle, tin, ground_type_manager, building_manager, source_height, receiver_height)

        if receiver not in self.cross_sections.keys():
            self.cross_sections[receiver] = []
        
        self.cross_sections[receiver].append(cross_section)
        
        return cross_section
    
    def get_intermediate_cross_section_collinear_source(self, source_point, cross_section, source_height, receiver_height, receiver):

            # find where the intermediate sources lie in the 'complete' cross-section

            # check if the cross section is going in the positive or negative direction
            if cross_section.vertices[-1][0] - cross_section.vertices[0][0] < 0:
                split_idx = reverse_bisect_left(cross_section.vertices, source_point)

            # if the path is parallel with the x axis, check if the y axis is in negative direction.
            elif cross_section.vertices[-1][0] - cross_section.vertices[0][0] == 0 and cross_section.vertices[-1][1] - cross_section.vertices[0][1] < 0:
                split_idx = reverse_bisect_left(cross_section.vertices, source_point)

            # the x direction is positive, or y is in positive direction
            else:
                split_idx = bisect.bisect_left(cross_section.vertices, source_point)

            part_path_direct = cross_section.vertices[split_idx:]
            source_ground_height = interpolate_edge(cross_section.vertices[split_idx - 1], cross_section.vertices[split_idx], source_point)
            part_path_direct = [(source_point[0], source_point[1], source_ground_height)] + part_path_direct

            cross_section_collinear_point = CrossSection([source_point], receiver, 0)
            cross_section_collinear_point.vertices = part_path_direct
            cross_section_collinear_point.extension = {
                0: ["source", source_height],
                len(cross_section_collinear_point.vertices) - 1 : ["receiver", receiver_height]
            }
            part_path_direct_material = [cross_section.materials[split_idx]] + cross_section.materials[split_idx:]
            cross_section_collinear_point.materials = part_path_direct_material
            
            # Key must already exist, so no need to check.
            self.cross_sections[receiver].append(cross_section_collinear_point)
            return
    
    def get_cross_sections_direct(self, direct_paths, tin, ground_type_manager, building_manager, source_height, receiver_height):
        """
        Explanation: Finds cross sections for all propagation paths, both direct. and saves them in a dicitonary with cross_sections objects.
        ---------------
        Input:
            propagation_paths_dict_direct : dictionary - receiver is key, value is a list with the sources 
            propagation_paths_dict_reflect : dictionary - receiver is key, value is a list with the reflection point and the source
            source_height : float - height above ground for the source (defines in main.py)
            receiver_height : float - height above ground for the receiver (defined in main.py)
            tin : GroundTin object - stores the DTM in a triangle datastructure
            ground_type_manager : GroundTypeManager object - stores all the groundtype objects
            building_manager : BuildingManager object - stores all the building objects
        ---------------
        Output:
            void (fills self.cross_section_manager for each receiver with a list of paths)
        """

        #
        for receiver, ray_intersects in direct_paths.items():
            #For each ray, grab all the source points between the receiver and the ray_end
            for ray_end, source_points in ray_intersects.items():
                #Create cross section for the furthest away point
                furthest_source_point = source_points[-1]
                cross_section = self.get_cross_section(receiver, [furthest_source_point], tin, ground_type_manager, building_manager, source_height, receiver_height)

                # create cross sections for intermediate source points, if available
                for source_point in source_points[:-1]:
                    #print("got collinear path")
                    self.get_intermediate_cross_section_collinear_source(
                        source_point, 
                        cross_section, 
                        source_height, 
                        receiver_height, 
                        receiver
                        )

        return

    def get_cross_sections_reflection(self, reflection_path, tin, ground_type_manager, building_manager, source_height, receiver_height):

        # can work with single and multi order reflection.
        # for each reflection
        for i, reflection_points_list in enumerate(reflection_path.reflection_points):
            #take the heights
            reflection_heights = reflection_path.reflection_heights[i]
            path = reflection_points_list
            path.append(reflection_path.source)

            self.get_cross_section(reflection_path.receiver, path, tin, ground_type_manager, building_manager, source_height, receiver_height, reflection_heights)
    
    def write_obj(self, filename):
        """
        Explanation: Write the paths of this receiver to an obj file, calls write_cross_section_to_obj
        ---------------
        Input:
            filename : string - filename, including path and extension(.obj)
        ---------------
        Output:
            void (writes obj file)
        """
        i = 0
        for receiver, cross_sections in self.cross_sections.items():
            write_cross_section_to_obj(str(i) + filename, cross_sections)
            i += 1

    """
    Old stuff
    #            self.cross_section_manager[receiver] = []

        # Loop over all the list of collinear paths for each source
        for points_to_source in paths_to_sources:

            # Get the cross section for the point furthest away
            cross_section = CrossSection([points_to_source[-1]], receiver)
            cross_section.get_cross_section(receiver_triangle, tin, ground_type_manager, building_manager, source_height, receiver_height)
            
            # append the direct path directly
            self.cross_section_manager[receiver].append(cross_section)

            # If there are collinear points, the list is more than 1 point.
            if (len(points_to_source) > 1):

                # if the list is longer, go over each point, and slice the path such that its until the intermediate source.
                for point in points_to_source[:-1]:

                    # find where the intermediate sources lie in the 'complete' cross-section

                    # check if the cross section is going in the positive or negative direction
                    if cross_section.vertices[-1][0] - cross_section.vertices[0][0] < 0:
                        split_idx = reverse_bisect_left(cross_section.vertices, point)

                    # if the path is parallel with the x axis, check if the y axis is in negative direction.
                    elif cross_section.vertices[-1][0] - cross_section.vertices[0][0] == 0 and cross_section.vertices[-1][1] - cross_section.vertices[0][1] < 0:
                        split_idx = reverse_bisect_left(cross_section.vertices, point)

                    # the x direction is positive, or y is in positive direction
                    else:
                        split_idx = bisect.bisect_left(cross_section.vertices, point)

                    # what is split idx

                    # check if the intermediate point is exactly (should be nearby) the last edge of the sliced path ( in x,y coordinates)
                    if point == cross_section.vertices[split_idx][:2]:  # better to add a distance threshold
                        # create new cross_section for intermediate point
                        cross_section_collinear_point = CrossSection([point], receiver)
                        cross_section_collinear_point.vertices = cross_section.vertices[split_idx:]
                        cross_section_collinear_point.extension = {
                            0: ["source", source_height],
                            #split_idx + 1: ["receiver", receiver_height]
                            len(cross_section_collinear_point.vertices) - 1 : ["receiver", receiver_height]
                        }
                        cross_section_collinear_point.materials = cross_section.material[split_idx:]

                        self.cross_section_manager[receiver].append(cross_section_collinear_point)

                    # If the intermediate point is not on the edge, than interpolate the height and add this point (at the beginning, since it starts at the source.)
                    else:
                        part_path_direct = cross_section.vertices[split_idx:]
                        source_ground_height = interpolate_edge(cross_section.vertices[split_idx - 1], cross_section.vertices[split_idx], point)
                        part_path_direct = [(point[0], point[1], source_ground_height)] + part_path_direct

                        cross_section_collinear_point = CrossSection([point], receiver)
                        cross_section_collinear_point.vertices = part_path_direct
                        cross_section_collinear_point.extension = {
                            0: ["source", source_height],
                            #split_idx + 1: ["receiver", receiver_height]
                            len(cross_section_collinear_point.vertices) - 1 : ["receiver", receiver_height]
                        }
                        part_path_direct_material = [cross_section.materials[split_idx]] + cross_section.materials[split_idx:]
                        cross_section_collinear_point.materials = part_path_direct_material
                        
                        self.cross_section_manager[receiver].append(cross_section_collinear_point)
    """
    #This is a quick implementation!!! SHOULD BE CHECKED!!!
    


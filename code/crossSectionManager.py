import bisect
from crossSection import CrossSection
from pprint import pprint
import numpy as np
from misc import interpolate_edge, reverse_bisect_left, write_cross_section_to_obj


class CrossSectionManager:

    def __init__(self):
        self.cross_sections = {}

        self.receiver_triangles = {}

    def get_cross_section_rf(self, reflection_path):
        pass
    
    def get_cross_section(self, receiver, path, tin, ground_type_manager, building_manager):
        #Initialize the cross section
        #receiver = path[0]
        source_point = path[-1]
        cross_section = CrossSection(path, receiver)

        #Find the triangle of the tin in which the receiver is located.
        if receiver in self.receiver_triangles.keys():
            receiver_triangle = self.receiver_triangles[receiver]
        else:
            receiver_triangle = tin.find_receiver_triangle(2, receiver)
            self.receiver_triangles[receiver] = receiver_triangle

        #Create the cross section from the receiver to the source point        
        cross_section.get_cross_section(receiver_triangle, tin, ground_type_manager, building_manager, source_point[2], receiver[2])

        if receiver not in self.cross_sections.keys():
            self.cross_sections[receiver] = []
        
        self.cross_sections[receiver].append(cross_section)
    
    def get_cross_sections_direct(self, direct_paths, source_height, tin, ground_type_manager, building_manager):
        """
        Explanation: Finds cross sections for all propagation paths, both direct and reflected. and saves them in a dicitonary with cross_sections objects.
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
                #Go through all the source points in the list
                for source_point in source_points:
                    source_point = (source_point[0], source_point[1], source_height)
                    self.get_cross_section(receiver, [source_point], tin, ground_type_manager, building_manager)


        return


        # create a key in the dictionary for this receiver.
#            self.cross_section_manager[receiver] = []

        # find the receiver triangle to walk from. (TODO: optimize the starting triangle)
        if receiver in self.receiver_triangles.keys():
            receiver_triangle = self.receiver_triangles[receiver]
        else:
            receiver_triangle = tin.find_receiver_triangle(2, receiver)
            self.receiver_triangles[receiver] = receiver_triangle

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
    
        # Reflected paths
        #for receiver, reflections in propagation_paths_dict_reflect.items():
            # for each reflection_object in the list of reflection objects
        #    for reflection_object in reflections:
                # for each reflection point for this source, create the path
        #        for i in range(len(reflection_object.reflection_points)):
        #            points_to_source = [reflection_object.reflection_points[i], reflection_object.source]
        #            cross_section = CrossSection(points_to_source, receiver, reflection_object.reflection_heights[i])
        #            cross_section.get_cross_section(receiver_triangle, tin, ground_type_manager, building_manager, source_height, receiver_height)

        #            self.cross_section_manager[receiver].append(cross_section)

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
        for receiver, cross_sections in self.cross_section_manager.items():
            write_cross_section_to_obj(str(i) + filename, cross_sections)
            i += 1


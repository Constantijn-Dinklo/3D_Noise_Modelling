import bisect
import numpy as np

from crossSection import CrossSection
from misc import interpolate_edge, reverse_bisect_left

class CrossSectionManager:

    def __init__(self, source_default_height, receiver_default_height):
        self.cross_sections = {}
        self.receiver_triangles = {}

        self.source_default_height = source_default_height
        self.receiver_default_height = receiver_default_height
    
    def get_cross_section(self, receiver_coords, source, path, tin, ground_type_manager, building_manager, source_height, receiver_height, reflection_heights=0):
        #Find the triangle of the tin in which the receiver is located.
        if receiver_coords in self.receiver_triangles.keys():
            receiver_triangle = self.receiver_triangles[receiver_coords]
        else:
            init_tr = tin.find_vts_near_pt(receiver_coords)
            receiver_triangle = tin.find_receiver_triangle(init_tr, receiver_coords)
            # Make sure the receiver triangle is not in a building, this is not valid. if so, exclude it
            if(tin.attributes[receiver_triangle][0] == 'b'):
                return 
            self.receiver_triangles[receiver_coords] = receiver_triangle

        cross_section = CrossSection(path, receiver_coords, source, reflection_heights)
        #Create the cross section from the receiver to the source point        
        cross_section.get_cross_section(receiver_triangle, tin, ground_type_manager, building_manager, source_height, receiver_height)

        if receiver_coords not in self.cross_sections.keys():
            self.cross_sections[receiver_coords] = []
        
        self.cross_sections[receiver_coords].append(cross_section)
        
        return cross_section
    
    def get_intermediate_cross_section_collinear_source(self, source_point, cross_section, source_height, receiver_height, receiver):

        # find where the intermediate sources lie in the 'complete' cross-section

        source_coords = source_point.source_coords

        # check if the cross section is going in the positive or negative direction
        if cross_section.vertices[-1][0] - cross_section.vertices[0][0] < 0:
            split_idx = reverse_bisect_left(cross_section.vertices, source_coords)

        # if the path is parallel with the x axis, check if the y axis is in negative direction.
        elif cross_section.vertices[-1][0] - cross_section.vertices[0][0] == 0 and cross_section.vertices[-1][1] - cross_section.vertices[0][1] < 0:
            split_idx = reverse_bisect_left(cross_section.vertices, source_coords)

        # the x direction is positive, or y is in positive direction
        else:
            split_idx = bisect.bisect_left(cross_section.vertices, source_coords)

        part_path_direct = cross_section.vertices[split_idx:]
        source_ground_height = interpolate_edge(cross_section.vertices[split_idx - 1], cross_section.vertices[split_idx], source_coords)
        part_path_direct = [(source_coords[0], source_coords[1], source_ground_height)] + part_path_direct

        cross_section_collinear_point = CrossSection([source_coords], receiver, source_point, 0)
        cross_section_collinear_point.vertices = part_path_direct
        source_length = source_point.left_length + source_point.right_length
        cross_section_collinear_point.extension = {
            0: ["source", source_height, source_length],
            len(cross_section_collinear_point.vertices) - 1 : ["receiver", receiver_height]
        }
        part_path_direct_material = [cross_section.materials[split_idx]] + cross_section.materials[split_idx:]
        cross_section_collinear_point.materials = part_path_direct_material
        
        # Key must already exist, so no need to check.
        self.cross_sections[receiver].append(cross_section_collinear_point)
        return
    
    def get_cross_sections_direct(self, receiver_points, tin, ground_type_manager, building_manager, source_height, receiver_height):
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
        for receiver_coords, receiver in receiver_points.items():  
            #print(i, receiver.receiver_coords)
            #For each ray, grab all the source points between the receiver and the ray_end
            for ray_end, source_points in receiver.source_points.items():
                #Create cross section for the furthest away point
                furthest_source_point = source_points[-1]

                # find the receiver triangle. If this triangle is in a building, than it is not valid and should not be included.
                # This is done here, since there is no need for the collinear paths to be checked in this case. 
                init_tr = tin.find_vts_near_pt(receiver_coords)
                receiver_triangle = tin.find_receiver_triangle(init_tr, receiver_coords)
                if(tin.attributes[receiver_triangle][0] == 'b'):
                    continue
                self.receiver_triangles[receiver_coords] = receiver_triangle
                cross_section = self.get_cross_section(receiver_coords, furthest_source_point, [furthest_source_point.source_coords], tin, ground_type_manager, building_manager, source_height, receiver_height)

                # create cross sections for intermediate source points, if available
                for source_point in source_points[:-1]:
                    self.get_intermediate_cross_section_collinear_source(
                        source_point, 
                        cross_section, 
                        source_height, 
                        receiver_height, 
                        receiver_coords
                        )

    def get_cross_sections_reflection(self, reflection_path, tin, ground_type_manager, building_manager, source_height, receiver_height):

        # can work with single and multi order reflection.
        # for each reflection
        for i, reflection_points_list in enumerate(reflection_path.reflection_points):
            #take the heights
            reflection_heights = reflection_path.reflection_heights[i]
            path = reflection_points_list
            path.append(reflection_path.source.source_coords)

            self.get_cross_section(reflection_path.receiver, reflection_path.source, path, tin, ground_type_manager, building_manager, source_height, receiver_height, reflection_heights)
    
    def write_obj(self, output_path, individual_bool): 
        """
        Explanation: Write the paths of this receiver to an obj file, calls write_cross_section_to_obj
        ---------------
        Input:
            individual_bool : boolean - defines whether the paths shoudl be written per receiver, or all combined.
        ---------------
        Output:
            void (writes obj file)
        """
        print("=== Writing {} ===".format("paths_section"))
        # write the paths to individual receiver files.
        if(individual_bool):
            i = 0
            for receiver, cross_sections in self.cross_sections.items():
                self.write_cross_section_to_obj("{}/receiver_{}.obj".format(output_path, i), cross_sections)
                i +=1

        # Or write one file with all paths
        else:
            total_paths = []
            for receiver, cross_sections in self.cross_sections.items():
                total_paths.append(cross_sections)

            cross_section_file_path = output_path + "/cross_sections.obj"
            with open(cross_section_file_path, 'w') as f_out:
                base = 0
                vts_count_lst = [0]
                counter = 0
                for cross_section_paths in total_paths:
                    #write the vertices
                    for cross_section in cross_section_paths:
                        path = cross_section.vertices
                        path = np.array(path)
                        counter = counter + len(path)
                        vts_count_lst.append(counter)
                        for v in path:
                            f_out.write("v {:.2f} {:.2f} {:.2f}\n".format(v[0], v[1], v[2]))
                #print(vts_count_lst)
                # write the lines:
                j = 0
                for cross_section_paths in total_paths:
                    for i, cross_section in enumerate(cross_section_paths):
                        path = cross_section.vertices
                        base = vts_count_lst[j]
                        f_out.write("l")
                        for i in range(len(path)):
                            f_out.write(" " + str(base + i + 1))
                        f_out.write("\n")
                        j += 1

    def write_cross_section_to_obj(self, filename, cross_sections):

        #with open(obj_filename, 'w') as f_out:
        
        with open(filename, 'w') as f_out:
            vts_count_lst = [0]
            counter = 0
            for cross_section in cross_sections:
                path = cross_section.vertices
                path = np.array(path)
                counter = counter + len(path)
                vts_count_lst.append(counter)
                for v in path:
                    f_out.write("v {:.2f} {:.2f} {:.2f}\n".format(v[0], v[1], v[2]))
            
            #print(vts_count_lst)
            for i, cross_section in enumerate(cross_sections):
                path = cross_section.vertices
                base = vts_count_lst[i]
                f_out.write("l")
                for i in range(len(path)):
                    f_out.write(" " + str(base + i + 1))
                f_out.write("\n")
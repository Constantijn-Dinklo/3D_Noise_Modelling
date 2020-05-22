
from crossSection import CrossSection
from pprint import pprint
import numpy as np
from misc import write_cross_section_to_obj

class CrossSectionManager:

    def __init__(self, propagation_paths_dict, reflection_heights):
        self.propagation_paths_dict = propagation_paths_dict
        self.reflection_heights = reflection_heights
        self.paths = {}
    
    def get_cross_sections(self, tin, ground_type_manager, building_manager):
        """
        Explanation: Finds cross-sections while walking to the source point, for all sections from the receiver.
        ---------------
        Input:
            receiver : (x,y,z) - the receiver point we walk from
            source : (x,y,z) - the source point we want to walk to
            tr_receiver : integer - triangle id of triangle underneath receiver point
            buildings : Fiona's Collection where each record/building holds a 'geometry' and a 'property' key
        ---------------
        Output:
            void (fills self.paths with a list of paths)
        """
        
        """
        paths_dict = {receiver: [
            [source], 
            [source],
            [Reflection, source],
            [Reflection, source]
        ]}

        Heights_dict = {receiver: [
            h1,
            h2,
            h3,
            h4
        ]} 
        """

        for receiver, paths_to_sources in self.propagation_paths_dict.items():
            receiver_paths = []
            receiver_triangle = tin.find_receiver_triangle(2, receiver)
            reflection_counter = 0
            #pprint("paths to sources: {}".format(paths_to_sources))
            print(" ")
            for points_to_source in paths_to_sources:
                print("direct path: {}".format(points_to_source[-1]))
                cross_section = []
                # direct path:
                receiver_section = CrossSection([points_to_source[-1]], receiver)
                path_direct, extension  = receiver_section.get_cross_section(receiver_triangle, tin, ground_type_manager, building_manager)
                receiver_paths.append(path_direct)

                # optional reflected path
                if(len(points_to_source) > 1):
                    print("reflected path: {}".format(points_to_source))
                    receiver_section = CrossSection(points_to_source, receiver, self.reflection_heights[receiver][reflection_counter])
                    path_reflected, extension = receiver_section.get_cross_section(receiver_triangle, tin, ground_type_manager, building_manager)
                    receiver_paths.append(path_reflected)

            self.paths[receiver] = receiver_paths
        #pprint(self.paths)


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
        for receiver, paths in self.paths.items():
            write_cross_section_to_obj(str(i) + filename, paths)
            i += 1

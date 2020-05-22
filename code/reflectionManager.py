from simpleReflection import ReflectionPath
from pprint import pprint
#import numpy as np
from misc import write_cross_section_to_obj

class ReflectionManager:

    def __init__(self, source_receivers_dict):
        self.source_receivers_dict = source_receivers_dict
        self.first_order_paths = {}
    
    def get_reflections(self, tin, building_manager):
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
        
        for receiver, sources_list in self.source_receivers_dict.items():
            receiver_paths = []

            for source in sources_list:
                reflection_object = ReflectionPath(source, receiver)
                path = reflection_object.get_first_order_reflection(tin, building_manager)
                receiver_paths.append(path)
            self.paths[receiver] = receiver_paths

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
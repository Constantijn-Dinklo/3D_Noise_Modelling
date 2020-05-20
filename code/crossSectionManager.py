
from crossSection import CrossSection
from pprint import pprint
import numpy as np
from misc import write_cross_section_to_obj

class CrossSectionManager:

    def __init__(self, receiver, receiver_tr, sources_list):
        # one manager per receiver.
        self.sources_list = sources_list
        self.receiver = receiver
        self.receiver_triangle = receiver_tr
        self.paths = []
    
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
        receiver_paths = []
        for source in self.sources_list:
            receiver_section = CrossSection(source, self.receiver)
            path = receiver_section.get_cross_section(self.receiver_triangle, tin, ground_type_manager, building_manager)
            receiver_paths.append(path)
        self.paths = receiver_paths

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
        write_cross_section_to_obj(filename, self.paths)


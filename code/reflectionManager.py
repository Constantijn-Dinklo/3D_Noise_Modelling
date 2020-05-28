from simpleReflection import ReflectionPath, read_buildings
from pprint import pprint
#import numpy as np
from misc import write_cross_section_to_obj

class ReflectionManager:

    def __init__(self):
        self.reflection_manager = {}
    
    def get_reflection_paths(self, source_receivers_dict, tin, building_manager, building_filename):
        """
        Explanation: Finds reflection points for all source - receiver sets.
        ---------------
        Input:
            source_receivers_dict : dictionary - stores a list of sources for each receiver.
            tin : GroundTin object - stores the DTM in a triangle datastructure
            ground_type_manager : GroundTypeManager object - stores all the groundtype objects
            building_filename : string - name of the builings shapefile, this will be deleted later. (TODO)
        ---------------
        Output:
            void (fills self.paths with a list of paths)
        """
        # TODO remove this once it is taken care of, for now read in hte buildings shapefile
        buildings_dictionary = read_buildings(building_filename)
        # for each receiver, get the list of sources (which is once again a list of collinear sources)
        for receiver, sources_list_per_ray in source_receivers_dict.items():

            # initiate a list for each receiver
            self.reflection_manager[receiver] = []

            # for each list of collinear sources in the total sources list.
            for sources_list in sources_list_per_ray:
                # For each source in the list of collinear sources.
                for source in sources_list:
                    # create a reflectionPath object for each source - receiver pair
                    reflection_object = ReflectionPath(source)

                    # get a list of reflection points for that source, returns True of False (False when no reflections are found)
                    reflections_found = reflection_object.get_first_order_reflection(buildings_dictionary, receiver) # future replace with tin and building_manager

                    # it is false when it does not have reflections.
                    if(reflections_found):
                        # If a reflections is found, add the object.
                        self.reflection_manager[receiver].append(reflection_object)

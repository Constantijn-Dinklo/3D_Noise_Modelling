from simpleReflection import ReflectionPath, read_buildings
from pprint import pprint
#import numpy as np
from misc import write_cross_section_to_obj

class ReflectionManager:

    def __init__(self):
        #self.propagation_paths = {}
        #self.reflection_heights = {}

        self.reflection_manager = {}
    
    def get_reflection_paths(self, source_receivers_dict, tin, building_manager, building_filename):
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
        
        for receiver, sources_list_per_ray in source_receivers_dict.items():
            #self.reflection_heights[receiver] = []
            #self.propagation_paths[receiver] = []
            self.reflection_manager[receiver] = []
            for sources_list in sources_list_per_ray:
                for source in sources_list:
                    

                    buildings_dictionary = read_buildings(building_filename)
                    reflection_object = ReflectionPath(source, receiver)
                    reflections_found = reflection_object.get_first_order_reflection(buildings_dictionary) # future replace with tin and building_manager

                    # it is false when it does not have reflections.
                    if(reflections_found):
                        # If a reflections is found, save the object.
                        self.reflection_manager[receiver].append(reflection_object)
                        #pprint(paths_and_heights)
                        #[p1, p2, ..., pn], [h1, h2, ..., hn]
                        #for i in range(len(paths_and_heights[0])):
                            #print("point: {} height: {}".format(paths_and_heights[0][i], paths_and_heights[1][i]))
                        #    self.propagation_paths[receiver].append([paths_and_heights[0][i], source])
                        #    self.reflection_heights[receiver].append(paths_and_heights[1][i])
                    #else:
                    #    self.propagation_paths[receiver].append([source])

            #self.first_order_paths[receiver] = receiver_paths
        #pprint(self.propagation_paths)
        #return self.reflection_manager
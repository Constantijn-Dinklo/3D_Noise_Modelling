from reflectionPath import ReflectionPath, read_buildings
from pprint import pprint
#import numpy as np
from misc import write_cross_section_to_obj

class ReflectionManager:

    def __init__(self):

        self.reflection_paths = {}
    
    def get_reflection_path(self, receiver, source_list_per_ray, building_manager):
        """
        Explanation: Finds cross-sections between the receiver and all source points in the source_list_per_ray dictionary.
        ---------------
        Input:
            receiver : (x,y,z) - the receiver point we walk from
            source_list_per_ray : {(ray_end): [source_points]} - A dictionary where all the source points are listed per outgoing ray from the receiver
            building_manager : BuildingManager - The manager that holds all the building information
        ---------------
        Output:
            void (fills self.reflection_paths with a list of paths)
        """
        
        #Loop through all the source points from all outgoing rays from the receiver
        for ray_end_point, source_point_list in source_list_per_ray.items():
            #Loop through all the source points from one outoing ray from the receiver    
            for source_point in source_point_list:

                #Create a reflection path from source to receiver and get all possible reflections
                reflection_object = ReflectionPath(source_point, receiver)
                reflection_object.get_first_order_reflection(building_manager.buildings)

                self.reflection_paths[receiver] = reflection_object
    
    def get_reflection_paths(self, source_receivers_dict, building_manager):
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
            self.get_reflection_path(receiver, sources_list_per_ray, building_manager)
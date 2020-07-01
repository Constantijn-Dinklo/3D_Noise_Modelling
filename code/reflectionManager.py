from reflectionPath import ReflectionPath, read_buildings


class ReflectionManager:

    def __init__(self):
        self.reflection_paths = {}
    
    def get_reflection_path(self, receiver_coords, source_list_per_ray, building_manager, tin, minimal_height_difference):
        """
        Explanation: Finds cross-sections between the receiver and all source points in the source_list_per_ray dictionary.
        ---------------
        Input:
            receiver_coords : (x,y,z) - the receiver point we walk from
            source_list_per_ray : {(ray_end): [source_points]} - A dictionary where all the source points are listed per outgoing ray from the receiver
            building_manager : BuildingManager - The manager that holds all the building information
        ---------------
        Output:
            void (fills self.reflection_paths with a list of paths)
        """

        # Loop through all the source po ints from all outgoing rays from the receiver
        for ray_end_point, source_point_list in source_list_per_ray.items():
            # Loop through all the source points from one outoing ray from the receiver
            for source_point in source_point_list:

                # Create a reflection path from source to receiver and get all possible reflections
                reflection_object = ReflectionPath(source_point, receiver_coords)
                at_least_one_reflection = reflection_object.get_first_order_reflection(building_manager, tin, minimal_height_difference)

                # If at least 1 reflection was found, store it
                if at_least_one_reflection:
                    if receiver_coords not in self.reflection_paths.keys():
                        self.reflection_paths[receiver_coords] = {}
                    if ray_end_point not in self.reflection_paths[receiver_coords].keys():
                        self.reflection_paths[receiver_coords][ray_end_point] = {}

                    self.reflection_paths[receiver_coords][ray_end_point][source_point.source_coords] = reflection_object
    
    def get_reflection_paths(self, source_receivers_dict, building_manager, tin, minimal_height_difference):
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
        for receiver_coords, receiver in source_receivers_dict.items():
            self.get_reflection_path(receiver_coords, receiver.source_points, building_manager, tin, minimal_height_difference)


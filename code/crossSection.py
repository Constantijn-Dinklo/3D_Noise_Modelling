
class CrossSection:

    def __init__(self):
        self.source = None
        self.receiver = None
        
        #Please add any other data that belongs to a cross section here eg, maybe intermidiate points?
        self.intermidiate_points - []

    def get_cross_section(self, ground_tin, building_manager, ground_type_manager):
        """
        Explination: Read an objp file and make a tin from it.
        ---------------
        Input:
            ground_tin : a GroundTin instace - The tin in which the cross section is contained
            building_manager : A BuildingManager instance - The place where you can get all the info about buildings
            ground_type_manager : A GroundTypeManager instance - The place where you can get all the info about the ground types
        ---------------
        Output:
            void - Stores the path into the intermidiate_points list
        """
        
        pass
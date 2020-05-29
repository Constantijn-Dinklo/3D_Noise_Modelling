Format for data:
    === INPUT ===
    TIN.objp:
        vertices:
        "v float(x) float(y) float(z)"
        faces / triangles:
        "f int(id_1) int(id_2) int(id_2) int(nb1) int(nb2) int(nb3)"
        Attributes:
        "a float(attribute ID)" <- why not integer?
    
    semaantics_test.shp:
        [describe this file]
        Holds all buildings and groundtypes in shapefile
    
    Buildings.shp:
        idem

    groundTypes.shp:
        idem
    
    receivers.xxx:
        receiver file
    
    === Algoritmic structures ===
    building_manager: dictionary with buildings
        building_manager = {
            int(building_id) = Building object,
            ...
        }
    
    Building (class):
        id: (super key / unique) (also key in dictionary)
        bag_id: building ID from BAG (not unique)
        polygon = shapely.shape object with polygon
        ground_level = height of ground NAP
        roof_level = roof height NAP
    
    ground_type_manager: dicitonary with groundTypes
        building_manager = {
            int(ground_id) = GroundType object,
            ...
        }

    GroundType (class):
        id = (super key / unique) (also key in dictionary)
        uuid: unique key from original file
        polygon = shapely.shape object with polygon
        index = absorbtion index 

    source_points_dict:
        dictionary with receivers and their sources
        {
            receiver_i: [dir_1, dir_2, ..., dir_n],
            receiver_n: ...
        }
        where:
            receiver: tuple(x,y)
            dir_i: list of found sources (in order of distance) along one direction
            dir_i = [source_1, source_2 ...]
            note: dir_i does not exist if that direction does not have instersections
            note_2: dir_i can have only 1 source, but it is still a list
        
    propagations_paths:
        dictionary with propagations paths holding the location of the source / receiver / reflection
        {
            receiver_i: [path_1, path_2, ..., path_n],
            receiver_n: ...
        }
        where:
            receiver_i: (float(x), float(y))
            path_i: [source] or [reflection, source]
            where:"
                source = [float(x), float(y)]
                reflection = [float(x), float(y)]
            note: There can be multiple path_i with the same source since there can be more reflections. 
    
    reflection_heights:
        dictionary with a list per receiver.
        {
            receiver_i: [height_1, height_2, ..., height_n],
            receiver_n: ...
        }
        where:
            receiver_i: (float(x), float(y))
            height_i: [height_r_1, height_r_2, ...m height_r_n]
            where:
                height_r_1 = [float(x), float(y)]
            note: for each reflection there is one height

    cross_section:
        dictionary with the paths per receiver
        {
            receiver_i: [path_1, path_2, ..., path_n]
            receiver_n: ...
        }
        where: 
            receiver_i: (float(x), float(y))
            path_i: [point_1, point_2, ..., point_n]
            where:
                point_1 = [(float(x), float(y), float(z)), mat]
                where:
                    mat: string "C" / "G" / "A0" defining the material
            note: both direct and reflected paths are the same.
    
    extension:
        dictionary with extension per receiver
        {
            receiver_i: [ext_1, ext_2, ..., ext_n]
            receiver_n: ...
        }
        where:
            receiver_i: (float(x), float(y))
            ext_1: {
                point_i: [type, height above TIN, (material)],
                point_n: ...
            }
            where:
                type: string - "source" / "receiver" / "wall" / "edge" / "barrier"
                height above TIN: float - relative height above the point
                optional:
                    material: string - the material of the extension
            note: material is only supplied when the type != "source" or "receiver"     
    
    === Output ===
    xml output:
        xml file with all information.
    """
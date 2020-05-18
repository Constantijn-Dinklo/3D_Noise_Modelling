import fiona

def read_buildings(input_file,dictionary):
    """
    Explination:
    Input:
    Output:
    """
    with fiona.open(input_file) as layer:
        for feature in layer:
            bag_id = feature['properties']['bag_id']
            f_dict[bag_id] = { }
            z = feature['properties']['hoogte_abs']
            f_geom_coord = feature['geometry']['coordinates']
            for polygon_index in range(len(f_geom_coord)):
                polygon_object = f_geom_coord[polygon_index]
                ground = []
                for coord_index in range(len(polygon_object[:(len(polygon_object)-1)])):
                    coord_object = list(polygon_object[coord_index])
                    ground.append(coord_object)
                roof = []
                for coord_index in range(len(polygon_object[:(len(polygon_object)-1)])):
                    coord_object = list(polygon_object[coord_index])
                    coord_object[2] = z
                    roof.append(coord_object)
                walls = []
                for coord_index in range(len(polygon_object[:(len(polygon_object)-1)])):
                    a = list(polygon_object[coord_index])
                    b = list(polygon_object[coord_index+1])
                    c = b
                    c[2] = z
                    d = a
                    d[2] = z
                    wall = [a,b,c,d]
                    walls.append(wall) 
                f_dict[bag_id]['ground'] = ground
                f_dict[bag_id]['roof'] = roof
                f_dict[bag_id]['walls'] = walls
                # OBS. IF THE BUILDINGS ARE NOT PART OF THE SURFACE MODEL, WOULD IT BE NICE TO WRITE THEM AS AN OBJ?
                # I CAN EXPLAIN THIS THOUGHT LATER.
    layer.close()

def read_points(input_file,dictionary):
    """
    Explination:
    Input:
    Output:
    """
    with fiona.open(input_file) as layer:
        for feature in layer:
            source_id = feature['properties']['id']
            coord_object = list(feature['geometry']['coordinates'])
            dictionary[source_id] = coord_object
    layer.close()

def get_plane_equation(p1,p2,p3):
    pass

def get_mirror_point(p,plane):
    pass

def get_intersection_line_plane(line,plane):
    pass

def get_paths(degree_reflection):
    for receiver in r_dict:
        for source in s_dict:
            count_reflection = 0
            while count_reflection < degree_reflection:
                for bag_id in f_dict:
                    walls = f_dict[bag_id]['walls']
                    for wall in walls:
                        pass
                        # CALCULATE THE EQUATION OF THE PLANE CONTAINING THE WALL:
                        # CALCULATE THE IMAGE OF THE SOURCE POINT (S) IN RELATION TO THIS PLANE, I.E. (S')
                        # GET THE LINE CONNECTING S' AND THE RECEIVER (R):
                        # GET THE POINT INTERSECTING THE LINE S'R AND THE PLANE:
                        # THIS IS THE FIRST REFLECTION POINT (REF1)
                        # GET LINES (S-REF1) AND (REF1-R) AND COUNT_REFLECTION += 1
                        # STORE THESE LINES SO THEY CAN BE WRITTEN IN THE OUTPUT

def write_output(output_file):
    """
    Explination:
    Input:
    Output:
    """
    pass

if __name__ == "__main__":
    f_dict = { }
    s_dict = { }
    r_dict = { }
    read_buildings('file:///Users/denisgiannelli/Desktop/Buildings1.gpkg',f_dict)
    print()
    for key in f_dict:
        print('key')
        print(key)
        #print('ground')
        #print(f_dict[key]['ground'])
        #print('roof')
        #print(f_dict[key]['roof'])
        print('walls')
        for wall in f_dict[key]['walls']:
            print(wall)
        print()
    read_points('file:///Users/denisgiannelli/Desktop/Sources1.gpkg',s_dict)
    print(s_dict)
    print()
    read_points('file:///Users/denisgiannelli/Desktop/Receivers1.gpkg',r_dict)
    print(r_dict)
    print()
    get_paths(2)
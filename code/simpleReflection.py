import fiona
import math

def read_buildings(input_file,dictionary):
    """
    Explination:
    Input:
    Output:
    """
    with fiona.open(input_file) as layer:
        for feature in layer:
            bag_id = feature['properties']['bag_id']
            dictionary[bag_id] = { }
            z = feature['properties']['hoogte_abs']
            dictionary[bag_id]['hoogte_abs'] = z
            f_geom_coord = feature['geometry']['coordinates']
            for polygon_index in range(len(f_geom_coord)):
                polygon_object = f_geom_coord[polygon_index]
                walls = []
                for coord_index in range(len(polygon_object[:(len(polygon_object)-1)])):
                    a = list(polygon_object[coord_index])
                    b = list(polygon_object[coord_index+1])
                    wall_2D = [a[:len(a)-1],b[:len(b)-1]]
                    walls.append(wall_2D)
                dictionary[bag_id]['walls'] = walls
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
            dictionary[source_id] = coord_object[:len(coord_object)-1]
    layer.close()

def get_line_equation(p1,p2):
    """
    Explination:
    Input:
    Output:
    """
    # EQUATION OF A LINE IN THE 2D PLANE:
    # A * x + B * y + C = 0
    a = p2[1] - p1[1]
    b = -(p2[0] - p1[0])
    c = -a*p1[0] -b*p1[1]
    m = math.sqrt(a*a + b*b)
    a_norm = a/m
    b_norm = b/m
    c_norm = c/m
    # EQUATION OF A LINE IN THE 2D PLANE WITH NORMALISED (UNIT) NORMAL VECTORs:
    # A' * x + B' * y + C' = 0
    parameters = [a_norm,b_norm,c_norm]
    return parameters # THE PARAMETERS OF THE NORMALISED LINE.

def get_mirror_point(p1,parameters):
    """
    Explination:
    Input:
    Output:
    """
    # THE SIGNED DISTANCE D FROM P1 TO THE LINE L, I.E. THE ONE WITH THE PARAMETERS.
    d = parameters[0]*p1[0] + parameters[1]*p1[1] + parameters[2]
    p_mirror_x = p1[0] - 2*parameters[0]*d
    p_mirror_y = p1[1] - 2*parameters[1]*d
    return [p_mirror_x,p_mirror_y]

def get_intersection(line1,line2):
    """
    Explination:
    Input:
    Output:
    """
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       raise Exception('lines do not intersect')

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return [x,y]

def get_bbox(line):
    """
    Explination:
    Input:
    Output:
    """
    p1 = line[0]
    p2 = line[1]
    x_min = min(p1[0],p2[0])
    x_max = max(p1[0],p2[0])
    y_min = min(p1[1],p2[1])
    y_max = max(p1[1],p2[1])
    bbox = [x_min,x_max,y_min,y_max]
    return bbox

def get_paths(dictionary):
    """
    Explination:
    Input:
    Output:
    """
    for receiver in r_dict:
        for source in s_dict:
            r = r_dict[receiver]
            s = s_dict[source]
            for bag_id in f_dict:
                walls = f_dict[bag_id]['walls']
                for wall in walls:
                    s_mirror = get_mirror_point(s,get_line_equation(wall[0],wall[1]))
                    ref = get_intersection(wall,[s_mirror,r])
                    bbox = get_bbox(wall)
                    if ref[0] > bbox[0] and ref[0] < bbox[1] and ref[1] > bbox[2] and ref[1] < bbox[3]:
                        rays = [s,ref], [ref,r]

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
    p_dict = { }
    read_buildings('file:///Users/denisgiannelli/Desktop/Buildings1.gpkg',f_dict)
    print()
    for key in f_dict:
        print('key')
        print(key)
        print('hoogte_abs')
        print(f_dict[key]['hoogte_abs'])
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
    get_paths(p_dict)
    print()
    print(p_dict)
import fiona
import math
import misc
import numpy as np
import time

from shapely.geometry import shape, Point

class ReflectionPath:

    def __init__(self, source, receiver):
        self.source = source #A SourcePoint instance
        self.receiver = receiver #Receiver coordinates

        # now storing this here.
        self.reflection_points = []
        self.reflection_heights = []

    def get_mirror_point(self, line_parameters, point=False):
        """
        Explanation: A function that reads the self.source point and the parameters of a line and returns the mirror point of p1 regarding this line.
        ---------------
        Input:
        parameters: [a_norm(float),b_norm(float),c_norm(float)] - The a,b,c parameters of the normalised line equation.
        ---------------
        Output:
        p_mirror: [x(float),y(float)] - The image (virtual) point.
        """
        if point == False:
            point = self.source.source_coords

        # THE SIGNED DISTANCE D FROM P1 TO THE LINE L, I.E. THE ONE WITH THE PARAMETERS.
        d = line_parameters[0] * point[0] + line_parameters[1] * point[1] + line_parameters[2]
        p_mirror_x = point[0] - 2 * line_parameters[0] * d
        p_mirror_y = point[1] - 2 * line_parameters[1] * d
        return [p_mirror_x, p_mirror_y]

    def check_validity(self, building_id, building_manager, tin, reflection_point, building_height, minimal_height_difference):
        triangle_index_building = np.where(tin.attributes == building_id)
        triangle_index_building = triangle_index_building[0][0]
        #print("random tr index of building: {}".format(triangle_index_building))
        # find the triangle where the reflection point is in (it is on the line though.)
        reflection_triangle = tin.find_receiver_triangle(triangle_index_building, reflection_point)
        #print("correct tr of building: {}".format(tin.attributes[reflection_triangle]))

        # can be either on the building side, or on the outerside
        # If the triangle is on the inside, get the triangle on the outside
        if(tin.attributes[reflection_triangle] == building_id):
            #print("triangle is on inside")
            # the triangle is on the inside of the building
            # now get neighbor
            edges = (
                (tin.vts[tin.trs[reflection_triangle][0]], tin.vts[tin.trs[reflection_triangle][1]]),
                (tin.vts[tin.trs[reflection_triangle][1]], tin.vts[tin.trs[reflection_triangle][2]]),
                (tin.vts[tin.trs[reflection_triangle][2]], tin.vts[tin.trs[reflection_triangle][0]])
            )
            # find which edge intersects with the point.
            neighbor = -1
            for i, edge in enumerate(edges):
                # side the side test is very much close to 0, it is the right edge
                if(abs(misc.side_test(edge[0], edge[1], reflection_point)) < 0.05): neighbor = i
            assert(neighbor != -1)
            nbs = [5, 3, 4]
            reflection_triangle = tin.trs[reflection_triangle][nbs[neighbor]]

        #print("triangle type on outside: {}".format(tin.attributes[reflection_triangle]))
        # we should have the correct triangle at hand
        if(tin.attributes[reflection_triangle][0] == 'b'):
            #print("other triangle is building")
            # it is a building
            outside_building_height = building_manager.buildings[tin.attributes[reflection_triangle]].roof_level
            if(building_height - outside_building_height > minimal_height_difference):
                # building is atleast 20 centimeters higher then
                return True
            else:
                return False
        else:
            # not a building, so its fine (should be, there should not be buildings below ground level in the dataset)
            return True

    def check_relative_size(self, wall_segments, building, point):
        for wall_id in wall_segments:
            other_wall = building.walls[wall_id]
            intersection_point = misc.line_intersect(other_wall, [self.receiver, point])
            if intersection_point != False:    
                return True
        return False

    def get_first_order_reflection(self, building_manager, tin, minimal_height_difference, radius_buffer=2000):
        """
        Explanation: A function that reads a buildings_dict and computes all possible first-ORDER reflection paths,
        according to the receivers and sources that are provided from main.py
        ---------------
        Input:
        buildings_dict : BuildingManager object - stores all the building objects
        ---------------
        Output:
        Stores reflection points, and their corresponding heights in the class.
        return True if reflections are found, False if not
        """
        query_geom = Point(self.receiver).buffer(radius_buffer)  # 2000 m buffer around receiver
        chosen_buildings = building_manager.buildings_tree.query(query_geom)
        for chosen_building in chosen_buildings:
            building_id = building_manager.polygon_id_to_building_id[id(chosen_building)]
            building = building_manager.buildings[building_id]
            
            if building.underground:
                continue

            number_of_walls = len(building.walls)
            
            for wall_id, wall in enumerate(building.walls):
                test_r = misc.side_test(wall[0], wall[1], self.receiver)
                test_s = misc.side_test(wall[0], wall[1], self.source.source_coords)

                # COS: Not sure if this is actually true!!!!
                if test_r > 0 and test_s > 0:  # This statement guarantees that the source and receiver are both on the outer side of the wall
                    # Get the mirrored source over the wall segment
                    s_mirror = self.get_mirror_point(misc.parametric_line_equation(wall[0], wall[1]))
                    # find the intersection point, returns False is they do not intersect.
                    reflection_point = misc.line_intersect(wall, [s_mirror, self.receiver])
                    # ref is false if there is no reflection.
                    if reflection_point:
                        angle = 0.01745329252  # Hardcoded Angle in radians (1 degree or 2.pi / 360)

                        # take the mirror point and check if reflection path is longer than 2Km
                        receiver_array = np.array(self.receiver)
                        mirrored_source_array = np.array(s_mirror)

                        # check distance between reflection point and mirrored source
                        reflection_point_array = np.array(reflection_point)
                        dist = np.linalg.norm(reflection_point_array-mirrored_source_array)
                        if dist <= 2000:

                            # rotate the mirrored point 1 degree to the left and look for an intersection with the building
                            left_point = misc.get_rotated_point(receiver_array, mirrored_source_array, angle)
                            wall_adjusted_order_left = np.array(range(wall_id, number_of_walls + wall_id, 1)) % number_of_walls
                            is_left_valid = self.check_relative_size(wall_adjusted_order_left, building, left_point)

                            if is_left_valid:
                                # rotate the mirrored point 1 degree to the right and look for an intersection with the building
                                right_point = misc.get_rotated_point(receiver_array, mirrored_source_array, -angle)
                                wall_adjusted_order_right = np.array(range(number_of_walls + wall_id, wall_id, -1)) % number_of_walls
                                is_right_valid = self.check_relative_size(wall_adjusted_order_right, building, right_point)

                                if is_right_valid:
                                    # Check if reflection is valid, ie if there is no other taller building in front.
                                    if(self.check_validity(building_id, building_manager, tin, reflection_point, building.roof_level, minimal_height_difference)):
                                        # If the reflection object is of sufficient size, and the reflection is valid, store it
                                        self.reflection_points.append([reflection_point])
                                        self.reflection_heights.append([building.roof_level])

        if len(self.reflection_points) > 0:
            return True
        return False

# THE FUNCTIONS BELOW ARE NOT USED IN THE MAIN ALGORITHM AND WERE, THEREFORE, PUT OUTSIDE THE CLASS.
# SINCE IT IS INTERESING TO KEEP THEM AS A RECORD OF THE CODING PROCESS, ESPECIALLY FOR WRITING THE FINAL REPORT, THEY ARE STILL STORED HERE.

def get_closest_point(p1, parameters):
    # THIS FUNCTION IS OUT-OF-DATE, SINCE WE ARE NOT WORKING WITH SECOND ORDER REFLECTIONS ANYMORE.
    """
    Explanation: A function that reads a point and the parameters of a line and returns the closest point of p1 on this line.
    ---------------
    Input:
    p1: [x(float),y(float)] - The object point.
    parameters: [a_norm(float),b_norm(float),c_norm(float)] - The a,b,c parameters of the normalised line equation.
    ---------------
    Output:
    p_line: [x(float),y(float)] - The closest point of p1 that lies on the line segment.
    """

    """
    # THE SIGNED DISTANCE D FROM P1 TO THE LINE L, I.E. THE ONE WITH THE PARAMETERS.
    d = parameters[0]*p1[0] + parameters[1]*p1[1] + parameters[2]
    p_line_x = p1[0] - parameters[0]*d
    p_line_y = p1[1] - parameters[1]*d
    return [p_line_x,p_line_y]
    """

def split_lineseg_n(n, lineseg):
    # THIS FUNCTION IS OUT-OF-DATE, SINCE WE ARE NOT WORKING WITH SECOND ORDER REFLECTIONS ANYMORE.
    """
    Explanation: A function that takes a line segment and splits it into multiple sub-segments, according to a specific number.
    ---------------
    Input:
    n: int - the number of line sub-segments in which lineseg will be divided into
    lineseg: [[x1(float),y1(float)],[xn(float),yn(float)]] - the line segment in matter
    ---------------
    Output:
    ref_list: [[x1(float),y1(float)],[x2(float),y2(float)],[x3(float),y3(float)].....[xn(float),yn(float)]] - a list of all vertices
    of lineseg (polyline), including the two outermost and original ones.
    """

    """
    delta_x = lineseg[1][0] - lineseg[0][0] # delta_x can be positive, negative or zero, depending on the direction of the line.
    delta_y = lineseg[1][1] - lineseg[0][1] # delta_x can be positive, negative or zero, depending on the direction of the line.
    vertex = lineseg[0]
    ref_list = [vertex]
    for number in range(n):
        x = vertex[0] + delta_x/n
        y = vertex[1] + delta_y/n
        vertex = [x,y]
        ref_list.append(vertex)
    return ref_list
    """

def split_lineseg_dim(dim, lineseg):
    # THIS FUNCTION IS OUT-OF-DATE, SINCE WE ARE NOT WORKING WITH SECOND ORDER REFLECTIONS ANYMORE.
    """
    Explanation: A function that takes a line segment and splits it into multiple sub-segments, each one of them with lenght = 'dim'
    ---------------
    Input:
    dim: float - the length of each sub-segment in which lineseg will be divided into
    lineseg: [[x1(float),y1(float)],[xn(float),yn(float)]] - the line segment in matter
    ---------------
    Output:
    ref_list: [[x1(float),y1(float)],[x2(float),y2(float)],[x3(float),y3(float)].....[xn(float),yn(float)]] - a list of all vertices
    of lineseg (polyline), including the two outermost and original ones.
    """

    """
    delta_x = lineseg[1][0] - lineseg[0][0]
    delta_y = lineseg[1][1] - lineseg[0][1]
    length = math.sqrt(delta_x**2 + delta_y**2)
    n = math.floor(length//dim)
    ref_list = [lineseg[0]]
    for number in range(n):
        h = (number+1)*dim
        x = ((h * delta_x) / length) + lineseg[0][0]
        y = ((h * delta_y) / length) + lineseg[0][1]
        inter = [x,y]
        ref_list.append(inter)
    if ref_list[(len(ref_list)-1)] == lineseg[1]:
        pass
    else:
        ref_list.append(lineseg[1])
    return ref_list
    """

def get_candidate_point(dim):
    # THIS FUNCTION IS OUT-OF-DATE, SINCE WE ARE NOT WORKING WITH SECOND ORDER REFLECTIONS ANYMORE.
    """
    Explanation: A function that gets all the walls from f_dict and create candidate reflection points.
    ---------------
    Input:
    dim: int - lenght of the segments in which the wall will be divided into.
    ---------------
    Output:
    void
    """

    """
    for bag_id in f_dict:
        h_dak = f_dict[bag_id]['h_dak']
        walls = f_dict[bag_id]['walls']
        for wall in walls:
            ref_list = self.split_lineseg_dim(dim,wall)
            for point in ref_list:
                point.append(h_dak)
                candidate = [wall[0],point,wall[1]]
                c_list.append(candidate)
    """

def get_second_order_reflection(s, r, t):
    # THIS FUNCTION IS OUT-OF-DATE, SINCE WE ARE NOT WORKING WITH SECOND ORDER REFLECTIONS ANYMORE.
    """
    Explanation: A function that reads a source point and a receiver and computes all possible SECOND-ORDER reflection paths,
    according to buildings that are stored in f_dict (separate dictionary)
    ---------------
    Input:
    s: [x(float),y(float),(z)(float)] - source point.
    r: [x(float),y(float),(z)(float)] - receiver point.
    threshold t: float - the threshold distance from the receiver.
    ---------------
    Output:
    A list of all (independent) point lists that are capable of reflecting the sound wave from source to receiver.:
    l = [ [ [p11, p12], [p21, p22], [p31, p32], .... [pn1, pn2] ] , [ [h11, h12], [h21, h22], [h31, h32], .... [hn1, hn2] ]
    such that:
    pn(1)(2) = coordinates of the reflection point [x(float),y(float)]
    hn = height value of the building in which the reflection point lies into (float)
    the n-th element of "p_list" corresponds to the n-th element of "h_list".
    """

    """
    coords   = [ ]
    heights  = [ ]
    for candidate in c_list:
        for bag_id in f_dict:
            h_dak = f_dict[bag_id]['h_dak']
            walls = f_dict[bag_id]['walls']
            for wall in walls:
                test_c = misc.side_test( wall[0], wall[1], candidate[1][:2]) #r[:2] makes the function to ignore an eventual 'z' value.
                test_s = misc.side_test( wall[0], wall[1], s[:2]) #s[:2] makes the function to ignore an eventual 'z' value.
                if test_c > 0 and test_s > 0: # This statement guarantees that S-REF and REF-CANDIDATE are entirely outside the polygon.
                    s_mirror = self.get_mirror_point(s,self.get_parametric_line_equation(wall[0],wall[1]))
                    b = self.line_intersect(wall,[s_mirror,candidate[1][:2]])
                    if type(b) == list:
                        test_b = misc.side_test( candidate[0], candidate[2], b[:2])
                        test_r = misc.side_test( candidate[0], candidate[2], r[:2])
                        if test_b > 0 and test_r > 0:
                            b_mirror = self.get_mirror_point(b,self.get_parametric_line_equation(candidate[0], candidate[2]))
                            dist = math.sqrt(((b_mirror[0]-candidate[1][0])**2)+((b_mirror[1]-candidate[1][1])**2))
                            if dist > 0.1:
                                if abs(misc.side_test( b_mirror, candidate[1][:2], r)) <= t:
                                    # GET CLOSEST POINT FROM R TO B_MIRROR_CANDIDATE[1]
                                    r_closest = self.get_closest_point(r,(self.get_parametric_line_equation(b_mirror,candidate[1])))
                                    r_closest.append(r[2])
                                    coords.append([b,candidate[1][:2]])
                                    heights.append([h_dak,candidate[1][2]])
                                    b_z = b
                                    b_z.append(h_dak)
                                    p2_list.append([s,b_z,candidate[1],r_closest])
    print('2nd-order reflection. numer of paths:',len(coords))
    return [ coords, heights ] #[ [ [p11, p12], [p21, p22], .... [pn1, pn2] ] , [ [h11, h12], [h21, h22], .... [hn1, hn2] ]
    """

def read_buildings(input_file):
    # THIS FUNCTION IS OUT-OF-DATE, SINCE WE ARE NOT WORKING WITH SECOND ORDER REFLECTIONS ANYMORE.
    # ATTENTION: THE CONTENT OF THIS FUNCTION HAS BEEN PLACED IN MAIN.PY AND BUILDINGMANAGER.PY
    """
    Explanation: A function that reads footprints and stores all walls as [p1,p2] and absolute heights (float) of these.
    ---------------
    Input:
    input_file: a .gpkg file containing the footprints of the buildings.
    dictionary: an empty 'f_dict' dictionary in __main__
    ---------------
    Output:
    void.
    """

    """
    dictionary = {}
    with fiona.open(input_file) as layer:
        for feature in layer:
            bag_id = feature['properties']['bag_id']
            dictionary[bag_id] = { }
            z = feature['properties']['h_dak']
            dictionary[bag_id]['h_dak'] = z
            f_geom_coord = feature['geometry']['coordinates']
            f_geom_type = feature['geometry']['type']
            if f_geom_type == 'Polygon':
                for polygon_index in range(len(f_geom_type)):
                    polygon_object = f_geom_type[polygon_index]
                    walls = []
                    for coord_index in range(len(polygon_object[:(len(polygon_object)-1)])):
                        a = list(polygon_object[coord_index])
                        b = list(polygon_object[coord_index+1])
                        wall_2D = [a[:len(a)-1],b[:len(b)-1]]
                        walls.append(wall_2D)
                    dictionary[bag_id]['walls'] = walls
            if f_geom_type == 'MultiPolygon':
                for multi_polygon_index in range(len(f_geom_coord)):
                    multi_polygon_object = f_geom_coord[multi_polygon_index]
                    for polygon_index in range(len(multi_polygon_object)):
                        polygon_object = multi_polygon_object[polygon_index]
                        walls = []
                        for coord_index in range(len(polygon_object[:(len(polygon_object)-1)])):
                            a = list(polygon_object[coord_index])
                            b = list(polygon_object[coord_index+1])
                            wall_2D = [a[:len(a)-1],b[:len(b)-1]]
                            walls.append(wall_2D)
                        dictionary[bag_id]['walls'] = walls
    return dictionary
    """

def read_points(input_file, dictionary):
    # THIS FUNCTION IS OUT-OF-DATE, SINCE WE ARE NOT WORKING WITH SECOND ORDER REFLECTIONS ANYMORE.
    """
    Explanation: A function that reads points and store their ids (int) and coordinates as [x,y].
    ---------------
    Input:
    input_file: a .gpkg file containing the points (with z coordinates)
    dictionary: an empty dictionary in __main__ (either s_dict for sources or r_dict for receivers)
    ---------------
    Output:
    void.
    """

    """
    with fiona.open(input_file) as layer:
        for feature in layer:
            source_id = feature['properties']['id']
            p_geom_type = feature['geometry']['type']
            p_geom_coord = feature['geometry']['coordinates']
            if p_geom_type == 'Point':
                coord_obj = list(p_geom_coord)
            if p_geom_type == 'MultiPoint':
                for point in p_geom_coord:
                    coord_obj = list(point)
            dictionary[source_id] = coord_obj
    layer.close()
    """

def write_candidates(output_file, lista):
    # THIS FUNCTION IS OUT-OF-DATE, SINCE WE ARE NOT WORKING WITH SECOND ORDER REFLECTIONS ANYMORE.
    """
    Explanation: A function that writes a CSV file with all candidate points. It is used for visualising these points in QGIS.
    ---------------
    Input:
    output_file: the directory/name of the csv file to be created.
    lista: a list containing all candidate points in the following schema:
    [candidate_x, candidate_y, h_dak]
    ---------------
    Output:
    void.
    """

    """
    fout = open(output_file,'w')
    line = 'fid \t geometry \n'
    fout.write(str(line))
    count = 0
    for candidate in lista:
        count += 1
        line = '%d \t PointZ (%f %f %f) \n' % (count,candidate[1][0],candidate[1][1],candidate[1][2])
        fout.write(line)
    fout.close()
    #PointZ (93539.68248698 441892 1.4)
    """

def write_output_1st(output_file, lista):
    # THIS FUNCTION IS OUT-OF-DATE, SINCE WE ARE NOT WORKING WITH SECOND ORDER REFLECTIONS ANYMORE.
    """
    Explanation: A function that writes a CSV file with the reflected paths. It is used for visualising the paths in QGIS.
    ---------------
    Input:
    output_file: the directory/name of the csv file to be created.
    lista: a list containing all the 1st order propagation paths in the following schema:
    [ [source_x, source_y, source_z,] , [reflection_x, reflection_y, h_dak], [receiver_x, receiver_y, receiver_z] ]
    ---------------
    Output:
    void.
    """

    """
    fout = open(output_file,'w')
    line = 'fid \t geometry \n'
    fout.write(str(line))
    count = 0
    for path in lista:
        count += 1
        sou = path[0]
        ref = path[1]
        rec = path[2]
        line = '%d \t MultiLineStringZ ((%f %f %f, %f %f %f, %f %f %f)) \n' % (count,sou[0],sou[1],sou[2],ref[0],ref[1],0,rec[0],rec[1],rec[2]) 
        fout.write(line)
    fout.close()
    #MultiLineStringZ ((93528.02305619 441927.11005859 2.5, 93567.67848824 441908.81858497 0, 93539.68248698 441892 1.4))
    """

def write_output_2nd(output_file, lista):
    # THIS FUNCTION IS OUT-OF-DATE, SINCE WE ARE NOT WORKING WITH SECOND ORDER REFLECTIONS ANYMORE.
    """
    Explanation: A function that writes a CSV file with the reflected paths. It is used for visualising the paths in QGIS.
    ---------------
    Input:
    output_file: the directory/name of the csv file to be created.
    lista: a list containing all the 1st order propagation paths in the following schema:
    [ [source_x, source_y, source_z,] , [b_ref_x, b_ref_y, b_ref_z], [c_ref_x, c_ref_y, c_ref_z], [receiver_x, receiver_y, receiver_z] ]
    ---------------
    Output:
    void.
    """

    """
    fout = open(output_file,'w')
    line = 'fid \t geometry \n'
    fout.write(str(line))
    count = 0
    for path in lista:
        # path = [s,b_z,candidate,r]
        count += 1
        sou =   path[0]
        b_ref = path[1]
        c_ref = path[2]
        rec =   path[3]
        line = '%d \t MultiLineStringZ ((%f %f %f, %f %f %f, %f %f %f, %f %f %f)) \n' % (count,sou[0],sou[1],sou[2],b_ref[0],b_ref[1],b_ref[2],c_ref[0],c_ref[1],c_ref[2],rec[0],rec[1],rec[2]) 
        fout.write(line)
    fout.close()
    #MultiLineStringZ ((93528.02305619 441927.11005859 2.5, 93567.67848824 441908.81858497 0, 93539.68248698 441892 1.4))
    """

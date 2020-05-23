import misc
import numpy as np
import sys
import fiona

from scipy.spatial import ConvexHull
from shapely.geometry import shape, Polygon, LineString, Point
from shapely.ops import transform
from scipy.spatial import KDTree
from time import time


class GroundTin:

    def __init__(self, vts, trs, attr = []):
        self.vts = np.array(vts)
        self.trs = np.array(trs)
        self.attributes = np.array(attr)
        
        self.kd_vts = KDTree(self.vts)

        self.bounding_box_2d = [100000000, 100000000, -100000000, -100000000]
        self.bounding_box_3d = [100000000, 100000000, 100000000, -100000000, -100000000, -100000000]

    def orient_tin(self):
        """
        Explination: Makes sure all the triangles are counter-clockwise when viewing the ground from above
        ---------------
        Input: void
        ---------------
        Output: void
        """

        for i in range(0, len(self.trs)):
            triangle = self.trs[i]

            v0 = self.vts[triangle[0]]
            v1 = self.vts[triangle[1]]
            v2 = self.vts[triangle[2]]

            test_triangle = [v0, v1, v2]

            normal_vector = misc.normal_of_triangle(test_triangle)

            if normal_vector[2] <= 0:
                self.flip_triangle(i)

    def point_in_triangle(self, pt, tr):
        """
        Explanation: Do a side test for all edges with the pt, if they are all positive.
        ---------------
        Input:
        pt : [x,y,z] - The point to check.
        tr : integer - triangle ID.
        ---------------
        Output:
            Boolean - True if the point is inside the triangle.
        """
        e = 10 ** (-8)
        d1 = misc.side_test(self.vts[self.trs[tr][0]], self.vts[self.trs[tr][1]], pt)
        d2 = misc.side_test(self.vts[self.trs[tr][1]], self.vts[self.trs[tr][2]], pt)
        d3 = misc.side_test(self.vts[self.trs[tr][2]], self.vts[self.trs[tr][0]], pt)

        if d1 >= -e and d2 >= -e and d3 >= -e:
            return True  # the point is in the triangle
        else:
            return False

    def flip_triangle(self, triangle_index):
        """
        Explination: Flips the triangle's orientation
        ---------------
        Input: 
            triangle_index - The index of the triangle that needs to be flipped
        ---------------
        Output: void
        """
        temp_incident = self.trs[triangle_index][3]
        temp_vertex = self.trs[triangle_index][0]

        self.trs[triangle_index][0] = self.trs[triangle_index][2]
        self.trs[triangle_index][3] = self.trs[triangle_index][5]

        self.trs[triangle_index][2] = temp_vertex
        self.trs[triangle_index][5] = temp_incident

    def find_receiver_triangle(self, tr_init, p_receiver):
        """
        Explanation: Find the trinagle in which the p_source is located, by means of walking from tr_init to the right triangle
        ---------------
        Input:
            tr_init : integer - An (arbitrary) triangle id to start from.
            p_receiver : [x,y,z] - The receiver point.
        ---------------
        Output:
            integer - triangle id of triangle underneath source point
        """
        print("=== find_receiver_triangle ===")
        tr = tr_init
        for i in range(1000):  # max 1000 triangles to walk.
            # do the side test for all sides, returns the value
            d1 = misc.side_test(self.vts[self.trs[tr][0]], self.vts[self.trs[tr][1]], p_receiver)
            d2 = misc.side_test(self.vts[self.trs[tr][1]], self.vts[self.trs[tr][2]], p_receiver)
            d3 = misc.side_test(self.vts[self.trs[tr][2]], self.vts[self.trs[tr][0]], p_receiver)

            # If all side_tests are positive (point is either exactly on the edge, or on the inside)
            if d1 >= 0 and d2 >= 0 and d3 >= 0:
                return tr
            # when one the the tests returns negative, we have to go to the next triangle,
            # first find the direction to go to:
            # turn it into a list, and get the minimum
            d = [d1, d2, d3]
            d_min = d.index(min(d))

            # find the right neighbouring triangle to go to.
            nbs = [5, 3, 4]
            nb_index = nbs[d_min]

            # get the index of the neighbour triangle
            tr = self.trs[tr][nb_index]
        print("no tr found after 1000 loops")

    def cross_section_total(self, receiver, source, tr_receiver, buildings):
        """
        Explanation: Finds cross-section while walking to the source point
        ---------------
        Input:
            receiver : (x,y,z) - the receiver point we walk from
            source : (x,y,z) - the source point we want to walk to
            tr_receiver : integer - triangle id of triangle underneath receiver point
            buildings : Fiona's Collection where each record/building holds a 'geometry' and a 'property' key
        ---------------
        Output:
            list of vertices - defining the cross-section
        """
        print("=== cross_section ===")
        check_tr = tr_receiver
        # the first vertex is the receiver projected into its triangle
        receiver_height = self.interpolate_triangle(receiver_tr, receiver)
        cross_section_vertices = [[(receiver[0], receiver[1], receiver_height), self.tr_mtls[check_tr]]]
        nbs = [5, 3, 4]
        count = 0
        while not self.point_in_triangle(source, check_tr):
            assert (check_tr != -1)
            edges = [(self.trs[check_tr][0], self.trs[check_tr][1]),
                     (self.trs[check_tr][1], self.trs[check_tr][2]),
                     (self.trs[check_tr][2], self.trs[check_tr][0])]
            for i, edge in enumerate(edges):
                if (misc.side_test(receiver, source, self.vts[edge[0]]) <= 0 and
                        misc.side_test(receiver, source, self.vts[edge[1]]) >= 0):
                    # get intersection point between edge and receiver-source segment
                    inter_pt = self.intersection_point(edge, source, receiver)
                    # Check if the new calculated point is not too close to the previously added point, in MH distance
                    if np.sum(cross_section_vertices[-1][0] - inter_pt) < 0.1:
                        print("points are too close, nothing to add")
                        check_tr = self.trs[check_tr][nbs[i]]
                        break
                    # Check if there are any building intersection
                    else:
                        inter_pt = tuple(inter_pt)
                        current_tr_mtl = self.tr_mtls[check_tr]
                        current_bldg = self.tr_bldgs.get(check_tr, -1)
                        check_tr = self.trs[check_tr][nbs[i]]
                        next_bldg = self.tr_bldgs.get(check_tr, -1)
                        next_tr_mtl = self.tr_mtls[check_tr]
                        if current_bldg == -1 and next_bldg == -1:  # don't use the mtl because maybe later there will be != mtl for bldgs
                            cross_section_vertices.append([inter_pt, next_tr_mtl])
                            break
                        else:
                            if count == 0:
                                '''next_build_info = buildings.get(next_bldg)
                                next_h_bldg = build_info['properties']['h_dak']'''
                                next_h_bldg = buildings[next_bldg]
                                if next_h_bldg > inter_pt[2]:
                                    cross_section_vertices.append([inter_pt, next_tr_mtl])
                                    cross_section_vertices.append([(inter_pt[0], inter_pt[1], next_h_bldg),
                                                                   next_tr_mtl])
                                    count = 1
                                    break
                                else:
                                    print("Roof height is lower than ground height, for building ", next_bldg)
                                    break
                            else:
                                '''build_info = buildings.get(current_bldg)
                                current_h_bldg = build_info['properties']['h_dak']'''
                                current_h_bldg = buildings[current_bldg]
                                if current_h_bldg > inter_pt[2] and next_bldg != -1:
                                    '''next_build_info = buildings.get(next_bldg)
                                    next_h_bldg = build_info['properties']['h_dak']'''
                                    next_h_bldg = buildings[next_bldg]
                                    # no collinear horizontal points
                                    if current_tr_mtl == next_tr_mtl and current_h_bldg == next_h_bldg:
                                        break
                                    # no collinear vertical points
                                    else:
                                        cross_section_vertices.append([(inter_pt[0], inter_pt[1], current_h_bldg),
                                                                       current_tr_mtl])
                                        cross_section_vertices.append([(inter_pt[0], inter_pt[1], next_h_bldg),
                                                                       next_tr_mtl])
                                        break
                                # down back to DTM
                                elif current_h_bldg > inter_pt[2] and next_bldg == -1:
                                    cross_section_vertices.append([(inter_pt[0], inter_pt[1], current_h_bldg),
                                                                   current_tr_mtl])
                                    cross_section_vertices.append([inter_pt, next_tr_mtl])
                                    count = 0
                                    break
                                else:
                                    print("Roof height is lower than ground height, for building ", current_bldg)
                                    break
        source_tr = check_tr
        source_height = self.interpolate_triangle(source_tr, source)
        source_tr_mtl = self.tr_mtls[source_tr]
        cross_section_vertices.append([(source[0], source[1], source_height), source_tr_mtl])
        cross_section_vertices.reverse()
        return cross_section_vertices

    def intersection_point(self, edge, source, receiver):
        """
        Explanation:
        ---------------
        Input:
        edge: (vi, vj) - vi is the index of a vertex in the vertex list
        source: (x,y,z) - the source point we want to walk to
        receiver: (x,y,z) - the receiver point we walk from
        ---------------
        Output:
        np.array((x,y,z)) - intersection between edge and receiver-source segment
        """
        vertex_right = np.array(self.vts[edge[0]])
        vertex_left = np.array(self.vts[edge[1]])

        # get the absolute area of the 2* the triangle (the rectangle of length from source to receiver and width the perpendicular distance to point p)
        area_right = abs(misc.side_test(receiver, source, vertex_right))
        area_left = abs(misc.side_test(receiver, source, vertex_left))

        # find where on the line (percentile) the cross section is.
        part_right = area_right / (area_left + area_right)

        # take vertex_right and append a part of the vector from right to left to it
        intersection_point = vertex_right + (vertex_left - vertex_right) * part_right

        return intersection_point

    def interpolate_triangle(self, tr, pt):
        """
        Explanation:
        Find the interpolated height in a triangle
        ---------------
        Input:
        tr: id of the triangle
        pt: point inside the triangle [x,y,z]
        ---------------
        Output:
        interpolated value
        """
        v1 = self.vts[self.trs[tr][0]]
        v2 = self.vts[self.trs[tr][1]]
        v3 = self.vts[self.trs[tr][2]]

        w1 = ((v2[1] - v3[1]) * (pt[0] - v3[0]) + (v3[0] - v2[0]) * (pt[1] - v3[1])) / (
                (v2[1] - v3[1]) * (v1[0] - v3[0]) + (v3[0] - v2[0]) * (v1[1] - v3[1]))
        w2 = ((v3[1] - v1[1]) * (pt[0] - v3[0]) + (v1[0] - v3[0]) * (pt[1] - v3[1])) / (
                (v2[1] - v3[1]) * (v1[0] - v3[0]) + (v3[0] - v2[0]) * (v1[1] - v3[1]))
        w3 = 1 - w1 - w2

        return w1 * v1[2] + w2 * v2[2] + w3 * v3[2]

    def get_2d_convex_hull(self):
        """
        Explination: Get the 2d convex hull of this tin.
        ---------------
        Input: void
        ---------------
        Output:
            convex_hull : ConvexHull - The 2d convex hull of this tin.
        """
        points_2d = self.vts[:, :2]
        convex_hull = ConvexHull(points_2d)
        return convex_hull

    def get_3d_convex_hull(self):
        """
        Explination: Get the 3d convex hull of this tin.
        ---------------
        Input: void
        ---------------
        Output:
            convex_hull : ConvexHull - The 3d convex hull of this tin.
        """
        convex_hull = ConvexHull(self.vts)
        return convex_hull

    def get_2d_bounding_box(self):
        """
        Explination: Get the 2d bounding box of this tin.
        ---------------
        Input: void
        ---------------
        Output:
            bounding_box : [min_x, min_y, max_x, max_y] - The 2d bounding box of this tin.
        """
        return self.bounding_box_2d

    def get_3d_bounding_box(self):
        """
        Explination: Get the 3d bounding box of this tin.
        ---------------
        Input: void
        ---------------
        Output:
            bounding_box : [min_x, min_y, min_z, max_x, max_y, max_z] - The 3d bounding box of this tin.
        """
        return self.bounding_box_3d

    @staticmethod
    def read_from_obj(file_path, orientation_check=True):
        """
        Explination: Read an obj file and make a tin from it.
        ---------------
        Input:
            file_path : string - The path to the obj file.
            orientation_check : Boolean - Set whether to check the orientation of all triangles after reading the file.
        ---------------
        Output:
            ground_tin : GroundTin - The tin that was created from the obj file input.
        """
        print("=== read_from_obj, connect triangles, create GroundTin object ===")
        vertices = []
        triangles = []

        min_values = [100000000, 100000000, 100000000]
        max_values = [-100000000, -100000000, -100000000]

        # Read the file and store all the vertices and triangles
        with open(file_path, 'r') as input_file:

            lines = input_file.readlines()

            for line in lines:
                line_elements = line.split(' ')
                if line_elements[0] == 'v':
                    x = float(line_elements[1])
                    y = float(line_elements[2])
                    z = float(line_elements[3])
                    vertex = [x, y, z]
                    vertices.append(vertex)
                    for i in range(0, 3):
                        if vertex[i] < min_values[i]:
                            min_values[i] = vertex[i]
                        if vertex[i] > max_values[i]:
                            max_values[i] = vertex[i]

                if line_elements[0] == 'f':
                    v1 = int(line_elements[1]) - 1
                    v2 = int(line_elements[2]) - 1
                    v3 = int(line_elements[3]) - 1
                    triangle = [v1, v2, v3, -1, -1, -1]
                    triangles.append(triangle)

        # Loop through all triangles, finding all triangles adjacent to it
        index = 0
        for triangle in triangles:
            # print("Index: " + str(index))
            v1 = triangle[0]
            v2 = triangle[1]
            v3 = triangle[2]
            i1 = triangle[3]
            i2 = triangle[4]
            i3 = triangle[5]

            # Check to make sure this triangle hasn't already been completely classified
            if (i1 != -1) and (i2 != -1) and (i3 != -1):
                index = index + 1
                continue

            for i in range(index + 1, len(triangles)):
                # print("Checking against triangle: " + str(i))
                adj_traingle = triangles[i]
                tri_vertices = adj_traingle[:3]

                if v1 == tri_vertices[0]:
                    if v2 == tri_vertices[1]:
                        triangle[5] = i
                        triangles[i][5] = index
                    if v2 == tri_vertices[2]:
                        triangle[5] = i
                        triangles[i][4] = index
                    if v3 == tri_vertices[1]:
                        triangle[4] = i
                        triangles[i][5] = index
                    if v3 == tri_vertices[2]:
                        triangle[4] = i
                        triangles[i][4] = index
                elif v1 == tri_vertices[1]:
                    if v2 == tri_vertices[0]:
                        triangle[5] = i
                        triangles[i][5] = index
                    if v2 == tri_vertices[2]:
                        triangle[5] = i
                        triangles[i][3] = index
                    if v3 == tri_vertices[0]:
                        triangle[4] = i
                        triangles[i][5] = index
                    if v3 == tri_vertices[2]:
                        triangle[4] = i
                        triangles[i][3] = index
                elif v1 == tri_vertices[2]:
                    if v2 == tri_vertices[0]:
                        triangle[5] = i
                        triangles[i][4] = index
                    if v2 == tri_vertices[1]:
                        triangle[5] = i
                        triangles[i][3] = index
                    if v3 == tri_vertices[0]:
                        triangle[4] = i
                        triangles[i][4] = index
                    if v3 == tri_vertices[1]:
                        triangle[4] = i
                        triangles[i][3] = index
                elif v2 == tri_vertices[0]:
                    if v3 == tri_vertices[1]:
                        triangle[3] = i
                        triangles[i][5] = index
                    if v3 == tri_vertices[2]:
                        triangle[3] = i
                        triangles[i][4] = index
                elif v2 == tri_vertices[1]:
                    if v3 == tri_vertices[0]:
                        triangle[3] = i
                        triangles[i][5] = index
                    if v3 == tri_vertices[2]:
                        triangle[3] = i
                        triangles[i][3] = index
                elif v2 == tri_vertices[2]:
                    if v3 == tri_vertices[0]:
                        triangle[3] = i
                        triangles[i][4] = index
                    if v3 == tri_vertices[1]:
                        triangle[3] = i
                        triangles[i][3] = index

            index = index + 1

        ground_tin = GroundTin(vertices, triangles)
        ground_tin.bounding_box_2d = [min_values[0], min_values[1], max_values[0], max_values[1]]
        ground_tin.bounding_box_3d = [min_values[0], min_values[1], min_values[2], max_values[0], max_values[1],
                                      max_values[2]]

        if orientation_check:
            ground_tin.orient_tin()

        return ground_tin

    def write_to_obj(self, file_path):
        """
        Explination: Writes out the tin to an obj file.
        ---------------
        Input:
            file_path : string - The path to the obj file we want to write to.
        ---------------
        Output: void
        """
        with open(file_path, 'w+') as output_file:
            for vertex in self.vts:
                vertex_str = "v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n"
                output_file.write(vertex_str)

            for triangle in self.trs:
                triangle_str = "f " + str(triangle[0] + 1) + " " + str(triangle[1] + 1) + " " + str(
                    triangle[2] + 1) + "\n"
                output_file.write(triangle_str)

    def write_to_objp(self, file_path):
        """
        Explination: Writes out the tin to an objp file.
        ---------------
        Input:
            file_path : string - The path to the obj file we want to write to.
        ---------------
        Output: void
        """

        with open(file_path, 'w+') as output_file:
            for vertex in self.vts:
                vertex_str = "v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n"
                output_file.write(vertex_str)

            for triangle in self.trs:
                triangle_str = "f " + str(triangle[0] + 1) + " " + str(triangle[1] + 1) + " " + str(
                    triangle[2] + 1) + " " + str(triangle[3] + 1) + " " + str(triangle[4] + 1) + " " + str(
                    triangle[5] + 1) + "\n"
                output_file.write(triangle_str)


#@staticmethod
def read_from_objp(file_path):
    """
    Explination: Read an objp file and make a tin from it.
    ---------------
    Input:
        file_path : string - The path to the obj file.
    ---------------
    Output:
        ground_tin : GroundTin - The tin that was created from the obj file input.
    """

    vertices = []
    triangles = []
    attributes = []

    min_values = [100000000, 100000000, 100000000]
    max_values = [-100000000, -100000000, -100000000]

    total_list_create_time = 0
    total_class_create_time = 0

    # Read the file and store all the vertices and triangles
    with open(file_path, 'r') as input_file:

        lines = input_file.readlines()

        for line in lines:
            line_elements = line.split(' ')
            if line_elements[0] == 'v':
                x = float(line_elements[1])
                y = float(line_elements[2])
                z = float(line_elements[3])
                vertex = [x, y, z]
                vertices.append(vertex)
                for i in range(0, 3):
                    if vertex[i] < min_values[i]:
                        min_values[i] = vertex[i]
                    if vertex[i] > max_values[i]:
                        max_values[i] = vertex[i]

            if line_elements[0] == 'f':
                v1 = int(line_elements[1]) - 1
                v2 = int(line_elements[2]) - 1
                v3 = int(line_elements[3]) - 1
                a1 = int(line_elements[4]) - 1
                a2 = int(line_elements[5]) - 1
                a3 = int(line_elements[6]) - 1

                triangle = [v1, v2, v3, a1, a2, a3]
                triangles.append(triangle)
            
            if line_elements[0] == 'a':
                attribute = float(line_elements[1])

                attributes.append(attribute)
    
    ground_tin = GroundTin(vertices, triangles, attributes)
    ground_tin.bounding_box_2d = [min_values[0], min_values[1], max_values[0], max_values[1]]
    ground_tin.bounding_box_3d = [min_values[0], min_values[1], min_values[2], max_values[0], max_values[1],
                                    max_values[2]]

    return ground_tin



if __name__ == "__main__":
    # run in commandline = python groundTin.py ./input/sample.obj
    tin_filename = sys.argv[1]

    # Create a
    # ground_tin_result = GroundTin.read_from_obj("input/isolated_cubes.obj")
    # ground_tin_resultp = GroundTin.read_from_objp("input/isolated_cubes.objp")

    start = time()
    ground_tin_result = read_from_objp(tin_filename)
    time_1 = time()
    print("runtime reading obj: {:.2f} seconds".format(time_1 - start))

    #convex_hull = ground_tin_result.get_2d_convex_hull()
    #print(convex_hull)

    #Setup dummy source and receiver points
    #source = [0.75, 0.1, 0]
    #receiver = [8.25, 0.9, 0]

    #Setup dummy source and receiver points
    #source = [93512.5, 441865, 3]
    #receiver = [93612.2, 441885.4, 2]

    #building_filename = sys.argv[2]
    #build = fiona.open(building_filename)

    # build = fiona.open(r"C:\Users\Nadine\Desktop\Nad\TU delft\Q4\GEO1101\3d_geo_data\lod13\lod13.shp")
    # t_00 = build.get(100)

    # dsm test
    '''triangles = np.array([[0, 2, 1, 1, -1, -1],
                          [1, 2, 3, 2, -1, 0],
                          [2, 4, 3, 3, 1, -1],
                          [3, 4, 5, 4, -1, 2],
                          [4, 6, 5, 5, 3, -1],
                          [5, 6, 7, 6, -1, 4],
                          [6, 8, 7, 7, 5, -1],
                          [7, 8, 9, -1, -1, 6]])

    vertices = np.array([[0, 0, 0],
                         [1, 1, 1],
                         [2, 0, 1],
                         [3, 1, 0],
                         [4, 0, 1],
                         [5, 1, 1],
                         [6, 0, 0],
                         [7, 1, 1],
                         [8, 0, 0],
                         [9, 1, 0]])

    ground_type = ['C', 'A0', 'A0', 'G', 'C', 'G', 'C', 'G']
    assoc_building = {1: 0, 2: 1}

    ground_tin_result = GroundTin(vertices, triangles, ground_type, assoc_building)'''

    # find source triangle
    #receiver_tr = ground_tin_result.find_receiver_triangle(4, receiver)
    # Walk to source, and save passing edges
    #edges, source_tr = ground_tin_result.walk_straight_to_source(source, receiver_tr)
    # interpolate height and distance
    #cross_vts, cross_edgs = ground_tin_result.create_cross_section(edges, source, receiver, source_tr, receiver_tr)
    
    # to delete
    # polygon_1 = [(1.8, 0.6, 0.0), (1.8, 0.2, 0.0), (2.2, 0.2, 0.0), (2.2, 0.6, 0.0), (1.8, 0.6, 0.0)]
    # polygon_2 = [(1.2, 0.2, 0.0), (1.8, 0.2, 0.0), (1.8, 0.8, 0.0), (1.2, 0.8, 0.0), (1.2, 0.2, 0.0)]
    # build = [Polygon(polygon_1), Polygon(polygon_2)]

    # add buildings to the cross section/ edges should have attributes or equivalent check data structure
    # cross_vts_dsm, cross_edgs_dsm = ground_tin_result.create_cross_section_dsm(cross_vts, cross_edgs, build)
    # ground_type = ['C', 'G', 'C', 'G', 'C', 'G', 'C', 'G']
    # assoc_building = [[1], [0, 1], [], [], [], [], [], []]
    #build = {0: 2, 1: 3}
    #test_00 = ground_tin_result.cross_section_total(receiver, source, receiver_tr, build)
    
    #time_2 = time()
    #print("runtime walking: {:.2f} seconds".format(time_2 - time_1))
    #print("runtime total: {:.2f} seconds".format(time_2 - start))
    

    #optionally, write the output line to the .obj file
    #misc.write_cross_section_to_obj("output/out.obj", cross_edgs, cross_vts, ground_tin_result.vts, ground_tin_result.trs)

    #output_file = "output/{}p".format(filename)
    #output_file = "output/out_test.objp"

    #ground_tin_result.write_to_obj("output/isolated_cubes.obj")
    #ground_tin_result.write_to_objp(output_file)

    #time_3 = time()
    #print("runtime writing: {:.2f} seconds".format(time_3 - time_2))
    #print(ground_tin_result.vts)
    #print(ground_tin_result.trs)

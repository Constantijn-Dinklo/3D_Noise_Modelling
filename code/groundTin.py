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
        
        self.kd_vts = KDTree(self.vts[:, [0, 1]])

        self.bounding_box_2d = [100000000, 100000000, -100000000, -100000000]
        self.bounding_box_3d = [100000000, 100000000, 100000000, -100000000, -100000000, -100000000]

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

    def find_vts_near_pt(self, p_receiver):
        nearest_vts = self.kd_vts.query(p_receiver)[1]
        for i, tr in enumerate(self.trs):
            if nearest_vts in tr[:3]:
                return i
        return 2

    def find_receiver_triangle(self, tr_init, p_receiver):
        """
        Explanation: Find the triangle in which the p_source is located, by means of walking from tr_init to the right triangle
        ---------------
        Input:
            tr_init : integer - An (arbitrary) triangle id to start from.
            p_receiver : [x,y,z] - The receiver point.
        ---------------
        Output:
            integer - triangle id of triangle underneath source point
        """
        #print("=== find_receiver_triangle ===")
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

        # quick check, debug:
        if((area_left + area_right) < 0.1):
            # if edge and both triangles are collinear, put the point half way.
            print("super small area, put point halfway")
            part_right = 0.5
        else: 
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
                # attribute = float(line_elements[1])
                attribute = line_elements[1].rstrip("\n")

                attributes.append(attribute)
    
    ground_tin = GroundTin(vertices, triangles, attributes)
    ground_tin.bounding_box_2d = [min_values[0], min_values[1], max_values[0], max_values[1]]
    ground_tin.bounding_box_3d = [min_values[0], min_values[1], min_values[2], max_values[0], max_values[1],
                                    max_values[2]]

    return ground_tin

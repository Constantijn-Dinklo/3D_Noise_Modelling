import matplotlib.pyplot as plt
import misc
import numpy as np
import startin
import sys
import triangle as tr

from scipy.spatial import ConvexHull
from shapely.geometry import shape, Polygon, LineString, Point
from shapely.ops import transform
from scipy.spatial import KDTree
from time import time

import fiona


class ConstrainedTin:

    def __init__(self, vts):
        # should we remove the vertices inside the building polygons? (time-wise)
        self.vts = vts
        self.trs = []
        self.vts_2d = []
        self.segments = []
        self.regions = []
        self.trs = []
        self.tin = startin.DT()
        self.tin.insert(vts)
        self.attr = []
        # self.segments_debug = []

        self.kd_vts = KDTree(self.vts)

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
        d1 = misc.side_test(self.vts[self.trs[tr][0]], self.vts[self.trs[tr][1]], pt)
        d2 = misc.side_test(self.vts[self.trs[tr][1]], self.vts[self.trs[tr][2]], pt)
        d3 = misc.side_test(self.vts[self.trs[tr][2]], self.vts[self.trs[tr][0]], pt)

        if d1 >= 0 and d2 >= 0 and d3 >= 0:
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

    def from_3d_to_2d(self):
        vts_3d = np.array(self.vts)
        vts = vts_3d[:, :2]
        self.vts_2d.extend(vts.tolist())

    def get_attr_coord(self, v0, v1, v2):
        seg_00 = (np.array(v1) - np.array(v0)) * (10 ** (-8))
        seg_01 = (np.array(v2) - np.array(v0)) * (10 ** (-8))
        coords = (seg_00 + seg_01) + np.array(v0)
        return coords[0], coords[1]

    def add_building_constraint(self, building):
        for record in building:
            i = len(self.vts)
            poly = shape(record['geometry'])
            x, y = poly.exterior.coords.xy
            vts_2d = list(zip(x, y))[:-1]
            self.vts_2d.extend(vts_2d)
            # interpolate points from TIN
            for v in vts_2d:
                z = self.tin.interpolate_tin_linear(v[0], v[1])
                self.vts.append((v[0], v[1], z))

            bound = []
            j = 0
            while j < len(vts_2d):
                if j != len(vts_2d) - 1:
                    bound.append((i + j, i + j + 1))
                    j += 1
                else:
                    bound.append((i + j, i))
                    j += 1

            self.segments.extend(bound)
            a, b = self.get_attr_coord(vts_2d[0], vts_2d[1], vts_2d[-1])
            self.regions.append([a, b, record['id'], 0])

    def add_ground_type_constraint(self, grd_type):
        for record in grd_type:
            i = len(self.vts)
            poly = shape(record['geometry'])
            vts_2d = list(poly.exterior.coords)[:-1]  # last vertex is same as first
            self.vts_2d.extend(vts_2d)
            # interpolate points from TIN
            for v in vts_2d:
                z = self.tin.interpolate_tin_linear(v[0], v[1])
                self.vts.append((v[0], v[1], z))

            bound = []
            j = 0
            while j < len(vts_2d):
                if j != len(vts_2d) - 1:
                    bound.append((i + j, i + j + 1))
                    j += 1
                else:
                    bound.append((i + j, i))
                    j += 1

            self.segments.extend(bound)
            a, b = self.get_attr_coord(vts_2d[0], vts_2d[1], vts_2d[-1])
            self.regions.append([a, b, record['id'], 0])

    def add_constraint(self, semantic):
        for record in semantic:
            if record['properties']['uuid'] is not None and record['properties']['bodemfacto'] is None:
                continue
            shapes = []
            if record['geometry']['type'] == 'MultiPolygon':
                for p in record['geometry']['coordinates']:
                    shapes.append(p[0])
            else:
                shapes.append(record['geometry']['coordinates'][0])
            k = 1
            for s in shapes:
                i = len(self.vts)
                poly = Polygon(s)
                x, y = poly.exterior.coords.xy
                vts_2d = list(zip(x, y))[:-1]
                self.vts_2d.extend(vts_2d)
                # interpolate points from TIN
                for v in vts_2d:
                    z = self.tin.interpolate_tin_linear(v[0], v[1])
                    self.vts.append((v[0], v[1], z))

                bound = []
                j = 0
                while j < len(vts_2d):
                    if j != len(vts_2d) - 1:
                        bound.append((i + j, i + j + 1))
                        j += 1
                    else:
                        bound.append((i + j, i))
                        j += 1

                self.segments.extend(bound)
                a, b = self.get_attr_coord(vts_2d[0], vts_2d[1], vts_2d[-1])
                self.regions.append([a, b, int(record['id']) * 100 + k, 0])
                # A = dict(vertices=self.vts_2d, segments=self.segments, regions=self.regions)
                # const_tin = tr.triangulate(A, 'npA')  # we can get the neighbors immediately
                # tr.compare(plt, A, const_tin)
                # plt.show()
                k += 1

    def triangulate_constraints(self, semantics):
        self.from_3d_to_2d()
        self.add_constraint(semantics)
        A = dict(vertices=self.vts_2d, segments=self.segments, regions=self.regions)
        const_tin = tr.triangulate(A, 'npA')  # we can get the neighbors immediately
        # tr.compare(plt, A, const_tin)
        # plt.show()
        if len(const_tin['vertices']) != len(self.vts):
            for v in const_tin['vertices'][len(self.vts):]:
                z = self.tin.interpolate_tin_linear(v[0], v[1])
                self.vts_2d.append(v)
                self.vts.append((v[0], v[1], z))
        temp_trs = const_tin['triangles'].tolist()
        temp_ns = const_tin['neighbors'].tolist()
        full_trs = list(zip(temp_trs, temp_ns))
        for triangle in full_trs:
            self.trs.append((triangle[0][0], triangle[0][1], triangle[0][2],
                             triangle[1][0], triangle[1][1], triangle[1][2]))
        self.attr = const_tin['triangle_attributes']
        return const_tin

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

        ground_tin = ConstrainedTin(vertices)
        ground_tin.bounding_box_2d = [min_values[0], min_values[1], max_values[0], max_values[1]]
        ground_tin.bounding_box_3d = [min_values[0], min_values[1], min_values[2], max_values[0], max_values[1],
                                      max_values[2]]

        return ground_tin

    @staticmethod
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

                    triangle = [v1, v2, v3, a1, a2, a3, np.array([100, 100]), 100, 100]

                    triangles.append(triangle)

        ground_tin = GroundTin(vertices, triangles)
        ground_tin.bounding_box_2d = [min_values[0], min_values[1], max_values[0], max_values[1]]
        ground_tin.bounding_box_3d = [min_values[0], min_values[1], min_values[2], max_values[0], max_values[1],
                                      max_values[2]]

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

            for attribute in self.attr:
                attribute_str = "a " + str(attribute[0]) + "\n"  # do we have to add 1 here?
                output_file.write(attribute_str)


if __name__ == "__main__":
    semantics = fiona.open("input/semaantics_test.shp")
    v_ground_tin_lod1 = ConstrainedTin.read_from_obj("input/tin.obj")
    output = v_ground_tin_lod1.triangulate_constraints(semantics)
    v_ground_tin_lod1.write_to_objp("output/constrainted_tin.objp")
    '''test_00 = output['vertices']
    test_01 = v_ground_tin_lod1.vts
    for i, v in enumerate(test_00):
        if i == len(test_00) - 1:
            print('1', i)
            break
        elif (v[0], v[1]) == (test_01[i][0], test_01[i][1]):
            continue
        else:
            print('2', i)
            break
    for t in output['triangles']:
        if 784 in t:
            print(t)'''

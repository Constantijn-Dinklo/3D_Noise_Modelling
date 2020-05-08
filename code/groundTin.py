
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
    
    def __init__(self, vts, trs):
        self.vts = np.array(vts)
        self.trs = np.array(trs)
        
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
        for i in range(1000): # max 1000 triangles to walk.
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
    
    def walk_straight_to_source(self, source, tr_receiver):
        """
        Explanation: Finds the edges of triangles between source and receiver.
        ---------------
        Input:
            source : [x,y,z] - the source point we want to walk to.
            tr_receiver : integer - triangle id of triangle underneath receiver point.
        ---------------
        Output:
            list of list - Contains the edges. [[e1_1, e1_2],
                                                [e2_1, e2_2]]
            the triangle containing the source
        """
        print("=== walk_straight_to_source ===")
        check_tr = tr_receiver
        chosen_edges = []
        nbs = [5, 3, 4]
        while not self.point_in_triangle(source, check_tr):
            assert(check_tr != -1)
            edges = [[self.trs[check_tr][0], self.trs[check_tr][1]],
                     [self.trs[check_tr][1], self.trs[check_tr][2]],
                     [self.trs[check_tr][2], self.trs[check_tr][0]]]
            for i, edge in enumerate(edges):
                if edge not in chosen_edges:
                    if (misc.side_test(receiver, source, self.vts[edge[0]]) <= 0 and
                            misc.side_test(receiver, source, self.vts[edge[1]]) >= 0):
                        chosen_edges.append(edge)
                        check_tr = self.trs[check_tr][nbs[i]]
                        break
        return chosen_edges, check_tr  # 2 edges might have a common vertex fix for this in interpolation
    
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

        w1 = ((v2[1] - v3[1])*(pt[0] - v3[0]) + (v3[0] - v2[0])*(pt[1] - v3[1])) / ((v2[1] - v3[1])*(v1[0] - v3[0]) + (v3[0] - v2[0])*(v1[1] - v3[1]))
        w2 = ((v3[1] - v1[1])*(pt[0] - v3[0]) + (v1[0] - v3[0])*(pt[1] - v3[1])) / ((v2[1] - v3[1])*(v1[0] - v3[0]) + (v3[0] - v2[0])*(v1[1] - v3[1]))
        w3 = 1 - w1 - w2

        return w1 * v1[2] + w2 * v2[2] + w3 * v3[2]

    def interpolate_edge(self, edge_0, edge_1, pt):
        """
        Explanation:
        Find the interpolated value on an edge
        ---------------
        Input:
        edge_0: first endpoint coordinates
        edge_1: second endpoint coordinates
        pt: point on the edge [x,y]
        ---------------
        Output:
        interpolated value
        """

        delta_x = edge_0[0] - pt[0]
        delta_y = edge_0[1] - pt[1]

        if delta_x > delta_y:
            w0 = delta_x / (edge_0[0] - edge_1[0])
        else:
            w0 = delta_y / (edge_0[1] - edge_1[1])

        w1 = 1 - w0

        return w0 * edge_0[2] + w1 * edge_1[2]

    def create_cross_section(self, edge_list, source, receiver, source_tr, receiver_tr ):
        """
        Explanation:
        ---------------
        Input:
        edge_list: list of edges, each edge is a tuple of 2 vertices.
        ---------------
        Output:
        a list with vertices in the cross section plane
        a list of edges which use the generated vertices.
        """
        print("=== create_cross_section ===")
        # the first vertex is the receiver, and the last vertex the source
        receiver_height = self.interpolate_triangle(receiver_tr, receiver)
        cross_section_vertices = [(receiver[0], receiver[1], receiver_height)]

        # the edges go from 0 - 1, 1-2, 2-3, 3-4, 4-5, 5-6
        cross_section_edges = [[0]]
        for i, edge in enumerate(edge_list):
            # get the vertices (from the vts list) and turn them into a numpt array for vector processing.
            vertex_right = np.array(self.vts[edge[0]])
            vertex_left = np.array(self.vts[edge[1]])
            
            #get the absolute area of the 2* the triangle (the rectangle of length from source to receiver and width the perpendicular distance to point p)
            area_right = abs(misc.side_test(receiver, source, vertex_right))
            area_left = abs(misc.side_test(receiver, source, vertex_left))

            # find where on the line (percentile) the cross section is.
            part_right = area_right / (area_left + area_right)

            # take vertex_right and append a part of the vector from right to left to it
            intersection_point = vertex_right + (vertex_left - vertex_right) * part_right

            # Check if the new calculated point is not too close to the previously added point, in MH distance
            if(np.sum(cross_section_vertices[-1] - intersection_point) < 0.1):
                print("points are the too close, nothing to add")
                continue

            cross_section_vertices.append(tuple(intersection_point))
            cross_section_edges[-1].append(i+1)
            cross_section_edges.append([i+1])
            #print("p_r: {}, p_l: {} a_r: {} a_l: {} portion: {} intersection at: {}".format(vertex_right, vertex_left, area_right, area_left, part_right, intersection_point))
        
        source_height = self.interpolate_triangle(source_tr, source)
        cross_section_vertices.append((source[0], source[1], source_height))
        cross_section_edges[-1].append(len(cross_section_vertices)-1)

        return cross_section_vertices, cross_section_edges

    def create_cross_section_dsm(self, dtm_vertices, dtm_edges, buildings):
        """
        Explanation:
        Adds buildings to the DTM cross section
        ---------------
        Input:
        dtm_vertices: List of vertices of cross section
        dtm_edges: list of edges, each edge is a tuple of 2 vertices and tuple of associated building polygons.[(__,__), (__, ..._)
        Buildings: list of shapely polygons with height attribute (how will this be exactly?)
        ---------------
        Output:
        a list with vertices in the cross section plane
        a list of edges which use the generated vertices.
        """
        cross_section_vertices = []
        cross_section_edges = []
        for edge in dtm_edges:
            shapely_line = LineString([dtm_vertices[edge[0][0]], dtm_vertices[edge[0][1]]])
            count = len(cross_section_vertices)
            if not edge[1]:
                if dtm_vertices[edge[0][0]] not in cross_section_vertices:
                    cross_section_vertices.append(dtm_vertices[edge[0][0]])
                    cross_section_vertices.append(dtm_vertices[edge[0][1]])
                    cross_section_edges.append((count, count + 1))
                else:
                    cross_section_vertices.append(dtm_vertices[edge[0][1]])
                    cross_section_edges.append((count - 1, count))
            else:
                # check intersection with polygon: intersects/ doesn't intersect/ inside polygon
                new_points = []
                check_edge_0 = False
                check_edge_1 = False
                for building in edge[1]:
                    build_info = buildings.get(building)  # building = id of polygon in shapefile
                    shapely_poly = shape(build_info['geometry'])
                    h_poly = build_info['properties']['h_dak']
                    if h_poly is None:
                        continue
                    flat_shp_geom = transform(lambda x, y, z=None: (x, y), shapely_poly)
                    '''build_info = buildings[building]  # building = id of polygon in shapefile
                    shapely_poly = shape(build_info)
                    h_poly = 2.0
                    flat_shp_geom = transform(lambda x, y, z=None: (x, y), shapely_poly)'''
                    # check if endpoints of edge are in polygon
                    if Point((dtm_vertices[edge[0][0]][0], dtm_vertices[edge[0][0]][1])).within(flat_shp_geom):
                        check_edge_0 = True
                    if Point((dtm_vertices[edge[0][1]][0], dtm_vertices[edge[0][1]][1])).within(flat_shp_geom):
                        check_edge_1 = True
                    poly_bound = flat_shp_geom.boundary
                    flat_shapely_line = transform(lambda x, y, z=None: (x, y), shapely_line)
                    if not flat_shapely_line.intersects(poly_bound) and not flat_shapely_line.within(flat_shp_geom):
                        # no intersection, edge identical to dtm
                        new_points.append(dtm_vertices[edge[0][0]])
                        new_points.append(dtm_vertices[edge[0][1]])
                        continue
                    elif not flat_shapely_line.intersects(poly_bound) and flat_shapely_line.within(flat_shp_geom):
                        # edge entirely inside polygon, no need to insert it anymore
                        continue
                    # elif flat_shapely_line.intersects(poly_bound) and flat_shapely_line.within(flat_shp_geom):
                        # do we need this condition?
                        # pass
                    else:
                        intersection_elem = flat_shapely_line.intersection(poly_bound)
                        if intersection_elem.geom_type == 'Point':
                            individual_points = list(intersection_elem.coords)
                        else:
                            individual_points = [(pt.x, pt.y) for pt in intersection_elem]
                        type_intersection = flat_shapely_line.intersection(flat_shp_geom)
                        # to distinguish between line intersections and point intersections
                        if type_intersection.geom_type == 'Point':
                            new_points.append(dtm_vertices[edge[0][0]])
                            new_points.append(dtm_vertices[edge[0][1]])
                            continue
                        if (type_intersection.geom_type == 'GeometryCollection' or
                                type_intersection.geom_type == 'MultiLineString'):
                            for elem in type_intersection:
                                if elem.geom_type == 'Point':
                                    pass
                                if elem.geom_type == 'LineString':
                                    points = list(elem.coords)
                                    if points[0] in individual_points:
                                        ground = self.interpolate_edge(dtm_vertices[edge[0][0]],
                                                                       dtm_vertices[edge[0][1]], points[0])
                                        if h_poly > ground:
                                            new_points.append((points[0][0], points[0][1], ground))
                                            new_points.append((points[0][0], points[0][1], h_poly))
                                        else:
                                            print("Roof height is lower than ground height, for building ", building)
                                            continue
                                    if points[1] in individual_points:
                                        ground = self.interpolate_edge(dtm_vertices[edge[0][0]],
                                                                       dtm_vertices[edge[0][1]], points[1])
                                        if h_poly > ground:
                                            new_points.append((points[1][0], points[1][1], h_poly))
                                            new_points.append((points[1][0], points[1][1], ground))
                                        else:
                                            print("Roof height is lower than ground height, for building ", building)
                                            continue
                        else:
                            # It is a LineString
                            points = list(type_intersection.coords)
                            if points[0] in individual_points:
                                ground = self.interpolate_edge(dtm_vertices[edge[0][0]],
                                                               dtm_vertices[edge[0][1]], points[0])
                                if h_poly > ground:
                                    new_points.append((points[0][0], points[0][1], ground))
                                    new_points.append((points[0][0], points[0][1], h_poly))
                                else:
                                    print("Roof height is lower than ground height, for building ", building)
                                    continue
                            if points[1] in individual_points:
                                ground = self.interpolate_edge(dtm_vertices[edge[0][0]],
                                                               dtm_vertices[edge[0][1]], points[1])
                                if h_poly > ground:
                                    new_points.append((points[1][0], points[1][1], h_poly))
                                    new_points.append((points[1][0], points[1][1], ground))
                                else:
                                    print("Roof height is lower than ground height, for building ", building)
                                    continue
                # add first endpoint of the edge if needed
                if dtm_vertices[edge[0][0]] not in new_points and check_edge_0 is False:
                    new_points = [dtm_vertices[edge[0][0]]] + new_points
                # add second endpoint of the edge if needed
                if dtm_vertices[edge[0][1]] not in new_points and check_edge_1 is False:
                    new_points = new_points + [dtm_vertices[edge[0][1]]]
                # sort buildings otherwise order of vertices will be wrong, check order between receiver and source
                if dtm_vertices[0][0] - dtm_vertices[-1][0] < 0:
                    new_points_sorted = sorted(new_points, key=lambda k: [k[0], k[1]])
                elif dtm_vertices[0][0] - dtm_vertices[-1][0] == 0 and dtm_vertices[0][1] - dtm_vertices[-1][1] < 0:
                    new_points_sorted = sorted(new_points, key=lambda k: [k[0], k[1]])
                elif dtm_vertices[0][0] - dtm_vertices[-1][0] == 0 and dtm_vertices[0][1] - dtm_vertices[-1][1] > 0:
                    new_points_sorted = sorted(new_points, key=lambda k: [k[0], k[1]], reverse=True)
                else:
                    new_points_sorted = sorted(new_points, key=lambda k: [k[0], k[1]], reverse=True)
                for pt in new_points_sorted:
                    count = len(cross_section_vertices)
                    if not cross_section_vertices:
                        cross_section_vertices.append(pt)
                    elif cross_section_vertices[-1] == pt:
                        pass
                    elif ((cross_section_vertices[-1][0], cross_section_vertices[-1][1]) == (pt[0], pt[1]) and
                          (cross_section_vertices[-2][0], cross_section_vertices[-2][1]) == (pt[0], pt[1])):
                        cross_section_vertices = cross_section_vertices[:(count-1)]
                        cross_section_vertices.append(pt)
                    else:
                        cross_section_vertices.append(pt)
                        cross_section_edges.append((count - 1, count))
        return cross_section_vertices, cross_section_edges

    def get_2d_convex_hull(self):
        """
        Explination: Get the 2d convex hull of this tin.
        ---------------
        Input: void
        ---------------
        Output:
            convex_hull : ConvexHull - The 2d convex hull of this tin.
        """
        points_2d = self.vts[:,:2]
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

        #Read the file and store all the vertices and triangles
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

        #Loop through all triangles, finding all triangles adjacent to it
        index = 0
        for triangle in triangles:
            #print("Index: " + str(index))
            v1 = triangle[0]
            v2 = triangle[1]
            v3 = triangle[2]
            i1 = triangle[3]
            i2 = triangle[4]
            i3 = triangle[5]

            #Check to make sure this triangle hasn't already been completely classified
            if (i1 != -1) and (i2 != -1) and (i3 != -1):
                index = index + 1
                continue

            for i in range(index + 1, len(triangles)):
                #print("Checking against triangle: " + str(i))
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

        ground_tin =  GroundTin(vertices, triangles)
        ground_tin.bounding_box_2d = [min_values[0], min_values[1], max_values[0], max_values[1]]
        ground_tin.bounding_box_3d = [min_values[0], min_values[1], min_values[2], max_values[0], max_values[1], max_values[2]]

        if orientation_check:
            ground_tin.orient_tin()

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

        #Read the file and store all the vertices and triangles
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
        ground_tin.bounding_box_3d = [min_values[0], min_values[1], min_values[2], max_values[0], max_values[1], max_values[2]]

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
                triangle_str = "f " + str(triangle[0] + 1) + " " + str(triangle[1] + 1) + " " + str(triangle[2] + 1) + "\n"
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
                triangle_str = "f " + str(triangle[0] + 1) + " " + str(triangle[1] + 1) + " " + str(triangle[2] + 1) + " " + str(triangle[3] + 1) + " " + str(triangle[4] + 1) + " " + str(triangle[5] + 1) + "\n"
                output_file.write(triangle_str)

if __name__ == "__main__":
    #run in commandline = python groundTin.py ./input/sample.obj
    tin_filename = sys.argv[1]

    #Create a 
    #ground_tin_result = GroundTin.read_from_obj("input/isolated_cubes.obj")
    #ground_tin_resultp = GroundTin.read_from_objp("input/isolated_cubes.objp")
    
    start = time()
    ground_tin_result = GroundTin.read_from_objp(tin_filename)
    time_1 = time()
    print("runtime reading obj: {:.2f} seconds".format(time_1 - start))
    #Setup dummy source and receiver points
    #source = [0.75, 0.1, 0]
    #receiver = [8.25, 0.9, 0]

    #Setup dummy source and receiver points
    source = [93512.5, 441865, 3]
    receiver = [93612.2, 441885.4, 2]

    building_filename = sys.argv[2]
    build = fiona.open(building_filename)

    # dsm test
    '''triangles = [[0, 2, 1, 1, -1, -1],
           [1, 2, 3, 2, -1, 0],
           [2, 4, 3, 3, 1, -1],
           [3, 4, 5, 4, -1, 2],
           [4, 6, 5, 5, 3, -1],
           [5, 6, 7, 6, -1, 4],
           [6, 8, 7, 7, 5, -1],
           [7, 8, 9, -1, -1, 6]]

    vertices = [[0, 0, 0],
                [1, 1, 1],
                [2, 0, 1],
                [3, 1, 0],
                [4, 0, 1],
                [5, 1, 1],
                [6, 0, 0],
                [7, 1, 1],
                [8, 0, 0],
                [9, 1, 0]]

    ground_tin_result = GroundTin(vertices, triangles)'''


    # find source triangle
    receiver_tr = ground_tin_result.find_receiver_triangle(4, receiver)
    # Walk to source, and save passing edges
    edges, source_tr = ground_tin_result.walk_straight_to_source(source, receiver_tr)
    # interpolate height and distance
    cross_vts, cross_edgs = ground_tin_result.create_cross_section(edges, source, receiver, source_tr, receiver_tr)
    # to delete
    '''cross_edgs_attr = []
    for lin, e in enumerate(cross_edgs):
        if lin < 6:
            cross_edgs_attr.append([e, []])
        elif lin == 6:
            cross_edgs_attr.append([e, [0, 1]])
        else:
            cross_edgs_attr.append([e, [1]])
    polygon_1 = [(1.8, 0.6, 0.0), (1.8, 0.2, 0.0), (2.2, 0.2, 0.0), (2.2, 0.6, 0.0), (1.8, 0.6, 0.0)]
    polygon_2 = [(1.2, 0.2, 0.0), (1.8, 0.2, 0.0), (1.8, 0.8, 0.0), (1.2, 0.8, 0.0), (1.2, 0.2, 0.0)]
    build = [Polygon(polygon_1), Polygon(polygon_2)]'''

    # add buildings to the cross section/ edges should have attributes or equivalent check data structure
    cross_vts_dsm, cross_edgs_dsm = ground_tin_result.create_cross_section_dsm(cross_vts, cross_edgs, build)


    time_2 = time()
    print("runtime walking: {:.2f} seconds".format(time_2 - time_1))
    print("runtime total: {:.2f} seconds".format(time_2 - start))
    

    #optionally, write the output line to the .obj file
    misc.write_cross_section_to_obj("output/out.obj", cross_edgs, cross_vts, ground_tin_result.vts, ground_tin_result.trs)

    #output_file = "output/{}p".format(filename)
    output_file = "output/out_test.objp"

    #ground_tin_result.write_to_obj("output/isolated_cubes.obj")
    ground_tin_result.write_to_objp(output_file)

    time_3 = time()
    print("runtime writing: {:.2f} seconds".format(time_3 - time_2))
    #print(ground_tin_result.vts)
    #print(ground_tin_result.trs)
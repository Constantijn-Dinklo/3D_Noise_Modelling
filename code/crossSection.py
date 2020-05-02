import sys
import numpy as np

# test data
trs = [[0, 2, 1, 1, -1, -1],
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

source = [0.75, 0.1, 0]
receiver = [8.25, 0.9, 0]


class Tin:
    def __init__(self, trs, vts):
        self.trs = trs  # triangles [v1, v2, v3, n1, n2, n3]
        self.vts = vts  # set with vertex numbers used in this mesh

    def side_test(self, pa, pb, pc):
        """
        Explanation:
        find whether pc is on the left (+) or on the right (-) of the line pa -> pb
        the computed value is actually the 2* area of the triangle
        ---------------
        Input:
        pa = [x,y,z]
        pb = [x,y,z]
        pc = [x,y,z]
        ---------------
        Output:
        2 *  the area of the triangle
        """
        return ((pa[0] - pc[0]) * (pb[1] - pc[1])) - ((pb[0] - pc[0]) * (pa[1] - pc[1]))

    def point_in_triangle(self, pt, tr):
        """
        Explanation:
        do a side test for all edges with the pt, if they are all positive
        ---------------
        Input:
        pt = [x,y,z]
        tr = triangle ID
        ---------------
        Output:
        """
        d1 = self.side_test(self.vts[self.trs[tr][0]], self.vts[self.trs[tr][1]], pt)
        d2 = self.side_test(self.vts[self.trs[tr][1]], self.vts[self.trs[tr][2]], pt)
        d3 = self.side_test(self.vts[self.trs[tr][2]], self.vts[self.trs[tr][0]], pt)

        if d1 >= 0 and d2 >= 0 and d3 >= 0:
            return True  # the point is in the triangle
        else:
            return False

    def find_receiver_triangle(self, tr_init, p_receiver):
        """
        Explanation:
        Find the trinagle in which the p_source is located, by means of walking from tr_init to the right triangle
        ---------------
        Input:
        tr_init: an (arbitrary) triangle id to start from
        p_source: the source point
        ---------------
        Output:
        triangle id of triangle underneath source point
        """
        print("=== find_receiver_triangle ===")
        tr = tr_init
        for i in range(1000): # max 1000 triangles to walk.
            # do the side test for all sides, returns the value
            d1 = self.side_test(self.vts[self.trs[tr][0]], self.vts[self.trs[tr][1]], p_receiver)
            d2 = self.side_test(self.vts[self.trs[tr][1]], self.vts[self.trs[tr][2]], p_receiver)
            d3 = self.side_test(self.vts[self.trs[tr][2]], self.vts[self.trs[tr][0]], p_receiver)

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
        assert(False)

    def walk_straight_to_source(self, tr_receiver):
        """
        Explanation:
        Finds the edges of triangles between source and receiver
        ---------------
        Input:
        tr_source: triangle id of triangle underneath source point
        ---------------
        Output:
        list of list containing the edges
        """
        print("=== walk_straight_to_source ===")
        check_tr = tr_receiver
        chosen_edges = []
        nbs = (5, 3, 4)
        while not self.point_in_triangle(source, check_tr):
            edges = [[self.trs[check_tr][0], self.trs[check_tr][1]],
                     [self.trs[check_tr][1], self.trs[check_tr][2]],
                     [self.trs[check_tr][2], self.trs[check_tr][0]]]
            for i, e in enumerate(edges):
                if e not in chosen_edges:
                    if (self.side_test(receiver, source, self.vts[e[0]]) <= 0 and
                            self.side_test(receiver, source, self.vts[e[1]]) >= 0):
                        chosen_edges.append(e)
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
        cross_section_vertices = [[receiver[0], receiver[1], receiver_height]]

        # the edges go from 0 - 1, 1-2, 2-3, 3-4, 4-5, 5-6
        cross_section_edges = [[0]]
        for i, edge in enumerate(edge_list):
            # get the vertices (from the vts list) and turn them into a numpt array for vector processing.
            vertex_right = np.array(self.vts[edge[0]])
            vertex_left = np.array(self.vts[edge[1]])
            
            #get the absolute area of the 2* the triangle (the rectangle of length from source to receiver and width the perpendicular distance to point p)
            area_right = abs(self.side_test(receiver, source, vertex_right))
            area_left = abs(self.side_test(receiver, source, vertex_left))

            # find where on the line (percentile) the cross section is.
            part_right = area_right / (area_left + area_right)

            # take vertex_right and append a part of the vector from right to left to it
            intersection_point = vertex_right + (vertex_left - vertex_right) * part_right

            # Check if the new calculated point is not too close to the previously added point, in MH distance
            if(np.sum(cross_section_vertices[-1] - intersection_point) < 0.1):
                print("points are the too close, nothing to add")
                continue

            cross_section_vertices.append(intersection_point)
            cross_section_edges[-1].append(i+1)
            cross_section_edges.append([i+1])
            #print("p_r: {}, p_l: {} a_r: {} a_l: {} portion: {} intersection at: {}".format(vertex_right, vertex_left, area_right, area_left, part_right, intersection_point))
        
        source_height = self.interpolate_triangle(source_tr, source)
        cross_section_vertices.append([source[0], source[1], source_height])
        cross_section_edges[-1].append(len(cross_section_vertices)-1)

        return cross_section_vertices, cross_section_edges



def write_obj(obj_filename, cross_edges, cross_vts):
    print("=== Writing {} ===".format(obj_filename))

    f_out = open(obj_filename, 'w')
    for v in vertices:
        f_out.write("v " + str(float(v[0])) + " " + str(float(v[1])) + " " + str(float(v[2])) + "\n")
    for v in cross_vts:
        f_out.write("v " + str(float(v[0])) + " " + str(float(v[1])) + " " + str(float(v[2])) + "\n")

    f_out.write("o 0\n")

    for tr in trs:
        tr[0] += 1
        tr[1] += 1
        tr[2] += 1
        f_out.write("f " + str(tr[0]) + " " + str(tr[1]) + " " + str(tr[2]) + "\n")

    f_out.write("l")
    for line in cross_edges:
        f_out.write(" " + str(line[0] + 1 + len(vertices)))
    f_out.write(" " + str(cross_edges[-1][1] + 1 + len(vertices)) +  "\n")

    f_out.close()

def main(sys_args):
    """
    Explanation:
    get the cross section from 2 given points
    find the starting triangle
    walk to the other point etc.
    ---------------
    Input:
    2 points in [x,y,z]
    ---------------
    Output:
    list?
    """
    # sys args will be: 
    # run command: python crossSection.py

    trs_ = Tin(trs, vertices)
    # find source triangle
    receiver_tr = trs_.find_receiver_triangle(4, receiver)
    # Walk to source, and save passing edges
    edges, source_tr = trs_.walk_straight_to_source(receiver_tr)
    # interpolate height and distance
    cross_vts, cross_edgs = trs_.create_cross_section(edges, source, receiver, source_tr, receiver_tr)

    #optionally, write the output line to the .obj file
    write_obj("out.obj", cross_edgs, cross_vts)


if __name__ == "__main__":
    main(sys.argv)

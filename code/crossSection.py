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
            [1, 1, 0],
            [2, 0, 0],
            [3, 1, 0],
            [4, 0, 0],
            [5, 1, 0],
            [6, 0, 0],
            [7, 1, 0],
            [8, 0, 0],
            [9, 1, 0]]

source = [0.75, 0.5, 0]
receiver = [8.25, 0.5, 0]


class Tin:
    def __init__(self, trs, vts):
        self.trs = trs  # triangles [v1, v2, v3, n1, n2, n3]
        self.vts = vts  # set with vertex numbers used in this mesh

    def side_test(self, pa, pb, pc):  # pa, pb, pc = index numbor of P
        """
        Explanation:
        find whether pc is on the left (+/-) or on the right (+/-) of the line pa -> pb
        the computed value is actually the 2* area of the triangle
        ---------------
        Input:
        vertex coordinates (had to change this: vertex indices edge of tr: pa, pb p_source = pc)
        ---------------
        Output:
        boolean, whether the point is in the triangle
        """
        return ((pa[0] - pc[0]) * (pb[1] - pc[1])) - ((pb[0] - pc[0]) * (pa[1] - pc[1]))

    def point_in_triangle(self, p_source, tr):
        """
        Explanation:
        ---------------
        Input:
        ---------------
        Output:
        """
        d1 = self.side_test(self.vts[self.trs[tr][0]], self.vts[self.trs[tr][1]], p_source)
        d2 = self.side_test(self.vts[self.trs[tr][1]], self.vts[self.trs[tr][2]], p_source)
        d3 = self.side_test(self.vts[self.trs[tr][2]], self.vts[self.trs[tr][0]], p_source)

        if d1 > 0 and d2 > 0 and d3 > 0:
            return True  # the point is in the triangle
        else:
            return False

    def find_source_triangle(self, tr_init, p_source):
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
        tr = tr_init
        while True:
            # do the side test for all sides, returns the value
            d1 = self.side_test(self.vts[self.trs[tr][0]], self.vts[self.trs[tr][1]], p_source)
            d2 = self.side_test(self.vts[self.trs[tr][1]], self.vts[self.trs[tr][2]], p_source)
            d3 = self.side_test(self.vts[self.trs[tr][2]], self.vts[self.trs[tr][0]], p_source)

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
            # if(d_min == 0): d_min = 5
            # if(d_min == 1): d_min = 3
            # if(d_min == 2): d_min = 4

            # get the index of the neighbour triangle
            tr = self.trs[tr][nb_index]

    def walk_straight_to_receiver(self, tr_source):
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
        check_tr = tr_source
        chosen_edges = []
        nbs = [5, 3, 4]
        while not self.point_in_triangle(receiver, check_tr):
            edges = [[self.trs[check_tr][0], self.trs[check_tr][1]],
                     [self.trs[check_tr][1], self.trs[check_tr][2]],
                     [self.trs[check_tr][2], self.trs[check_tr][0]]]
            for i, e in enumerate(edges):
                # store edges from smaller to larger index to be consistent in chosen_edges
                e.sort()
                if e not in chosen_edges:
                    if (self.side_test(receiver, source, self.vts[e[0]]) >= 0 and
                        self.side_test(receiver, source, self.vts[e[1]]) <= 0) or \
                            (self.side_test(receiver, source, self.vts[e[0]]) <= 0 and
                             self.side_test(receiver, source, self.vts[e[1]]) >= 0):
                        chosen_edges.append(e)
                        check_tr = self.trs[check_tr][nbs[i]]
                        break
        return chosen_edges  # 2 edges might have a common vertex fix for this in interpolation

    def create_cross_section(self, tr_list):
        """
        Explanation:
        ---------------
        Input:
        ---------------
        Output:
        """
        pass


def write_obj(obj_filename):
    print("=== Writing {} ===".format(obj_filename))

    f_out = open(obj_filename, 'w')
    for v in vertices:
        f_out.write("v " + str(float(v[0])) + " " + str(float(v[1])) + " " + str(float(v[2])) + "\n")

    f_out.write("o 0\n")

    for tr in trs:
        tr[0] += 1
        tr[1] += 1
        tr[2] += 1
        f_out.write("f " + str(tr[0]) + " " + str(tr[1]) + " " + str(tr[2]) + "\n")
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
    # run command: python crossSection.py ....

    trs_ = Tin(trs, vertices)
    # find source triangle
    init_tr = trs_.find_source_triangle(4, source)
    edges = trs_.walk_straight_to_receiver(init_tr)
    # fix the problem with edge [0,1] first triangle needs a double check
    print('hi')
    # Walk to receiver, and save passing triangles
    # interpolat height and distance

    # write_obj("out.obj")


if __name__ == "__main__":
    main(sys.argv)

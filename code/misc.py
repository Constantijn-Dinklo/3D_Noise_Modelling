
import numpy as np

def normal_of_triangle(triangle):

    x0, y0, z0 = triangle[0]
    x1, y1, z1 = triangle[1]
    x2, y2, z2 = triangle[2]

    ux, uy, uz = u = [x1-x0, y1-y0, z1-z0]
    vx, vy, vz = v = [x2-x0, y2-y0, z2-z0]

    normal_vector = [uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx]
    return normal_vector

def side_test(pa, pb, pc):
        """
        Explanation:
        find whether pc is on the left (+) or on the right (-) of the line pa -> pb
        the computed value is actually the 2* area of the triangle
        ---------------
        Input:
        pa = [x,y(,z)]
        pb = [x,y(,z)]
        pc = [x,y(,z)]
        ---------------
        Output:
        2 *  the area of the triangle
        """
        return ((pa[0] - pc[0]) * (pb[1] - pc[1])) - ((pb[0] - pc[0]) * (pa[1] - pc[1]))

def interpolate_edge(edge_0, edge_1, pt):
    """
    Explanation:
    Find the interpolated value on an edge
    ---------------
    Input:
    edge_0: (x, y, z) - first endpoint coordinates
    edge_1: (x, y, z) - second endpoint coordinates
    pt: (x, y) - point on the edge to be interpolated
    ---------------
    Output:
    float - interpolated value
    """

    delta_x = edge_0[0] - pt[0]
    delta_y = edge_0[1] - pt[1]
    segment_x = edge_0[0] - edge_1[0]
    segment_y = edge_0[1] - edge_1[1]

    w0_ = (delta_x**2 + delta_y**2)**0.5 / (segment_x**2 + segment_y**2)**0.5

    if delta_x > delta_y and segment_x != 0:
        w0 = delta_x / segment_x
    elif delta_x <= delta_y and segment_y != 0:
        w0 = delta_y / segment_y
    elif delta_x > delta_y and segment_x == 0:
        w0 = delta_y / segment_y
    else:
        w0 = delta_x / segment_x

    w1 = 1 - w0_
    t = w1 * edge_0[2] + w0_ * edge_1[2]

    return w1 * edge_0[2] + w0_ * edge_1[2]

def reverse_bisect_left(a, x, lo=0, hi=None):
    """Borrowed from the bissect library - Return the index where to insert
    item x in list a, assuming a is sorted.
    The return value i is such that all e in a[:i] have e < x, and all e in
    a[i:] have e >= x.  So if x already appears in the list, a.insert(x) will
    insert just before the leftmost x already there.
    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """

    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    while lo < hi:
        mid = (lo+hi)//2
        if a[mid] > x: lo = mid+1
        else: hi = mid
    return lo
    
def write_cross_section_to_obj(obj_filename, path_list):
    print("=== Writing {} ===".format(obj_filename))


    with open(obj_filename, 'w') as f_out:
        vts_count_lst = [0]
        counter = 0
        for path in path_list:
            path = np.array(path)
            # has the starting vertex number
            counter = counter + len(path)
            vts_count_lst.append(counter)
            print(path)
            for v in path:
                #f_out.write("v " + str(float(v[0])) + " " + str(float(v[1])) + " " + str(float(v[2])) + "\n")
                f_out.write("v {:.2f} {:.2f} {:.2f}\n".format(v[0], v[1], v[2]))
        
        #print(vts_count_lst)
        for i, path in enumerate(path_list):
            base = vts_count_lst[i]
            f_out.write("l")
            for i in range(len(path)):
                f_out.write(" " + str(base + i + 1))
            f_out.write("\n")
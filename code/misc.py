

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
        pa = [x,y,z]
        pb = [x,y,z]
        pc = [x,y,z]
        ---------------
        Output:
        2 *  the area of the triangle
        """
        return ((pa[0] - pc[0]) * (pb[1] - pc[1])) - ((pb[0] - pc[0]) * (pa[1] - pc[1]))
    
def write_cross_section_to_obj(obj_filename, cross_edges, cross_vts, vertices=[], trs=[]):
    print("=== Writing {} ===".format(obj_filename))

    f_out = open(obj_filename, 'w')
    for v in vertices:
        f_out.write("v " + str(float(v[0])) + " " + str(float(v[1])) + " " + str(float(v[2])) + "\n")
    for v in cross_vts:
        #f_out.write("v " + str(float(v[0])) + " " + str(float(v[1])) + " " + str(float(v[2])) + "\n")
        f_out.write("v {:.3f} {:.3f} {:.3f}\n".format(v[0], v[1], v[2]))
        

    f_out.write("o 0\n")

    for tr in trs:
        tr += 1
        f_out.write("f " + str(tr[0]) + " " + str(tr[1]) + " " + str(tr[2]) + "\n")

    f_out.write("l")
    for line in cross_edges:
        f_out.write(" " + str(line[0] + 1 + len(vertices)))
    f_out.write(" " + str(cross_edges[-1][1] + 1 + len(vertices)) +  "\n")

    f_out.close()
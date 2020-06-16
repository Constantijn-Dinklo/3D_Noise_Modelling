
import math
import numpy as np
import xml.etree.cElementTree as ET

def normal_of_triangle(triangle):

    x0, y0, z0 = triangle[0]
    x1, y1, z1 = triangle[1]
    x2, y2, z2 = triangle[2]

    ux, uy, uz = u = [x1-x0, y1-y0, z1-z0]
    vx, vy, vz = v = [x2-x0, y2-y0, z2-z0]

    normal_vector = [uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx]
    return normal_vector


def parametric_line_equation(p1, p2):
    """
    Explanation: A function that reads two points and returns the ABC parameters of the line composed by these points.
    ---------------
    Input:
    p1 : [x(float), y(float)] - The starting point in the line.
    p2 : [x(float), y(float)] - The ending point in the line.
    ---------------
    Output:
    parameters: [a_norm(float),b_norm(float),c_norm(float)] - The a,b,c parameters of the normalised line equation.
    """
    # EQUATION OF A LINE IN THE 2D PLANE:
    # A * x + B * y + C = 0
    a = p2[1] - p1[1]
    b = -(p2[0] - p1[0])
    c = -a * p1[0] - b * p1[1]
    m = math.sqrt(a * a + b * b)
    a_norm = a / m
    b_norm = b / m
    c_norm = c / m
    # EQUATION OF A LINE IN THE 2D PLANE WITH NORMALISED (UNIT) NORMAL VECTORs:
    # A' * x + B' * y + C' = 0
    parameters = [a_norm, b_norm, c_norm]
    return parameters  # THE PARAMETERS OF THE NORMALISED LINE.

def point_on_line(point, lineseg):
    """
    Explanation: A function that tests if a point that is known to be part of a line is within a specific line segment of
    that particular line.
    ---------------
    Input:
    point: [x(float), y(float)] - A point.
    lineseg: [[x(float), y(float)],[x(float), y(float)]] - A line segment.
    ---------------
    Output:
    point: [x(float), y(float)] - The intersection point.
    """
    x_min = min(lineseg[0][0], lineseg[1][0])
    x_max = max(lineseg[0][0], lineseg[1][0])
    y_min = min(lineseg[0][1], lineseg[1][1])
    y_max = max(lineseg[0][1], lineseg[1][1])
    return point[0] > x_min and point[0] < x_max and point[1] > y_min and point[1] < y_max

def line_intersect(line1, line2):
    """
    Explanation: this functions returns the intersection points (source points) of both lines
    ---------------
    Input:
    line1: the line segment of the receiver point
    line2: the line segment of the source
    ---------------
    Output:
    point : it returns the point where both line segments intersect
    """
    d = (line2[1][1] - line2[0][1]) * (line1[1][0] - line1[0][0]) - (line2[1][0] - line2[0][0]) * (
                line1[1][1] - line1[0][1])
    if d:
        uA = ((line2[1][0] - line2[0][0]) * (line1[0][1] - line2[0][1]) - (line2[1][1] - line2[0][1]) * (
                    line1[0][0] - line2[0][0])) / d
        uB = ((line1[1][0] - line1[0][0]) * (line1[0][1] - line2[0][1]) - (line1[1][1] - line1[0][1]) * (
                    line1[0][0] - line2[0][0])) / d
    else:
        return False
    if not (0 <= uA <= 1 and 0 <= uB <= 1):
        return False
    x = line1[0][0] + uA * (line1[1][0] - line1[0][0])
    y = line1[0][1] + uA * (line1[1][1] - line1[0][1])
    return (x, y)

def x_line_intersect(line1, line2):
    """
    Explanation: A function that returns the intersection point between two xlines. It doesn't matter if the line segments
    are really intersecting each other; if they are not, the interception point is virtual, as like it will be the extension of
    as least one of these lines. This is important for testing reflection points and, therefore, the algorithm cannot use
    line_intersect, since this last one will return False if the lines do not intercept each other indeed.
    ---------------
    Input:
    line1 : [[x(float), y(float)],[x(float), y(float)]] - A line segment.
    line2 : [[x(float), y(float)],[x(float), y(float)]] - A line segment.
    ---------------
    Output:
    point: [x(float), y(float)] - The intersection point.
    """
    num_x = (line1[0][0] * line1[1][1] - line1[0][1] * line1[1][0]) * (line2[0][0] - line2[1][0]) - (
                line1[0][0] - line1[1][0]) * (line2[0][0] * line2[1][1] - line2[0][1] * line2[1][0])
    num_y = (line1[0][0] * line1[1][1] - line1[0][1] * line1[1][0]) * (line2[0][1] - line2[1][1]) - (
                line1[0][1] - line1[1][1]) * (line2[0][0] * line2[1][1] - line2[0][1] * line2[1][0])
    denom = (line1[0][0] - line1[1][0]) * (line2[0][1] - line2[1][1]) - (line1[0][1] - line1[1][1]) * (
                line2[0][0] - line2[1][0])
    return [num_x / denom, num_y / denom]

def get_rotated_point(p1, p2, angle):
    """
    Explanation: A function that reads point p1 (centre), p2, and an angle and returns p2', i.e. the rotated point.
    ---------------
    Input:
    p1 : numpy array [x(float), y(float)] - The centre of rotation.
    p2 : numpy array [x(float), y(float)] - The starting point of rotation, i.e. the point to be rotated.
    angle : float - The angle of rotation (in radians)
    Attention: a positive angle rotates to the left (counterclockwise), whereas a negative angle rotates to the right (clockwise)
    ---------------
    Output:
    p2_new: numpy array [x(float), y(float)] - The rotated point
    """
    vector = p2 - p1
    # get the squared length (as an indication, had to be longer than the original), faster and safer to use a longer distance.
    vector_length = vector[0] ** 2 + vector[1] ** 2

    # inverse tanges of y / x, returns the angle of hte vector.
    vector_angle = math.atan2(vector[1], vector[0]) 
    # add the angle difference
    vector_angle += angle
    
    new_vector = (
        vector_length * math.cos(vector_angle), 
        vector_length * math.sin(vector_angle))
    
    # add the new vector to the old one, to go to the real world coordinate again.
    new_vector += p1

    return new_vector

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

    delta_x = abs(edge_0[0] - pt[0])
    delta_y = abs(edge_0[1] - pt[1])
    segment_x = abs(edge_0[0] - edge_1[0])
    segment_y = abs(edge_0[1] - edge_1[1])

    if delta_x > delta_y:
        w0 = delta_x / segment_x
    else:
        w0 = delta_y / segment_y

    w1 = 1 - w0

    return w1 * edge_0[2] + w0 * edge_1[2]

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

def write_default_noise(filename, Lw, source_height):
    """
        CURRENTLY NOT USED
    """
    """
    root = ET.Element("CNOSSOS_SourcePower", version="X1.0")
    source = ET.SubElement(root, "source")
    ET.SubElement(source, "h").text = str(source_height)
    ET.SubElement(source, "Lw", 
        sourceType=Lw['sourceType'],
        measurementType=Lw['measurementType'],
        frequencyWeighting=Lw['frequencyWeighting']
    ).text = Lw['power']
    tree = ET.ElementTree(root)
    tree.write(filename, encoding="UTF-8", xml_declaration=True)
    """
    pass
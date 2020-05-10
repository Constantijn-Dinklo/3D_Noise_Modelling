# Generate sources and receivers
import math
import xml.etree.cElementTree as ET
import matplotlib.pyplot as plt
import numpy as np

hard_coded_source = (93550, 442000)

def read_gml(path):
    # input: path to a xml file
    # output: returns the roots of the xml file
    tree = ET.parse(path)
    root = tree.getroot()
    return root

structured_segments = [ ]
def return_segments_source(root):
    line_string = [ ] # replace lists inside function
    line_float = [ ]
    line_segments = [ ]
    # input: root of the xml file
    # output: list of line segments consisting of two points, however format not correct yet
    for child in root.iter():
        if "coordinates" in child.tag:
            coordinates = child.text
            line_string = coordinates.split()
            if len(line_string) > 1:
                for point in line_string:
                    coord = point.split(',') 
                    line_float.append((float(coord[0]), float(coord[1])))
                for i in range(len(line_float)-1):
                    first_el = line_float[i]
                    second_el = line_float[i + 1]
                    line = (first_el, second_el)
                    if line not in line_segments:
                        line_segments.append((first_el, second_el))
    return line_segments

def return_points_circle(centre, radius, radians):
    # input: receiver point [x, y], radius and the angle size
    # output: next point on circumsfere [x, y]
    x_next = centre[0] + radius * math.cos(radians)
    y_next = centre[1] + radius * math.sin(radians)
    next_point = [x_next, y_next]
    return next_point

angle = 2.0 * (math.pi / 180) 
cnossos_radius = 100.0
base_angle = 0.0
angle_st = 2.0
start_st = 0.0
def return_line_segments_receiver(centre, start, step, base):
    # input: receiver point [x, y], start, step size, basis angle in degrees
    # output: a list of all receiver line segments
    lines_per_circle = [ ]
    while start < 360:
        next_angle = base * (math.pi / 180)
        following = return_points_circle(hard_coded_source, cnossos_radius, next_angle)
        lines_per_circle.append([centre, following])
        base += step
        start += step
    return lines_per_circle

def line_intersect(line1, line2):
    # input: line1 is the receiver line segments, line2 is the source line segment
    # output: intersection point in a tuple
    d = (line2[1][1] - line2[0][1]) * (line1[1][0] - line1[0][0]) - (line2[1][0] - line2[0][0]) * (line1[1][1] - line1[0][1])
    if d:
        uA = ((line2[1][0] - line2[0][0]) * (line1[0][1] - line2[0][1]) - (line2[1][1] - line2[0][1]) * (line1[0][0] - line2[0][0])) / d
        uB = ((line1[1][0] - line1[0][0]) * (line1[0][1] - line2[0][1]) - (line1[1][1] - line1[0][1]) * (line1[0][0] - line2[0][0])) / d
    else:
        return
    if not(0 <= uA <= 1 and 0 <= uB <= 1):
        return
    x = line1[0][0] + uA * (line1[1][0] - line1[0][0])
    y = line1[0][1] + uA * (line1[1][1] - line1[0][1])
    return x, y

dict_intersection = { }
list_intersection = [ ]
def return_dictionary(receiver_list, source_list):
    # input: two lists of line segments
    # output: a dictionary in which the receiver point is the key and a list of intersection points as the corresponding value
    for circle_line in receiver_list:
        for struct_line in source_list:
            point_intersection = line_intersect(circle_line, struct_line)
            if point_intersection not in list_intersection and point_intersection is not None:
                list_intersection.append(point_intersection)

    dict_intersection[hard_coded_source] = list_intersection
    return dict_intersection

if __name__ == '__main__':
    doc = read_gml('/Users/mprusti/Documents/geo1101/wegvakgeografie_simplified.gml') # now local, should be global in future
    line_lst = return_segments_source(doc) # check
    hard_coded_source_lines = return_line_segments_receiver(hard_coded_source, start_st, angle_st, base_angle) # check
    intersected = return_dictionary(hard_coded_source_lines, line_lst)

    # Plot the source line segments
    x_source = [ ]
    y_source = [ ]
    for ln in line_lst:
        x_source.append(ln[0][0])
        x_source.append(ln[1][0])
        y_source.append(ln[0][1])
        y_source.append(ln[1][1])
    plt.plot(x_source, y_source, c='g')

    # Plot the receiver line segments
    x_receiver = [ ]
    y_receiver = [ ]
    for lne in hard_coded_source_lines:
        x_receiver.append(lne[0][0])
        x_receiver.append(lne[1][0])
        y_receiver.append(lne[0][1])
        y_receiver.append(lne[1][1])
    plt.plot(x_receiver, y_receiver, c='b')

    # Plot the intersection points
    list_intersected = np.array(intersected.get(hard_coded_source))
    plt.scatter(list_intersected[:,0], list_intersected[:,1], c='r')

    plt.show()

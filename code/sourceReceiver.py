# Generate sources and receivers
import math
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np

# Read the GML file
tree = ET.parse('./input/wegvakgeografie_simplified.gml')
root = tree.getroot()
line_segments = []
structured_segments = []

# Creates a list with line segments
for child in root.iter():
    if 'coordinates' in child.tag:
        coordinates = child.text
        line = coordinates.split()
        line_segments.append(line)
        for elem in line_segments:
            if len(elem) > 2:
                for i in range(len(elem)):
                    if i < (len(elem)-1):
                        first_el = elem[i]
                        second_el = elem[i + 1]
                        line_segments.append([first_el, second_el])
                line_segments.remove(elem)

temp_point = [ ]
structured_lines = [ ]
# input is a list with line segments
# output is a single line segment that can be tested for intersection
for segment in line_segments:
    for point in segment:
        coord = point.split(',')
        gml_point = [coord[0], coord[1]]
        if len(temp_point) < 2:
            temp_point.append(gml_point)
        if len(temp_point) == 2:
            #print([temp_point[0], temp_point[1]])
            structured_lines.append([temp_point[0], temp_point[1]])
            temp_point.clear()

angle = 2.0 * (math.pi / 180) 
cnossos_radius = 2000.0
base_angle = 0.0
lines_per_circle = [ ]
angle_st = 2.0
start_st = 0.0

hard_coded_source = [93450, 445000]
hard_coded_line = [[93450, 445000], [94500, 43500]]

def return_points_circle(centre, radius, radians):
    # input = receiver point, radius and the angle size
    # output = next point on circumsfere
    x_next = centre[0] + radius * math.cos(radians)
    y_next = centre[1] + radius * math.sin(radians)
    next_point = [x_next, y_next]
    return next_point

def return_line_segments_receiver(centre, start, step, base):
    # input = receiver point
    # output = all receiver line segments
    while start < 360:
        next_angle = base * (math.pi / 180)
        following = return_points_circle(hard_coded_source, cnossos_radius, next_angle)
        lines_per_circle.append([centre, following])
        base += step
        start += step
    return lines_per_circle

intersected_points = [ ]
def return_point_intersection(line1, line2):
    # input = two line segments, line1 = (p1, p2), line2 = (p3, p4)
    # output = intersection point of the two line segments
    xdiff = (float(line1[0][0]) - float(line1[1][0]), float(line2[0][0]) - float(line2[1][0]))
    ydiff = (float(line1[0][1]) - float(line1[1][1]), float(line2[0][1]) - float(line2[1][1]))

    def det(a, b):
        return float(a[0]) * float(b[1]) - float(a[1]) * float(b[0])

    div = det(xdiff, ydiff)
    d = (det(*line1), det(*line2))
    if div != 0:
        x = det(d, xdiff) / div
        y = det(d, ydiff) / div
        return [x, y]

dict_intersection = { }
list_intersection = [ ]
count = 0

# Check for every source line segment whether it intersects with source line segments
hard_coded_lines = return_line_segments_receiver(hard_coded_source, start_st, angle_st, base_angle)
#print("circle lines", hard_coded_lines)
#print("structured_lines", structured_lines)
for circle_line in hard_coded_lines:
    for struct_line in structured_lines:
        #print("circle line:", circle_line, "with struct line:", struct_line)
        point_intersection = return_point_intersection(circle_line, struct_line)
        #print("this is their intersection:", intersection)
        if point_intersection not in list_intersection and point_intersection is not None:
            list_intersection.append(point_intersection)

# Save all the intersection points in dictionary
hard_coded_source = tuple(hard_coded_source)
dict_intersection[hard_coded_source] = list_intersection
list_intersection = np.array(list_intersection)
#print(list_intersection[:,1])

plt.scatter(hard_coded_source[0], hard_coded_source[1])
plt.scatter(list_intersection[:,0], list_intersection[:,1])

plt.show()
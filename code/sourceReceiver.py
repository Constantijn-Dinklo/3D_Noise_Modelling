import math
import xml.etree.cElementTree as ET
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
from pprint import pprint

class ReceiverPoint:

    def __init__(self, xml_file, receiver_location):
        self.x = receiver_location[0]
        self.y = receiver_location[1]

    def read_gml(path):
        """
        Explanation: Reads a XML file
        ---------------
        Input:
        path : path to the XML file itself
        ---------------
        Output:
        root : root of the XML file
        """
        tree = ET.parse(path)
        root = tree.getroot()
        return root

    structured_segments = [ ]
    def return_segments_source(root):
        """
        Explanation: Changes the data structure of the coordinates from strings to floats in tuples
        ---------------
        Input:
        root : the root of the XML file
        ---------------
        Output:
        list : a list of all the coordinates are saved as (x, y), line segments with every next point in list
        """
        count = 0
        sets = [ ]
        all_points = [ ]
        line_string = [ ]
        line_float = [ ]
        line_segments = [ ]
        for child in root.iter():
            if "coordinates" in child.tag:
                coordinates = child.text
                line_string = coordinates.split()
                if len(line_string) > 1:
                    for point in line_string:
                        coord = point.split(',') 
                        sets.append((float(coord[0]), float(coord[1])))
                        all_points.append((float(coord[0]), float(coord[1])))
                        count += 1
                        if len(line_string) == count:
                            line_float.append(sets)
                            count = 0
                            sets = [ ]
        for elem in line_float:
            if len(elem) == 2:
                line_segments.append(elem)
            if len(elem) > 2:
                for i in range(len(elem) -1):
                    first_el = elem[i]
                    next_el = elem[i + 1]
                    new_elem = first_el, next_el
                    line_segments.append([first_el, next_el])
        return line_segments

    def return_points_circle(self, radius, radians):
        """
        Explanation: takes the noise receiver and returns the next point on the circumsphere of the user set radius
        ---------------
        Input:
        self : tuple of coordinates of the receiver point
        radius : is the user set radius around the receiver point
        radians : the size of the angle in radians between two points on the circumsphere
        ---------------
        Output:
        point : it returns the next point on the circumsphere in (x, y)
        """
        x_next = self[0] + radius * math.cos(radians)
        y_next = self[1] + radius * math.sin(radians)
        return (x_next, y_next)

    def return_segments_receiver(self):
        """
        Explanation: takes the noise receiver and returns line segments from the receiver to the points on the circumsphere
        ---------------
        Input:
        self : tuple of coordinates of the receiver point
        start : start of the circle, when 360 is reached the whole circle is checked
        step : the step of degrees that will be added after every iteration
        base : angle in degrees that will be increased by the step every iteration
        ---------------
        Output:
        list : the function returns a list from the receiver point to the points on the circumsphere
        """
        start = 0.0
        base = 0.0
        step = 2.0
        
        lines_per_circle = [ ]
        while start < 360:
            next_angle = base * (math.pi / 180)
            following = ReceiverPoint.return_points_circle(self, cnossos_radius, next_angle)
            lines_per_circle.append((self, following))
            base += step
            start += step
        return lines_per_circle

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

    def return_dictionary(receiver_list, source_list):
        """
        Explanation: for every line segment of the receiver an intersection per line segment of the source is checked
        ---------------
        Input:
        line1: list with the line segments of the receiver
        line2: list with the line segments of the source
        ---------------
        Output:
        dictionary : a list of source points (intersection points) are saved as a value to the receiver point as a key in a dictionary
        """        
        dict_intersection = { }
        list_intersection = [ ]
        for circle_line in receiver_list:
            for struct_line in source_list:
                point_intersection = ReceiverPoint.line_intersect(circle_line, struct_line)
                if point_intersection not in list_intersection and point_intersection is not None:
                    list_intersection.append(point_intersection)
        dict_intersection[hard_coded_source] = list_intersection
        return dict_intersection

if __name__ == '__main__':
    hard_coded_source = (93550, 442000)
    cnossos_radius = 100.0
    cnossos_angle = 2.0 * (math.pi / 180)

    doc = ReceiverPoint.read_gml('/Users/mprusti/Documents/geo1101/wegvakgeografie_simplified.gml') # eventually global, now local
    source_lines = ReceiverPoint.return_segments_source(doc)
    receiver_lines = ReceiverPoint.return_segments_receiver(hard_coded_source)
    intersected = ReceiverPoint.return_dictionary(source_lines, receiver_lines)

    # Plot the source line segments
    source_lines = np.array(source_lines)
    #pprint(source_lines)
    for line in source_lines:
        plt.plot(line[:,0], line[:,1])
    
    # Plot the receiver line segments
    receiver_lines = np.array(receiver_lines)
    #pprint(receiver_lines)
    for line in receiver_lines:
        plt.plot(line[:,0], line[:,1])

    # Plot the intersection points
    list_intersected = np.array(intersected.get(hard_coded_source))
    plt.scatter(list_intersected[:,0], list_intersected[:,1], c='r')
    plt.show()
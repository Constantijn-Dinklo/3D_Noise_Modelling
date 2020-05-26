import math
import xml.etree.cElementTree as ET
import matplotlib.pyplot as plt
import numpy as np
from pprint import pprint


class ReceiverPoint:

    def __init__(self, receiver, radius, step_angle):
        self.receiver = receiver
        self.radius = radius
        self.step_angle = step_angle
        self.road_lines = []
        self.receiver_segments = []

    def return_list_receivers(self, path):
        """
        Explanation: Reads a shapefile and returns a list of receiver points
        ---------------
        Input:
        path : string - the path of the shapefile
        ---------------
        Output:
        list : list - a list of all the coordinates are saved as (x, y), line segments with every next point in list
        """
        rec_list = []
        shape = fiona.open(path)
        for elem in shape:
            geometry = elem["geometry"]
            rec_pt = geometry["coordinates"]
            rec_list.append(rec_pt)
        self.receiver_segments = rec_list

    def return_segments_source(self, path):
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
        sets = []
        line_string = []
        line_float = []
        line_segments = []

        tree = ET.parse(path)
        root = tree.getroot()
        for child in root.iter():
            if "coordinates" in child.tag:
                coordinates = child.text
                line_string = coordinates.split()
                if len(line_string) > 1:
                    for point in line_string:
                        coord = point.split(',')
                        sets.append((float(coord[0]), float(coord[1])))
                        count += 1
                        if len(line_string) == count:
                            line_float.append(sets)
                            count = 0
                            sets = []
        for elem in line_float:
            if len(elem) == 2:
                line_segments.append(elem)
            if len(elem) > 2:
                for i in range(len(elem) - 1):
                    first_el = elem[i]
                    next_el = elem[i + 1]
                    new_elem = first_el, next_el
                    line_segments.append([first_el, next_el])
        self.road_lines = line_segments

    def return_points_circle(self, rcvr, radians):
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
        x_next = rcvr[0] + self.radius * math.cos(radians)
        y_next = rcvr[1] + self.radius * math.sin(radians)
        return (x_next, y_next)

    def line_intersect(self, line1, line2):
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
            return
        if not (0 <= uA <= 1 and 0 <= uB <= 1):
            return
        x = line1[0][0] + uA * (line1[1][0] - line1[0][0])
        y = line1[0][1] + uA * (line1[1][1] - line1[0][1])
        return (x, y)

    def return_intersection_points(self):
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
        list_intersection_per_ray = []
        list_intersection_per_receiver = []
        dict_per_source_segment = {}

        for rcvr in self.receiver:
            for angle in np.arange(0, (2.0 * math.pi), math.radians(self.step_angle)):
                following = self.return_points_circle(rcvr, angle)
                for struct_line in self.road_lines:
                    point_intersection = self.line_intersect((rcvr, following), struct_line)
                    if point_intersection is not None:
                        list_intersection_per_ray.append(point_intersection)
                if len(list_intersection_per_ray) >= 1:
                    sorted_list_intersection = sorted(list_intersection_per_ray, key=lambda point: (
                                                (point[0] - rcvr[0]) ** 2 + (point[1] - rcvr[1]) ** 2) ** 0.5)
                    # dict_per_source_segment[(self.receiver, following)] = sorted_list_intersection
                    list_intersection_per_receiver.append(sorted_list_intersection)
                    list_intersection_per_ray = []
            if list_intersection_per_receiver:
                dict_per_source_segment[rcvr] = list_intersection_per_receiver
            # print(dict_per_source_segment)
        return dict_per_source_segment


if __name__ == '__main__':
    hard_coded_source = (93550, 441900)
    cnossos_radius = 2000.0  # should be 2000.0 --> 2km, for now 100 is used to test
    cnossos_angle = 2.0

    doc = ReceiverPoint(hard_coded_source, cnossos_radius, cnossos_angle)
    read_doc = doc.return_segments_source('/Users/mprusti/Documents/geo1101/test_2.gml')  # eventually global, now local
    intersected = doc.return_intersection_points()

    plt.scatter(hard_coded_source[0], hard_coded_source[1], c='b')

    # Plot the source line segments
    source_lines = np.array(doc.road_lines)
    for line in source_lines:
        plt.plot(line[:, 0], line[:, 1], c='k')

    # Plot the intersection points
    intersected_points = np.array(intersected.get(hard_coded_source))
    plt.scatter(intersected_points[:, 0], intersected_points[:, 1], c='r')
    plt.show()

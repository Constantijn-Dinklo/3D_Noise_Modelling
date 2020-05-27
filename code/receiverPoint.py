import math
import xml.etree.cElementTree as ET
import matplotlib.pyplot as plt
import numpy as np
from pprint import pprint
import fiona

CNOSSOS_RADIUS = 2000.0
CNOSSOS_ANGLE = 2.0

#cnossos_radius = 2000.0 # should be 2000.0 --> 2km, for now 100 is used to test
#cnossos_angle = 2.0
#source_height = 0.05
#receiver_height = 2

class ReceiverPoint:

    def __init__(self, receiver_coords, radius = CNOSSOS_RADIUS, step_angle = CNOSSOS_ANGLE):
        self.receiver_coords = receiver_coords
        
        self.radius = radius
        self.step_angle = step_angle
        
    def return_points_circle(self, radians):
        """
        Explanation: takes the noise receiver and returns the next point on the circumsphere of the user set radius
        ---------------
        Input:
        radians : float - the size of the angle in radians between two points on the circumsphere
        ---------------
        Output:
        point : tuple - it returns the next point on the circumsphere
        """
        x_next = self.receiver_coords[0] + self.radius * math.cos(radians)
        y_next = self.receiver_coords[1] + self.radius * math.sin(radians)
        return (x_next, y_next)

    def line_intersect(self, line1, line2):
        """
        Explanation: this functions returns the intersection points (source points) of both lines
        ---------------
        Input:
        line1: list - the line segment of the receiver point
        line2: list - the line segment of the source
        ---------------
        Output:
        point : tuple - it returns the point where both line segments intersect
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

    def return_intersection_points(self, road_lines):
        """
        Explanation: for every line segment of the receiver an intersection per line segment of the source is checked
        ---------------
        Input:
        void
        ---------------
        Output:
        dictionary : a list of source points (intersection points) are saved as a value to the receiver point as a key
        in a dictionary
        """

        intersection_points = {}

        #for rcvr in self.receiver_points:
        for angle in np.arange(0, (2.0 * math.pi), math.radians(self.step_angle)):
            #Get the end point of the line at this angle from the receiver to the edge of the receiver's area
            following = self.return_points_circle(angle)

            #Create a line from receiver to end point
            current_receiver_line = [self.receiver_coords, following] #A list for now, since struct_line is also a list.
            
            list_intersection_per_ray = []
            #Check all line segments for intersection points from this angle
            for struct_line in road_lines:
                point_intersection = self.line_intersect(current_receiver_line, struct_line)
                if point_intersection is not None:
                    list_intersection_per_ray.append(point_intersection)
            
            #If at least 1 intersection point was found, store it.
            if len(list_intersection_per_ray) >= 1:
                #Sort the interection points based on how far they are from the receiver point
                sorted_list_intersection = sorted(list_intersection_per_ray, key=lambda point: (
                                            (point[0] - self.receiver_coords[0]) ** 2 + (point[1] - self.receiver_coords[1]) ** 2) ** 0.5)

                intersection_points[following] = sorted_list_intersection

        return intersection_points


def return_segments_source(path):
    """
    Explanation: Changes the data structure of the coordinates from strings to floats in tuples
    ---------------
    Input:
    path : string - the path of the XML file
    ---------------
    Output:
    list : list - a list of all the coordinates are saved as (x, y), line segments with every next point in list
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
                line_segments.append([first_el, next_el])
    return line_segments

if __name__ == '__main__':
    hard_coded_source = (93550, 441900)
    cnossos_radius = 2000.0
    cnossos_angle = 2.0

    doc = ReceiverPoint(hard_coded_source, cnossos_radius, cnossos_angle)
    road_lines = return_segments_source('/Users/mprusti/Documents/geo1101/test_2.gml')  # eventually global, now local
    #doc.return_list_receivers('/Users/mprusti/Documents/geo1101/receiver_points/toetspunten/Toetspunten_rdam.shp')
    intersected = doc.return_intersection_points(road_lines)  # --> this is a dictionary

    #--------------------------------------------------------------------------------------------#
    #                                                                                            #
    #                                  REDO GRAPHS                                               #
    #                                                                                            #
    #--------------------------------------------------------------------------------------------#
    
    # Plot the source line segments
    source_lines = np.array(doc.road_lines)
    for line in source_lines:
        plt.plot(line[:, 0], line[:, 1], c='k')

    # Plot the receiver line segments
    receiver_pts = np.array(doc.receiver_segments)
    for pts in receiver_pts:
        plt.scatter(pts[0], pts[1], c='g')

    # Plot the intersection points
    temp_list = []
    for key in intersected.keys():
        list_of_values = intersected[key]
        for value in list_of_values:
            temp_list.append(value)
    intersected_points = np.array(temp_list)
    plt.scatter(intersected_points[:, 0], intersected_points[:, 1], c='r')

    # plt.show()

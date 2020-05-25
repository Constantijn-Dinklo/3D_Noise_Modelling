import math
import xml.etree.cElementTree as ET
import matplotlib.pyplot as plt
import numpy as np
from pprint import pprint
import fiona

class ReceiverPoint:

    def __init__(self, receiver, radius, step_angle):
        self.receiver = receiver
        self.radius = radius
        self.step_angle = step_angle
        self.road_lines = [ ]
        self.receiver_segments = [ ]

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
        rec_list = [ ]
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
        path : string - the path of the XML file
        ---------------
        Output:
        list : list - a list of all the coordinates are saved as (x, y), line segments with every next point in list
        """
        count = 0
        sets = [ ]
        line_string = [ ]
        line_float = [ ]
        line_segments = [ ]

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
        self.road_lines = line_segments

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
        x_next = self.receiver[0] + self.radius * math.cos(radians)
        y_next = self.receiver[1] + self.radius * math.sin(radians)
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

    def return_intersection_points(self):
        """
        Explanation: for every line segment of the receiver an intersection per line segment of the source is checked
        ---------------
        Input:
        void
        ---------------
        Output:
        dictionary : key is the receiver line segment, value is a list of intersection point from nearby to far away
        """        
        dict_intersection = { }
        list_intersection = [ ]
        dict_per_source_segment = { }

        for rcvr in self.receiver_segments:
            for angle in np.arange(0, (2.0 * math.pi), math.radians(self.step_angle)):
                following = self.return_points_circle(angle)
                for struct_line in self.road_lines:
                    point_intersection = self.line_intersect((rcvr, following), struct_line)
                    if point_intersection is not None:
                        list_intersection.append(point_intersection)
                if len(list_intersection) >= 1:
                    sorted_list_intersection = sorted(list_intersection, key = lambda point: ((point[0] - rcvr[0])**2 + (point[1] - rcvr[1])**2)**0.5)
                    dict_per_source_segment[(rcvr, following)] = sorted_list_intersection
                    list_intersection = [ ]
        #print(dict_per_source_segment)
        return dict_per_source_segment

if __name__ == '__main__':
    hard_coded_source = (93550, 441900)
    cnossos_radius = 2000.0 
    cnossos_angle = 2.0 

    doc = ReceiverPoint(hard_coded_source, cnossos_radius, cnossos_angle)
    read_doc = doc.return_segments_source('/Users/mprusti/Documents/geo1101/test_2.gml') # eventually global, now local
    doc_rec = doc.return_list_receivers('/Users/mprusti/Documents/geo1101/receiver_points/toetspunten/Toetspunten_rdam.shp')
    intersected = doc.return_intersection_points() # --> this is a dictionary

    # Plot the source line segments
    source_lines = np.array(doc.road_lines)
    for line in source_lines:
        plt.plot(line[:,0], line[:,1], c='k')

    # Plot the receiver line segments
    receiver_pts = np.array(doc.receiver_segments)
    for pts in receiver_pts:
        plt.scatter(pts[0], pts[1], c='g')

    # Plot the intersection points
    temp_list = [ ]
    for key in intersected.keys():
        list_of_values = intersected[key]
        for value in list_of_values:
            temp_list.append(value)
    intersected_points = np.array(temp_list)
    plt.scatter(intersected_points[:,0], intersected_points[:,1], c='r')

    #plt.show()
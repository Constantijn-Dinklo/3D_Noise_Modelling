import fiona
import math
import matplotlib.pyplot as plt
import numpy as np
import xml.etree.cElementTree as ET
from misc import get_rotated_point, x_line_intersect

from sourcePoint import SourcePoint

from pprint import pprint
from shapely.geometry import Polygon, LineString, Point

CNOSSOS_RADIUS = 2000.0
CNOSSOS_ANGLE = 2.0

class ReceiverPoint:

    def __init__(self, receiver_coords, radius = CNOSSOS_RADIUS, step_angle = CNOSSOS_ANGLE):
        self.receiver_coords = receiver_coords
        
        self.radius = radius
        self.step_angle = step_angle

        self.source_points = {} #Source points per ray cast
        
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

    def find_intersection_points(self, road_lines):
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

        #for rcvr in self.receiver_points:
        step_angle_radians = math.radians(self.step_angle)
        for angle in np.arange(0, (2.0 * math.pi), step_angle_radians):
            #Get the end point of the line at this angle from the receiver to the edge of the receiver's area
            following = self.return_points_circle(angle)

            #Create a line from receiver to end point
            current_receiver_line = LineString((self.receiver_coords, following))

            # Find roads within a certain buffer from ray
            query_geom = current_receiver_line.buffer(1)  # 1 m buffer around ray
            chosen_roads = road_lines.query(query_geom)
            
            list_intersection_per_ray = []
            #Check all line segments for intersection points from this angle
            for struct_line in chosen_roads:
                if current_receiver_line.intersects(struct_line):
                    point_intersection = current_receiver_line.intersection(struct_line)
                    source_coords = list(point_intersection.coords)[0]
                    source_pt = SourcePoint(source_coords)
                    list_intersection_per_ray.append(source_pt)
                    
                    #Calculate the left and right segment length
                    # find the point on the radius circle for 1 degree left and right ( can be optimized more)
                    point_left = self.return_points_circle(angle + (step_angle_radians / 2.0))
                    point_right = self.return_points_circle(angle - (step_angle_radians / 2.0))

                    # make a (virtual) intersection with the same road element on both sides
                    point_left = np.array(x_line_intersect([self.receiver_coords, point_left], struct_line.coords))
                    point_right = np.array(x_line_intersect([self.receiver_coords, point_right], struct_line.coords))

                    # Get the vector (length) of the line between the left and right point
                    vector = point_left - point_right
                    segment_length = (vector[0] ** 2 + vector[1] ** 2) ** 0.5

                    #Set the segment lengths
                    source_pt.left_length = segment_length / 2
                    source_pt.right_length = segment_length / 2
            
            #If at least 1 intersection point was found, store it.
            if len(list_intersection_per_ray) >= 1:
                #Sort the interection points based on how far they are from the receiver point
                sorted_list_intersection = sorted(list_intersection_per_ray, key=lambda point: (
                                            (point.source_coords[0] - self.receiver_coords[0]) ** 2 + (point.source_coords[1] - self.receiver_coords[1]) ** 2) ** 0.5)

                self.source_points[following] = sorted_list_intersection

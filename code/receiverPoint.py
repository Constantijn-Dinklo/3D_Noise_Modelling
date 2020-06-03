import math
import xml.etree.cElementTree as ET
import matplotlib.pyplot as plt
import numpy as np
from pprint import pprint
from shapely.geometry import Polygon, LineString, Point
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
            current_receiver_line = LineString((self.receiver_coords, following))

            # Find roads within a certain buffer from ray
            query_geom = current_receiver_line.buffer(1)  # 1 m buffer around ray
            chosen_roads = road_lines.query(query_geom)
            
            list_intersection_per_ray = []
            #Check all line segments for intersection points from this angle
            for struct_line in chosen_roads:
                if current_receiver_line.intersects(struct_line):
                    point_intersection = current_receiver_line.intersection(struct_line)
                    list_intersection_per_ray.append(list(point_intersection.coords)[0])
            
            #If at least 1 intersection point was found, store it.
            if len(list_intersection_per_ray) >= 1:
                #Sort the interection points based on how far they are from the receiver point
                sorted_list_intersection = sorted(list_intersection_per_ray, key=lambda point: (
                                            (point[0] - self.receiver_coords[0]) ** 2 + (point[1] - self.receiver_coords[1]) ** 2) ** 0.5)

                intersection_points[following] = sorted_list_intersection

        return intersection_points

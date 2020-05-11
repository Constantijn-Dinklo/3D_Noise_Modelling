import fiona
import math
import matplotlib.pyplot as plt

class ReflectionPath:

    def __init__(self,sources,receivers,footprints):
        self.sources = sources
        self.receivers = receivers
        self.footprints = footprints

    def get_line_equation(self,p1,p2):
        """
        Explanation:
        A function that reads two points and returns the ABC parameters of the line composed by these points.
        Input:
        p1 [x(float),y(float)] and p2 [x(float),y(float)]
        Output:
        parameters [a_norm(float),b_norm(float),c_norm(float)]
        """
        # EQUATION OF A LINE IN THE 2D PLANE:
        # A * x + B * y + C = 0
        a = p2[1] - p1[1]
        b = -(p2[0] - p1[0])
        c = -a*p1[0] -b*p1[1]
        m = math.sqrt(a*a + b*b)
        a_norm = a/m
        b_norm = b/m
        c_norm = c/m
        # EQUATION OF A LINE IN THE 2D PLANE WITH NORMALISED (UNIT) NORMAL VECTORs:
        # A' * x + B' * y + C' = 0
        parameters = [a_norm,b_norm,c_norm]
        return parameters # THE PARAMETERS OF THE NORMALISED LINE.

    def get_mirror_point(self,p1,parameters):
        """
        Explanation:
        A function that reads a point and the parameters of a line and returns the mirror point of p1 regarding this line.
        Input:
        p1 [x(float),y(float)]
        parameters [a_norm(float),b_norm(float),c_norm(float)]
        Output:
        p_mirror [x(float),y(float)]
        """
        # THE SIGNED DISTANCE D FROM P1 TO THE LINE L, I.E. THE ONE WITH THE PARAMETERS.
        d = parameters[0]*p1[0] + parameters[1]*p1[1] + parameters[2]
        p_mirror_x = p1[0] - 2*parameters[0]*d
        p_mirror_y = p1[1] - 2*parameters[1]*d
        return [p_mirror_x,p_mirror_y]

    def get_intersection(self,line1,line2):
        """
        Explanation:
        A function that takes two lines and returns the interesection point between them.
        Input:
        line 1 [[x1(float),y1(float)],[x2(float),y2(float)]]
        line 2 [[x3(float),y3(float)],[x4(float),y4(float)]]
        Output:
        point [x(float),y(float)]
        """
        xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
        ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

        def det(a, b):
            return a[0] * b[1] - a[1] * b[0]

        div = det(xdiff, ydiff)
        if div == 0:
            raise Exception('lines do not intersect')

        d = (det(*line1), det(*line2))
        x = det(d, xdiff) / div
        y = det(d, ydiff) / div
        return [x,y]

    def get_bbox(self,line):
        """
        Explanation:
        A function that takes a line and computes the bounding box of its geometry.
        Input:
        line 1 [[x1(float),y1(float)],[x2(float),y2(float)]]
        Output:
        bbox [x_min(float),x_max(float),y_min(float),y_max(float)]
        """
        p1 = line[0]
        p2 = line[1]
        x_min = min(p1[0],p2[0])
        x_max = max(p1[0],p2[0])
        y_min = min(p1[1],p2[1])
        y_max = max(p1[1],p2[1])
        bbox = [x_min,x_max,y_min,y_max]
        return bbox

    def get_paths(self,dictionary):
        """
        Explanation:
        A function that reads receivers, sources and walls and computes 1ST-ORDER propagation paths for each pair of
        source and receiver, according to the walls that (eventually) present a reflection point in its 2D line.
        Input:
        dictionary: an empty 'p_dict' dictionary in __main__, which will be filled with the info about the path
        p_dict = {
                receiver = { 
                    source = { 
                        bag_id = { 
                            'hoogte_abs' = float
                            'paths' = [ [sx,xy], [refx,refy], [rx,ry] ]
                                }
                            }
                            }
                }
        Output:
        void.
        """
        for receiver in r_dict:
            dictionary[receiver] = {}
            for source in s_dict:
                sources_dictionary = { }
                dictionary[receiver][source] = sources_dictionary
                r = r_dict[receiver]
                s = s_dict[source]
                for bag_id in f_dict:
                    bag_dictionary = { }
                    dictionary[receiver][source][bag_id] = bag_dictionary
                    hoogte_abs = f_dict[bag_id]['hoogte_abs']
                    dictionary[receiver][source][bag_id]['hoogte_abs'] = hoogte_abs
                    paths = [ ]
                    walls = f_dict[bag_id]['walls']
                    for wall in walls:
                        s_mirror = self.get_mirror_point(s,self.get_line_equation(wall[0],wall[1]))
                        ref = self.get_intersection(wall,[s_mirror,r])
                        bbox = self.get_bbox(wall)
                        if ref[0] > bbox[0] and ref[0] < bbox[1] and ref[1] > bbox[2] and ref[1] < bbox[3]:
                            ray = [s, ref, r]
                            paths.append(ray)
                    dictionary[receiver][source][bag_id]['paths'] = paths

    def write_output(self,output_file,dictionary):
        """
        Explanation:
        A function that reads a dictionary and write a 'gml' file as an output.
        Input:
        output_file: the directory/file that will be written as an output.
        p_dict in __main__, containing the geometry of the line segments.
        Output:
        void
        """
        

def read_buildings(input_file,dictionary):
    """
    Explanation:
    A function that reads footprints and stores all walls as [p1,p2] and absolute heights (float) of these.
    Input:
    input_file: a .gpkg file containing the footprints of the buildings.
    dictionary: an empty 'f_dict' dictionary in __main__
    Output:
    void.
    """
    with fiona.open(input_file) as layer:
        for feature in layer:
            bag_id = feature['properties']['bag_id']
            dictionary[bag_id] = { }
            z = feature['properties']['hoogte_abs']
            dictionary[bag_id]['hoogte_abs'] = z
            f_geom_coord = feature['geometry']['coordinates']
            for polygon_index in range(len(f_geom_coord)):
                polygon_object = f_geom_coord[polygon_index]
                walls = []
                for coord_index in range(len(polygon_object[:(len(polygon_object)-1)])):
                    a = list(polygon_object[coord_index])
                    b = list(polygon_object[coord_index+1])
                    wall_2D = [a[:len(a)-1],b[:len(b)-1]]
                    walls.append(wall_2D)
                dictionary[bag_id]['walls'] = walls
    layer.close()

def read_points(input_file,dictionary):
    """
    Explanation:
    A function that reads points and store their ids (int) and coordinates as [x,y].
    Input:
    input_file: a .gpkg file containing the points (with z coordinates)
    dictionary: an empty dictionary in __main__ (either s_dict for sources or r_dict for receivers)
    Output:
    void.
    """
    with fiona.open(input_file) as layer:
        for feature in layer:
            source_id = feature['properties']['id']
            coord_object = list(feature['geometry']['coordinates'])
            dictionary[source_id] = coord_object[:len(coord_object)-1]
    layer.close()

if __name__ == "__main__":
    f_dict = { }
    s_dict = { }
    r_dict = { }
    p_dict = { }
    read_buildings('file:///Users/denisgiannelli/Desktop/Buildings1.gpkg',f_dict)
    read_points('file:///Users/denisgiannelli/Desktop/Sources1.gpkg',s_dict)
    read_points('file:///Users/denisgiannelli/Desktop/Receivers1.gpkg',r_dict)
    reflection_path = ReflectionPath(s_dict,r_dict,f_dict)
    reflection_path.get_paths(p_dict)
    print(p_dict)
    #write_output('',p_dict)
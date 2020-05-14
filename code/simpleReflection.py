import fiona
import math
import misc

class ReflectionPath:

    def __init__(self,sources,receivers,footprints):
        self.sources = sources
        self.receivers = receivers
        self.footprints = footprints

    def get_line_equation(self,p1,p2):
        """
        Explanation:A function that reads two points and returns the ABC parameters of the line composed by these points.
        ---------------
        Input:
        p1 [x(float),y(float)]
        p2 [x(float),y(float)]
        ---------------
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
        Explanation: A function that reads a point and the parameters of a line and returns the mirror point of p1 regarding this line.
        ---------------
        Input:
        p1 [x(float),y(float)]
        parameters [a_norm(float),b_norm(float),c_norm(float)]
        ---------------
        Output:
        p_mirror [x(float),y(float)]
        """
        # THE SIGNED DISTANCE D FROM P1 TO THE LINE L, I.E. THE ONE WITH THE PARAMETERS.
        d = parameters[0]*p1[0] + parameters[1]*p1[1] + parameters[2]
        p_mirror_x = p1[0] - 2*parameters[0]*d
        p_mirror_y = p1[1] - 2*parameters[1]*d
        return [p_mirror_x,p_mirror_y]

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
        d = (line2[1][1] - line2[0][1]) * (line1[1][0] - line1[0][0]) - (line2[1][0] - line2[0][0]) * (line1[1][1] - line1[0][1])
        if d:
            uA = ((line2[1][0] - line2[0][0]) * (line1[0][1] - line2[0][1]) - (line2[1][1] - line2[0][1]) * (line1[0][0] - line2[0][0])) / d
            uB = ((line1[1][0] - line1[0][0]) * (line1[0][1] - line2[0][1]) - (line1[1][1] - line1[0][1]) * (line1[0][0] - line2[0][0])) / d
        else:
            return False
        if not(0 <= uA <= 1 and 0 <= uB <= 1):
            return False 
        x = line1[0][0] + uA * (line1[1][0] - line1[0][0])
        y = line1[0][1] + uA * (line1[1][1] - line1[0][1])
        return [x,y]

    def get_paths(self,s,r):
        """
        Explanation: A function that reads a source point and a receiver and computes all possible first-order reflection paths,
        according to buildings that are stored in f_dict (separate dictionary)
        ---------------        
        Input:
        source s    [x,y,(z)]
        receiver r  [x,y,(z)]
        ---------------
        Output:
        A list of all (independent) points that are capable of reflecting the sound wave from source to receiver.:
        l = [ [ p1, p2, p3, .... pn ] , [ h1, h2, h3, .... hn ] ]
        such that:
        p = [x(float),y(float)]
        h = value(float)
        the n-th element of "p_list" corresponds to the n-th element of "h_list".
        """
        coords   = [ ]
        heights  = [ ]
        for bag_id in f_dict:
            hoogte_abs = f_dict[bag_id]['hoogte_abs']
            walls = f_dict[bag_id]['walls']
            for wall in walls:
                test_r = misc.side_test( wall[0], wall[1], r[:2]) #r[:2] makes the function to ignore an eventual 'z' value.
                test_s = misc.side_test( wall[0], wall[1], s[:2]) #s[:2] makes the function to ignore an eventual 'z' value.
                if test_r > 0 and test_s > 0: # This statement guarantees that S-REF and REF-R are entirely outside the polygon.
                    s_mirror = self.get_mirror_point(s,self.get_line_equation(wall[0],wall[1]))
                    ref = self.line_intersect(wall,[s_mirror,r])
                    if type(ref) == list:
                        coords.append(ref)
                        heights.append(hoogte_abs)
                        ref_z = ref
                        ref_z.append(hoogte_abs)
                        p_list.append([s,ref_z,r])
        return [ coords, heights ] #[ [p1, p2, ..., pn], [h1, h2, ..., hn] ] 

def read_buildings(input_file,dictionary):
    """
    Explanation: A function that reads footprints and stores all walls as [p1,p2] and absolute heights (float) of these.
    ---------------
    Input:
    input_file: a .gpkg file containing the footprints of the buildings.
    dictionary: an empty 'f_dict' dictionary in __main__
    ---------------
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
    Explanation: A function that reads points and store their ids (int) and coordinates as [x,y].
    ---------------
    Input:
    input_file: a .gpkg file containing the points (with z coordinates)
    dictionary: an empty dictionary in __main__ (either s_dict for sources or r_dict for receivers)
    ---------------
    Output:
    void.
    """
    with fiona.open(input_file) as layer:
        for feature in layer:
            source_id = feature['properties']['id']
            coord_object = list(feature['geometry']['coordinates'])
            dictionary[source_id] = coord_object#[:len(coord_object)-1]
    layer.close()

def write_output(output_file,lista):
    """
    Explanation: A function that writes a CSV file with the reflected paths. It is used for visualising the paths in QGIS.
    ---------------
    Input:
    output_file: the directory/name of the csv file to be created.
    lista: a list containing all the 1st order propagation paths in the following schema:
    [ [source_x, source_y, source_z,] , [reflection_x, reflection_y, hoogte_abs], [receiver_x, receiver_y, receiver_z] ] 
    ---------------
    Output:
    void.
    """
    fout = open(output_file,'w')
    line = 'fid \t geometry \n'
    fout.write(str(line))
    count = 0
    for path in lista:
        count += 1
        sou = path[0]
        ref = path[1]
        rec = path[2]
        line = '%d \t MultiLineStringZ ((%f %f %f, %f %f %f, %f %f %f)) \n' % (count,sou[0],sou[1],sou[2],ref[0],ref[1],0,rec[0],rec[1],rec[2]) 
        fout.write(line)
    fout.close()
    #MultiLineStringZ ((93528.02305619 441927.11005859 2.5, 93567.67848824 441908.81858497 0, 93539.68248698 441892 1.4))

if __name__ == "__main__":
    f_dict = { }
    s_dict = { }
    r_dict = { }
    p_list = [ ]
    
    # DATASETS FOR 'SCENARIO 000'
    read_buildings('//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/06_DATA/01_Scenarios/scenario000/Building Data/lod10/p75/37fz1_lod10_p75/pand.gpkg',f_dict)
    read_points('//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/06_DATA/01_Scenarios/scenario000/Sources/Sources1.gpkg',s_dict)
    read_points('//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/06_DATA/01_Scenarios/scenario000/Receivers/Receivers1.gpkg',r_dict)
    
    reflection_path = ReflectionPath(s_dict,r_dict,f_dict)

    for source in s_dict:
        for receiver in r_dict:
            print('source:',source,'receiver',receiver)
            print('number of paths:',len(reflection_path.get_paths(s_dict[source],r_dict[receiver])[0]))
            for el in reflection_path.get_paths(s_dict[source],r_dict[receiver]):
                print(el)
            print()

    for path in p_list:
        print(path)
    print(len(p_list))

    write_output('//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/06_DATA/01_Scenarios/scenario000/path.csv',p_list)
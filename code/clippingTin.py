import xml.etree.ElementTree as ET
from time import time

# THESE ARE THE EMPTY LISTS AND DICTIONARIES THAT WILL BE USED IN THE PROGRAM
v_list_input = [ ] # The list in whihc the vertices from the input file are stored.
f_list_input = [ ] # The list in which the faces from the input file are stores.

v_list_output = [ ] # The list in which the vertices for the output file are stored.
v_dict_output = { } # The dictionary that is used to check if a vertice has already been added to v_list_output.

f_list_output = [ ] # The list in which the faces for the output file are stored.
f_dict_output = { } # The dictionary that is used to check if a face has already been added to f_list_output.

bbox = [ ] # The bounding box that is being taken into consideration for the clipping process.

def get_bbox(input_file):
    """
    Explination:
    A function that defines the bounding box of the area to be clipped.
    It requires ElementTree.
    Input:
    input_file: a GML file containing one feature (the bounding box as a polygon).
    Output:
    void: it appends the x & y min. and max. values to the external bbox list.
    """
    x_list = [ ]
    y_list = [ ]
    root_dict = { }
    tree = ET.parse(input_file)
    root = tree.getroot()
    for child in root.iter():
        root_dict[child.tag] = child.text
    for tag in root_dict:
        if 'coordinates' in tag:
            coord_list = root_dict[tag].split()
            for coord in coord_list[:len(coord_list)-1]:
                x = float(coord.split(',')[0])
                y = float(coord.split(',')[1])
                if x not in x_list:
                    x_list.append(x)
                if y not in y_list:
                    y_list.append(y)
    bbox.append(min(x_list))
    bbox.append(max(x_list))
    bbox.append(min(y_list))
    bbox.append(max(y_list))

def read_obj(input_file):
    """
    Explination:
    A function that reads the input file.
    Input:
    An .obj file containing the TIN surface.
    Output:
    void: it appends the vertices and faces to the external v_list_input and f_list_input, respectively.
    """
    fin = open(input_file,'r')
    for line in fin:
        if line[0] == 'v':
            line_list = line.split()
            vertex = [float(line_list[1]), float(line_list[2]), float(line_list[3])]
            v_list_input.append(vertex)
        if line[0] == 'f':
            line_list = line.split()
            face = [int(line_list[1])-1, int(line_list[2])-1, int(line_list[3])-1]
            f_list_input.append(face)
    fin.close()

def orientation_test(ax,ay,bx,by,px,py):
    """
    Explination:
    An auxiliary function that tests in which side of a line segment a point lies into.
    Input:
    AB is the line segment and P is the point: all six values (3 x values / 3 y values) are float numbers.
    Output:
    'value': a float number that can be positive / zero / negative.
    """
    value = ( ax*by + ay*px + bx*py ) - ( by*px + ax*py + ay*bx )
    return value

def clipping():
    """
    Explination:
    The main function of the program. For each face (triangle) in f_list_input, the function tests is it lies
    at least partially in the previously created bounding box.
    CASE 1 verifies if at least one of the vertices is either in the interior or on the boundary of the bbox.
    CASE 2 verifies if part of the triangle is inside / on the boundary of the bbox, despite all three vertices
    are outside of it.
    The function makes use of external dictionaries to check if the triangle has already been considered in order
    to avoid duplicated features.
    Input:
    No input: it reads the external lists and dictionaries.
    Output:
    Void: it appends the 'clipped' vertices and faces into v_list_output and f_list_output, respectively.
    """
    for f_index in range(len(f_list_input)):
        f_object =  f_list_input[f_index]
        vertex_a = f_object[0]
        vertex_b = f_object[1]
        vertex_c = f_object[2]
        ax = v_list_input[vertex_a][0]
        ay = v_list_input[vertex_a][1]
        az = v_list_input[vertex_a][2]
        bx = v_list_input[vertex_b][0]
        by = v_list_input[vertex_b][1]
        bz = v_list_input[vertex_b][2]
        cx = v_list_input[vertex_c][0]
        cy = v_list_input[vertex_c][1]
        cz = v_list_input[vertex_c][2]

        # CASE 1: AT LEAST ONE VERTEX IS EITHER IN THE INTERIOR OR ON THE BOUNDARY OF THE BBOX.
        
        # CASE 1.A: TESTING IF VERTEX A IS WITHIN THE BBOX
        if ax >= bbox[0] and ax <= bbox[1] and ay >= bbox[2] and ay <= bbox[3]:
            if (ax,ay,az) in v_dict_output.keys():
                pass
            else:
                v_list_output.append([ax,ay,az])
                v_dict_output[(ax,ay,az)] = len(v_list_output)-1
            if (bx,by,bz) in v_dict_output.keys():
                pass
            else:
                v_list_output.append([bx,by,bz])
                v_dict_output[(bx,by,bz)] = len(v_list_output)-1
            if (cx,cy,cz) in v_dict_output.keys():
                pass
            else:
                v_list_output.append([cx,cy,cz])
                v_dict_output[(cx,cy,cz)] = len(v_list_output)-1
                     
            face = [ v_dict_output[(ax,ay,az)] , v_dict_output[(bx,by,bz)] , v_dict_output[(cx,cy,cz)] ]
            if face in f_dict_output.values():
                pass
            else:
                f_dict_output[''] = face
                f_list_output.append(face)

        # CASE 1.B: TESTING IF VERTEX B IS WITHIN THE BBOX
        if bx >= bbox[0] and bx <= bbox[1] and by >= bbox[2] and by <= bbox[3]:
            if (ax,ay,az) in v_dict_output.keys():
                pass
            else:
                v_list_output.append([ax,ay,az])
                v_dict_output[(ax,ay,az)] = len(v_list_output)-1
            if (bx,by,bz) in v_dict_output.keys():
                pass
            else:
                v_list_output.append([bx,by,bz])
                v_dict_output[(bx,by,bz)] = len(v_list_output)-1
            if (cx,cy,cz) in v_dict_output.keys():
                pass
            else:
                v_list_output.append([cx,cy,cz])
                v_dict_output[(cx,cy,cz)] = len(v_list_output)-1
            
            face = [ v_dict_output[(ax,ay,az)] , v_dict_output[(bx,by,bz)] , v_dict_output[(cx,cy,cz)] ]
            if face in f_dict_output.values():
                pass
            else:
                f_dict_output[''] = face
                f_list_output.append(face)

        # CASE 1.C: TESTING IF VERTEX C IS WITHIN THE BBOX
        if cx >= bbox[0] and cx <= bbox[1] and cy >= bbox[2] and cy <= bbox[3]:
            if (ax,ay,az) in v_dict_output.keys():
                pass
            else:
                v_list_output.append([ax,ay,az])
                v_dict_output[(ax,ay,az)] = len(v_list_output)-1
            if (bx,by,bz) in v_dict_output.keys():
                pass
            else:
                v_list_output.append([bx,by,bz])
                v_dict_output[(bx,by,bz)] = len(v_list_output)-1
            if (cx,cy,cz) in v_dict_output.keys():
                pass
            else:
                v_list_output.append([cx,cy,cz])
                v_dict_output[(cx,cy,cz)] = len(v_list_output)-1
            
            face = [ v_dict_output[(ax,ay,az)] , v_dict_output[(bx,by,bz)] , v_dict_output[(cx,cy,cz)] ]
            if face in f_dict_output.values():
                pass
            else:
                f_dict_output[''] = face
                f_list_output.append(face)

        # CASE 2: ALL THREE VERTICES ARE OUTSIDE THE BBOX, BUT STILL THE TRIANGLE AND THE BBOX OVERLAP WITH EACH OTHER.

        #CASE 2.1: TESTING IF TRIANGLE CONTAINS BL
        if orientation_test(ax,ay,bx,by,bbox_bl[0],bbox_bl[1]) >= 0: # A B P
            if orientation_test(bx,by,cx,cy,bbox_bl[0],bbox_bl[1]) >= 0: # B C P
                if orientation_test(cx,cy,ax,ay,bbox_bl[0],bbox_bl[1]) >= 0: # C A P
                    if (ax,ay,az) in v_dict_output.keys():
                        pass
                    else:
                        v_list_output.append([ax,ay,az])
                        v_dict_output[(ax,ay,az)] = len(v_list_output)-1
                    if (bx,by,bz) in v_dict_output.keys():
                        pass
                    else:
                        v_list_output.append([bx,by,bz])
                        v_dict_output[(bx,by,bz)] = len(v_list_output)-1
                    if (cx,cy,cz) in v_dict_output.keys():
                        pass
                    else:
                        v_list_output.append([cx,cy,cz])
                        v_dict_output[(cx,cy,cz)] = len(v_list_output)-1
                            
                    face = [ v_dict_output[(ax,ay,az)] , v_dict_output[(bx,by,bz)] , v_dict_output[(cx,cy,cz)] ]
                    if face in f_dict_output.values():
                        pass
                    else:
                        f_dict_output[''] = face
                        f_list_output.append(face)                    

        #CASE 2.2: TESTING IF TRIANGLE CONTAINS BR
        if orientation_test(ax,ay,bx,by,bbox_br[0],bbox_br[1]) >= 0: # A B P
            if orientation_test(bx,by,cx,cy,bbox_br[0],bbox_br[1]) >= 0: # B C P
                if orientation_test(cx,cy,ax,ay,bbox_br[0],bbox_br[1]) >= 0: # C A P
                    if (ax,ay,az) in v_dict_output.keys():
                        pass
                    else:
                        v_list_output.append([ax,ay,az])
                        v_dict_output[(ax,ay,az)] = len(v_list_output)-1
                    if (bx,by,bz) in v_dict_output.keys():
                        pass
                    else:
                        v_list_output.append([bx,by,bz])
                        v_dict_output[(bx,by,bz)] = len(v_list_output)-1
                    if (cx,cy,cz) in v_dict_output.keys():
                        pass
                    else:
                        v_list_output.append([cx,cy,cz])
                        v_dict_output[(cx,cy,cz)] = len(v_list_output)-1
                            
                    face = [ v_dict_output[(ax,ay,az)] , v_dict_output[(bx,by,bz)] , v_dict_output[(cx,cy,cz)] ]
                    if face in f_dict_output.values():
                        pass
                    else:
                        f_dict_output[''] = face
                        f_list_output.append(face)         

        #CASE 2.3: TESTING IF TRIANGLE CONTAINS TR
        if orientation_test(ax,ay,bx,by,bbox_tr[0],bbox_tr[1]) >= 0: # A B P
            if orientation_test(bx,by,cx,cy,bbox_tr[0],bbox_tr[1]) >= 0: # B C P
                if orientation_test(cx,cy,ax,ay,bbox_tr[0],bbox_tr[1]) >= 0: # C A P
                    if (ax,ay,az) in v_dict_output.keys():
                        pass
                    else:
                        v_list_output.append([ax,ay,az])
                        v_dict_output[(ax,ay,az)] = len(v_list_output)-1
                    if (bx,by,bz) in v_dict_output.keys():
                        pass
                    else:
                        v_list_output.append([bx,by,bz])
                        v_dict_output[(bx,by,bz)] = len(v_list_output)-1
                    if (cx,cy,cz) in v_dict_output.keys():
                        pass
                    else:
                        v_list_output.append([cx,cy,cz])
                        v_dict_output[(cx,cy,cz)] = len(v_list_output)-1
                            
                    face = [ v_dict_output[(ax,ay,az)] , v_dict_output[(bx,by,bz)] , v_dict_output[(cx,cy,cz)] ]
                    if face in f_dict_output.values():
                        pass
                    else:
                        f_dict_output[''] = face
                        f_list_output.append(face)         

        #CASE 2.4: TESTING IF TRIANGLE CONTAINS TL
        if orientation_test(ax,ay,bx,by,bbox_tl[0],bbox_tl[1]) >= 0: # A B P
            if orientation_test(bx,by,cx,cy,bbox_tl[0],bbox_tl[1]) >= 0: # B C P
                if orientation_test(cx,cy,ax,ay,bbox_tl[0],bbox_tl[1]) >= 0: # C A P
                    if (ax,ay,az) in v_dict_output.keys():
                        pass
                    else:
                        v_list_output.append([ax,ay,az])
                        v_dict_output[(ax,ay,az)] = len(v_list_output)-1
                    if (bx,by,bz) in v_dict_output.keys():
                        pass
                    else:
                        v_list_output.append([bx,by,bz])
                        v_dict_output[(bx,by,bz)] = len(v_list_output)-1
                    if (cx,cy,cz) in v_dict_output.keys():
                        pass
                    else:
                        v_list_output.append([cx,cy,cz])
                        v_dict_output[(cx,cy,cz)] = len(v_list_output)-1
                            
                    face = [ v_dict_output[(ax,ay,az)] , v_dict_output[(bx,by,bz)] , v_dict_output[(cx,cy,cz)] ]
                    if face in f_dict_output.values():
                        pass
                    else:
                        f_dict_output[''] = face
                        f_list_output.append(face)     

def write_obj(output_file):
    """
    Explination:
    A function that writes the clipped TIN .obj file.
    Input:
    The new directory/name for the clipped TIN .obj file.
    Output:
    void.
    """
    # OPEN THE FILE
    fout = open(output_file,'w')
    # WRITING THE 'HEAD' OF THE OBJ FILE
    line = '# Created with Python3 Version: Python 3.7.5 64-bit'
    fout.write(line)
    # WRITING THE VERTICES
    line = '# Number of Geometry Coordinates: %d \n' % (len(v_list_output))
    fout.write(line)
    line = '# Number of Texture Coordinates: %d \n' % (0)
    fout.write(line)
    line = '# Number of Normal Coordinates: %d \n' % (0)
    fout.write(line)
    for vertex_object in v_list_output:
        line = 'v %6f %6f %6f \n' % (vertex_object[0], vertex_object[1], vertex_object[2]) 
        fout.write(line)
    line = '# Number of Elements in set: %d \n' % (len(f_list_output))
    fout.write(line)
    # WRITING FACES
    for face_object in f_list_output:
        line = 'f %d %d %d \n' % (face_object[0]+1, face_object[1]+1, face_object[2]+1) 
        fout.write(line)
    line = '# Total Number of Elements in file: %d \n' % (len(f_list_output))
    fout.write(line)
    line = '# EOF'
    fout.write(line)
    # CLOSE THE FILE
    fout.close()

def write_bbox(bbox):
    """
    Explination:
    A function that writes the clipped bounding box .obj file.
    Input:
    The new directory/name for the clipped bounding box .obj file.
    Output:
    void.
    """
    # OPEN THE FILE
    fout = open(bbox,'w')
    # WRITING BL VERTEX
    line = 'v %d %d %d \n' % (bbox_bl[0], bbox_bl[1], 0) 
    fout.write(line)
    # WRITING BR VERTEX
    line = 'v %d %d %d \n' % (bbox_br[0], bbox_br[1], 0) 
    fout.write(line)
    # WRITING TR VERTEX
    line = 'v %d %d %d \n' % (bbox_tr[0], bbox_tr[1], 0) 
    fout.write(line)
    # WRITING TR VERTEX
    line = 'v %d %d %d \n' % (bbox_tl[0], bbox_tl[1], 0) 
    fout.write(line)
    # WRITING THE BBOX (FACE)
    line = 'f %d %d %d %d \n' % (1,2,3,4) 
    fout.write(line)
    # CLOSE THE FILE
    fout.close()

if __name__ == "__main__":
    start = time()
    get_bbox('//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/06_DATA/01_Scenarios/scenario002/Bounding_Box/boundingbox_5m.gml')
    bbox_bl = [bbox[0], bbox[2]] # Xmin, Ymin
    bbox_br = [bbox[1], bbox[2]] # Xmax, Ymin
    bbox_tr = [bbox[1], bbox[3]] # Xmax, Ymax
    bbox_tl = [bbox[0], bbox[3]] # Xmin, Ymax
    read_obj("//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/06_DATA/00_InputData/Terrain data/TIN/1,0m/tin_1m.obj/37hn1.obj")
    clipping()
    print('len(v_list_input):',len(v_list_input))
    print('len(f_list_input):',len(f_list_input))
    print('len(v_list_output):',len(v_list_output))
    print('len(f_list_output):',len(f_list_output))
    write_obj('//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/06_DATA/01_Scenarios/scenario002/Terrain_Data/TIN/1,0m/tin_37hn1.obj')
    #write_bbox('//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/06_DATA/01_Scenarios/scenario002/Terrain_Data/TIN/1,0m/bbox_37hn1.obj')
    end = time()
    print(round((end - start),2),'s')
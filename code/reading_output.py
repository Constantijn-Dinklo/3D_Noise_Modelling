import os 
import xml.etree.ElementTree as ET

def read_cnossosxml(input_file):
    x_list = [ ]
    y_list = [ ]
    z_list = [ ]
    path_list = [ ]
    tree = ET.parse(input_file)
    root = tree.getroot()
    for x in root.iter('x'):
        x_list.append(float(x.text))
    for y in root.iter('y'):
        y_list.append(float(y.text))
    for z in root.iter('z'):
        z_list.append(float(z.text))
    for i in range(len(x_list)):
        path_list.append([x_list[i],y_list[i],z_list[i]])
    return path_list

def read_mesh(input_file):
    fin = open(input_file,'r')
    for line in fin:
        line_list = line.split(' ')
        if line_list[0] == 'v':
            vertex = [float(line_list[1]),float(line_list[2]),float(line_list[3][:-1])]
            v_list.append(vertex)
        if line_list[0] == 'l':
            path = [ ]
            for el in line_list[1:]:
                path.append(int(el)-1)
            p_list.append(path)

def write_from_xml_to_csv(output_file,path):
    """
    Explanation: A function that writes a CSV file with the reflected paths. It is used for visualising the paths in QGIS.
    ---------------
    Input:
    output_file: directory - the directory/name of the csv file to be created.
    path: list - a list containing all the paths in the following schema: [ [x,y,z], [x,y,z], ... [x,y,z] ]
    ---------------
    Output:
    void.
    """
    fout = open(output_file,'w')
    line = 'fid \t geometry \n'
    fout.write(str(line))
    count = 0
    pstr_list = [ ]
    for point_index in range(len(path)):
        x = path[point_index][0]
        y = path[point_index][1]
        z = path[point_index][2]
        line = '%f %f %f' % (x,y,z)
        pstr_list.append(line)
    string = ''
    for pstr_index in range(len(pstr_list)):
        if pstr_index != len(pstr_list)-1:
            string = string + pstr_list[pstr_index] + ', '
    string = string + pstr_list[len(pstr_list)-1]
    count = 1
    line = '%d \t MultiLineStringZ ((%s)) \n' % (count,string)
    fout.write(line)
    fout.close()

def write_from_obj_to_csv(output_file,v_list,p_list):
    fout = open(output_file,'w')
    line = 'fid \t geometry \n'
    fout.write(str(line))
    count = 0
    for path in p_list:
        pstr_list = [ ]
        for point in path:
            x = v_list[point][0]
            y = v_list[point][1]
            z = v_list[point][2]
            line = '%f %f %f' % (x,y,z)
            pstr_list.append(line)
        string = ''
        for pstr_index in range(len(pstr_list)):
            if pstr_index != len(pstr_list)-1:
                string = string + pstr_list[pstr_index] + ', '
        string = string + pstr_list[len(pstr_list)-1]
        count = 1
        line = '%d \t MultiLineStringZ ((%s)) \n' % (count,string)
        fout.write(line)
    fout.close()

if __name__ == "__main__":
    parent_list = os.listdir("//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/3D_Noise_Modelling/code/output/obj/")
    for child in parent_list:
        v_list = [ ]
        p_list = [ ]
        child_input = '//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/3D_Noise_Modelling/code/output/obj/'+child
        read_mesh(child_input)
        child_output = '//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/3D_Noise_Modelling/code/output/csv/'+child[:-4]+'.csv'
        write_from_obj_to_csv(child_output,v_list,p_list)
        print('child',child[:-4],'done!')
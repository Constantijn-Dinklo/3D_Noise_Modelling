import xml.etree.ElementTree as ET

BOUNDING_BOX = [ ]

def get_bounding_box(input_file):
    """
    Explination:
    A function that computes the bounding box of a feature.
    Input:
    A GML file. (input_file)
    Output:
    Void.
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
    BOUNDING_BOX.append(min(x_list))
    BOUNDING_BOX.append(max(x_list))
    BOUNDING_BOX.append(min(y_list))
    BOUNDING_BOX.append(max(y_list))

if __name__ == "__main__":
    get_bounding_box('///Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/06_DATA/01_Scenarios/scenario000/_Bounding Box/scenario000_boundingbox_int5.gml')
    print(BOUNDING_BOX)

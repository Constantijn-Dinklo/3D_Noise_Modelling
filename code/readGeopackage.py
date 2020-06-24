import fiona

def read_input(input_file):
    """
    Explination:
    A function that parses an .gpkg file and extract the attributes of its layers, especially the geometry.
    It requires fiona.
    Input:
    input_file: a .gpkg file.
    Output:
    void: for now, it is just a preliminary function for us to understand how to parse .gpkg files.
    """
    with fiona.open(input_file) as layer:
        for feature in layer:
            #print(feature)
            #for key in feature:
            #    print(key)
            #    print(feature[key])
            f_type = feature['type']
            f_id = feature['id']
            print('id',f_id)
            f_ppt = feature['properties']
            f_geom = feature['geometry']
            f_geom_type = feature['geometry']['type']
            print('geom_type',f_geom_type)
            f_geom_coord = feature['geometry']['coordinates']
            for polygon_index in range(len(f_geom_coord)):
                polygon_object = f_geom_coord[polygon_index]
                print('polygon #',polygon_index)
                print(polygon_object)
            print()

if __name__ == "__main__":
    #read_input('//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/06_DATA/01_Scenarios/scenario000/Ground type data/6 m2/tiles_bodemvlakken_6.gpkg/37fz1_bodemvlakken_6.0.gpkg')
    read_input('input/37fz1_bodemvlakken_6.0.gpkg')
import json
import sys

from pathlib import Path

class json_parse:

    def __init__(self):
        self.vts = []
        self.trs = []
        self.attr = []

        self.edges = {}

    def read_json(self, file_path):
                
        with open(file_path, 'r') as json_input_file:
            lines = json_input_file.readlines()
            #Load the json
            json_string = lines[0]
            json_dict = json.loads(json_string)

            #Assign the vertices
            self.vts = json_dict["vertices"]

            #Run through all the city json objects
            objects = json_dict["CityObjects"]
            for uuid in objects:
                constrained_object = objects[uuid]
                #print(constrained_object)
                # Get the attributes of this object
                attributes = constrained_object["attributes"]

                if 'bodemfactor' in attributes.keys():
                    id_value = 'g' + attributes["bodemfactor"]
                elif 'bodemfacto' in attributes.keys():
                    id_value = 'g' + attributes["bodemfacto"]

                #Get the identificatie of this object
                if 'part_id' in attributes.keys():
                    part_id = attributes["part_id"]
                    #If the identificatie is not empty, it is a building and this is the id used to identify the object
                    if part_id != '':
                        id_value = 'b' + part_id
                
                object_geoms = constrained_object['geometry']
                for object_geom in object_geoms:
                    object_boundaries = object_geom['boundaries']

                    for boundary in object_boundaries:
                        for triangle in boundary:
                            v1 = triangle[0]
                            v2 = triangle[1]
                            v3 = triangle[2]
                            face = [v1, v2, v3, -1, -1, -1]

                            #The index this triangle will be at
                            tri_index = len(self.trs)

                            edge1 = [v1, v2]
                            edge1.sort()
                            edge1 = (edge1[0], edge1[1])
                            
                            edge2 = [v2, v3]
                            edge2.sort()
                            edge2 = (edge2[0], edge2[1])

                            edge3 = [v1, v3]
                            edge3.sort()
                            edge3 = (edge3[0], edge3[1])

                            tri_edges = [edge1, edge2, edge3]

                            #Loop through all edges
                            inc_tri = [5, 3, 4]
                            count = 0
                            for tri_edge in tri_edges:
                                #Check if this edge already exists in the edges dict
                                if tri_edge in self.edges.keys():
                                    edge_value = self.edges[tri_edge]

                                    face[inc_tri[count]] = edge_value[0]
                                    self.trs[edge_value[0]][edge_value[1]] = tri_index
                                #If this edge was not in the edges yet, add it as one
                                else:
                                    self.edges[tri_edge] = [tri_index, inc_tri[count]]
                                
                                count = count + 1

                            #Append the face and the attribute of that face
                            self.trs.append(face)
                            self.attr.append(id_value)

    def write_to_objp(self, file_path): #, id_to_attr):
        """
        Explination: Writes out the tin to an objp file.
        ---------------
        Input:
            file_path : string - The path to the obj file we want to write to.
        ---------------
        Output: void
        """
        print("=== write to file {} ===".format(file_path))

        with open(file_path, 'w+') as output_file:
            for vertex in self.vts:
                vertex_str = "v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n"
                output_file.write(vertex_str)

            for triangle in self.trs:
                triangle_str = "f " + str(triangle[0] + 1) + " " + str(triangle[1] + 1) + " " + str(
                    triangle[2] + 1) + " " + str(triangle[3] + 1) + " " + str(triangle[4] + 1) + " " + str(
                    triangle[5] + 1) + "\n"
                output_file.write(triangle_str)

            for attribute in self.attr:
                attribute_str = "a " + attribute + "\n"
                output_file.write(attribute_str)
                
                #if attribute[0] != 0.0:
                #    attribute_str = "a " + id_to_attr[int(attribute[0])] + "\n"
                #    output_file.write(attribute_str)
                #else:
                #    attribute_str = "a " + id_to_attr[1001] + "\n"
                #    output_file.write(attribute_str)

    def write_to_obj(self, file_path): #, id_to_attr):
        """
        Explination: Writes out the tin to an objp file.
        ---------------
        Input:
            file_path : string - The path to the obj file we want to write to.
        ---------------
        Output: void
        """
        print("=== write to file {} ===".format(file_path))

        with open(file_path, 'w+') as output_file:
            for vertex in self.vts:
                vertex_str = "v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n"
                output_file.write(vertex_str)

            for triangle in self.trs:
                triangle_str = "f " + str(triangle[0] + 1) + " " + str(triangle[1] + 1) + " " + str(
                    triangle[2] + 1) + "\n"
                output_file.write(triangle_str)

jp = json_parse()

json_file_path = sys.argv[1]
jp.read_json(json_file_path)

output_file_path = sys.argv[2]
Path(output_file_path).mkdir(parents=True, exist_ok=True)

objp_output_file = output_file_path + "/constrainted_tin.objp"
jp.write_to_objp(objp_output_file)

obj_output_file = output_file_path + "/constrainted_tin.obj"
jp.write_to_obj(obj_output_file)
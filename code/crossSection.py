import misc
import numpy as np

from pprint import pprint

class CrossSection:

    def __init__(self, points_to_source, receiver, reflection_heights):
        self.points_to_source = points_to_source
        self.reflection_heights = reflection_heights
        self.receiver = receiver
        
        self.vertices = []
        self.materials = []
        self.extension = {}

    def get_next_edge(self, ground_tin, tr, origin, destination):
        """
        Explanation: returns the next edge in the triangle which the path crosses
        ---------------
        Input:
            receiver : tuple(x,y,z) - the receiver point we walk from
            ground_tin : ground_Tin object - stores the whole tin
            tr : integer - id of the current triangle
        ---------------
        Output:
            list - two vertices of the edge.
        """
        edges = (
            (ground_tin.trs[tr][0], ground_tin.trs[tr][1]),
            (ground_tin.trs[tr][1], ground_tin.trs[tr][2]),
            (ground_tin.trs[tr][2], ground_tin.trs[tr][0])
            )
        # Go over the edges
        for i, edge in enumerate(edges):
            # Check if the orientation is correct
            if (misc.side_test(origin, destination, ground_tin.vts[edge[0]]) <= 0 and
                    misc.side_test(origin, destination, ground_tin.vts[edge[1]]) > 0):
                return i, edge
        
        print("something went wrong here")
        assert(False)
   
    def get_material(self, tin, buildings_manager, ground_type_manager, tr):
        """
        Explanation: Returns the material and attribute id of the triangle
        ---------------
        Input:
            tin : ground_Tin object - stores the whole tin
            buildings_manager : building_manager object - stores all the buildings
            ground_type_manager : ground_type_manager object - stores all ground surfaces
            tr : interger - id of triangle
        ---------------
        Output:
            string - material type
            integer - attribute id of the building, or -1 if it is ground
        """
        if tin.attributes[tr][0] == 'b':
            building_id = tin.attributes[tr]
            return "A0", building_id
        elif tin.attributes[tr][0] == 'g':
            if(ground_type_manager.grd_division[tin.attributes[tr]].index == 0):
                return "G", -1
            else:
                return "C", -1

    def get_cross_section(self, current_triangle, ground_tin, ground_type_manager, building_manager, source_height, receiver_height):
        """
        Explanation: Finds cross-section while walking to the source point
        ---------------
        Input:
            current_triangle : integer - the receiver triangle we walk from
            ground_tin : GroundTin object - stores the DTM in a triangle datastructure
            ground_type_manager : GroundTypeManager object - stores all the groundtype objects
            building_manager : BuildingManager object - stores all the building objects
        ---------------
        Output:
            void (saves the DSM, materials and extension in the class)
        """
        #print("=== cross_section ===")
        # define the neighbour ids
        nbs = [5, 3, 4] # -> [v0, v1, v2, n0, n1, n2]

        # initialize extension, holds information about receiver, reflections and source.
        extension = {}
        reflection_point_id_inversed = 0

        # the first vertex is the receiver projected into its triangle
        receiver_height_ground = ground_tin.interpolate_triangle(current_triangle, self.receiver)

        # get the material of the current triangle
        material_triangle, material_id = self.get_material(ground_tin, building_manager, ground_type_manager, current_triangle)
        cross_section_vertices = [(self.receiver[0], self.receiver[1], receiver_height_ground)]
        material = [material_triangle]
        
        # Boolean to check if the path is on top of a building, or not. receiver is never in building
        in_building = False
        origin = self.receiver

        for destination_id, destination in enumerate(self.points_to_source):
            # keep going untill the source triangle has been found.
            #print("{} origin: {} -> destination: {}".format(destination_id, origin, destination))
            while not ground_tin.point_in_triangle(destination, current_triangle):
                # Make sure that we have not gotten of the TIN
                assert (current_triangle != -1)

                # Get the outgoing edge of the triangle
                #print(destination_id, current_triangle)
                edge_id, edge = self.get_next_edge(ground_tin, current_triangle, origin, destination)

                # get intersection point between edge and receiver-source segment
                interpolated_point = ground_tin.intersection_point(edge, destination, origin)
                
                current_material, current_building_id = self.get_material(ground_tin, building_manager, ground_type_manager,
                                                                        current_triangle)

                # move triangle to the next triangle in the path
                current_triangle = ground_tin.trs[current_triangle][nbs[edge_id]]

                # Get the material and building_id of next building
                next_material, next_building_id = self.get_material(ground_tin, building_manager, ground_type_manager,
                                                                    current_triangle)

                # Check if the new calculated point is not too close to the previously added point, in MH distance
                
                if np.sum(abs(cross_section_vertices[-1][0] - interpolated_point)) <= 0.1:
                    #print("points are too close, material: {} -> {}".format(current_material, next_material))
                    if current_material == next_material:
                        continue
                    else:
                        # cross_section_vertices[-1] = [interpolated_point, next_material]
                        cross_section_vertices = cross_section_vertices[:-1]
                        material = material[:-1]
                
                # Check if both this and the next triangle are ground, then append the vertex to the list
                if current_building_id == -1 and next_building_id == -1:  # don't use the mtl because maybe later there will be != mtl for bldgs
                    cross_section_vertices.append(tuple(interpolated_point))
                    material.append(next_material)

                # Check if this triangle is, but the next triangle is not building. if the count however is still 0, than the building is not valid. should happen too often
                elif current_building_id != -1 and next_building_id == -1 and not in_building:
                    print("prev building was negative")
                    pass

                # if the next, or both points are building, than check whether its rising, lowering, and staying on roof level.
                else:

                    # We are not in building, but are going up
                    if not in_building:

                        # Get height of building
                        next_height_building = building_manager.buildings[next_building_id].roof_level

                        # if the next building is higher than the interpolated point (dtm level), we need to add the rising edge
                        if next_height_building > interpolated_point[2]:
                            # add ground point
                            cross_section_vertices.append(tuple(interpolated_point))
                            material.append(next_material)
                            # add roof point
                            cross_section_vertices.append((interpolated_point[0], interpolated_point[1], next_height_building))
                            material.append(next_material)
                            in_building = True

                        else:
                            print("Roof height is lower than ground height, for building ", next_building_id)

                    else:
                        if(current_building_id == -1):
                            print("segemt: {} tr: {} next attrib: {} inbuilding?: {} last point: {}".format(destination_id, current_triangle, next_building_id, in_building, cross_section_vertices[-1]))
                        
                        current_height_building = building_manager.buildings[current_building_id].roof_level

                        # We will stay in Building, check if building is higher than the ground (negative buildings considered)
                        if current_height_building > interpolated_point[2] and next_building_id != -1:

                            next_height_building = building_manager.buildings[next_building_id].roof_level

                            # no collinear vertical points, so we are going from one building to another building with a different height
                            if current_material != next_material or abs(current_height_building - next_height_building) > 0.1:
                                # add current roof height
                                cross_section_vertices.append((interpolated_point[0], interpolated_point[1], current_height_building))
                                material.append(current_material)
                                # add new roof height
                                cross_section_vertices.append((interpolated_point[0], interpolated_point[1], next_height_building))
                                material.append(next_material)
                                

                        # Will go down from building again
                        elif current_height_building > interpolated_point[2] and next_building_id == -1:
                            """
                            # add the roof top
                            cross_section_vertices.append([(interpolated_point[0], interpolated_point[1],
                                                            current_height_building), current_material])
                            # add the ground point
                            cross_section_vertices.append([interpolated_point, next_material])
                            in_building = False
                            """
                            # Check if the ray only crosses the corner of the building, then ignore
                            if np.sum(abs(cross_section_vertices[-2][0] - interpolated_point)) <= 0.1:
                                cross_section_vertices = cross_section_vertices[:-2]
                                material = material[:-2]

                                cross_section_vertices.append(tuple(interpolated_point))
                                material.append(next_material)
                                in_building = False
                            else:
                                # add the roof top
                                cross_section_vertices.append((interpolated_point[0], interpolated_point[1], current_height_building))
                                material.append(current_material)
                                # add the ground point
                                cross_section_vertices.append(tuple(interpolated_point))
                                material.append(next_material)
                                in_building = False
                        else:
                            print("Roof height is lower than ground height, for building ", current_building_id)

            # When destination has been reached, check if that is the source.
            if(destination_id != len(self.points_to_source)-1):
                # set the reflection point to the origin
                origin = destination
                # get the height of the tin at the reflection point

                reflection_ground_material, building_id = self.get_material(ground_tin, building_manager, ground_type_manager, current_triangle)

                if(building_id != -1):
                    reflection_height_ground = building_manager.buildings[next_building_id].roof_level
                else:
                    reflection_height_ground = ground_tin.interpolate_triangle(current_triangle, destination)

                cross_section_vertices.append((destination[0], destination[1], reflection_height_ground))
                material.append(reflection_ground_material)

                # save the refleciton point to store the extension at the end.
                reflection_point_id_inversed = len(cross_section_vertices)-1

        # Reached source triangle, add this point as well.
        source_height_ground = ground_tin.interpolate_triangle(current_triangle, destination)

        source_material, building_id = self.get_material(ground_tin, building_manager, ground_type_manager, current_triangle)

        cross_section_vertices.append((destination[0], destination[1], source_height_ground))
        material.append(source_material)
        #
        # Invert the path to go from source to receiver (materials are taken care of.)
        cross_section_vertices.reverse()

        # add source and receiver points. source is always 0.05 meter above terrain, receiver always at 2 meters.
        extension[0] = ["source", source_height]
        extension[len(cross_section_vertices) - 1] = ["receiver", receiver_height]

        # Add the reflection (path is inversed, so also the location of the extension needs to be inversed.)
        if(reflection_point_id_inversed != 0):
            reflection_vertex = len(cross_section_vertices) - 1 - reflection_point_id_inversed
            extension[reflection_vertex] = ["wall", self.reflection_heights[0] - cross_section_vertices[reflection_vertex][2], "A0"]

        self.vertices = cross_section_vertices
        self.materials = material
        self.extension = extension

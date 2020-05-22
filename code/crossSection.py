import misc
import numpy as np
class CrossSection:

    def __init__(self, source, receiver):
        self.source = source
        self.receiver = receiver
        
        #Please add any other data that belongs to a cross section here eg, maybe intermidiate points?
        #self.intermidiate_points - []

    def get_next_edge(self, ground_tin, tr):
        """
        Explanation: returns the next edge in the triangle which the path crosses
        ---------------
        Input:
            receiver : (x,y,z) - the receiver point we walk from
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
                if (misc.side_test(self.receiver, self.source, ground_tin.vts[edge[0]]) <= 0 and
                        misc.side_test(self.receiver, self.source, ground_tin.vts[edge[1]]) >= 0):
                    return i, edge
        
        print("something went wrong here")
        assert(True)

        
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
        if tin.attributes[tr] in buildings_manager.buildings:
            building_id = int(tin.attributes[tr])
            return "A0", building_id
        else:
            if(ground_type_manager.grd_division[int(tin.attributes[tr])].index == 0):
                return "G", -1
            else:
                return "C", -1

    def get_cross_section(self, current_triangle, ground_tin, ground_type_manager, building_manager):
        """
        Explanation: Finds cross-section while walking to the source point
        ---------------
        Input:
            receiver : (x,y,z) - the receiver point we walk from
            source : (x,y,z) - the source point we want to walk to
            tr_receiver : integer - triangle id of triangle underneath receiver point
            buildings : Fiona's Collection where each record/building holds a 'geometry' and a 'property' key
        ---------------
        Output:
            list of vertices - defining the cross-section
        """
        #print("=== cross_section ===")
        # define the neighbour ids
        nbs = [5, 3, 4] # -> [v0, v1, v2, n0, n1, n2]

        # the first vertex is the receiver projected into its triangle
        receiver_height = ground_tin.interpolate_triangle(current_triangle, self.receiver)

        # get the material of the current triangle
        material_triangle, material_id = self.get_material(ground_tin, building_manager, ground_type_manager, current_triangle)
        cross_section_vertices = [[(self.receiver[0], self.receiver[1], receiver_height), material_triangle]]

        # Boolean to check if the path is on top of a building, or not. receiver is never in building
        in_building = False

        # keep going until the source triangle has been found.
        while not ground_tin.point_in_triangle(self.source, current_triangle):
            # Make sure that we have not gotten off the TIN
            assert (current_triangle != -1)
            
            # Get the outgoing edge of the triangle
            edge_id, edge = self.get_next_edge(ground_tin, current_triangle)

            # get intersection point between edge and receiver-source segment
            interpolated_point = ground_tin.intersection_point(edge, self.source, self.receiver)
            current_material, current_building_id = self.get_material(ground_tin, building_manager, ground_type_manager,
                                                                      current_triangle)

            # move triangle to the next triangle in the path
            current_triangle = ground_tin.trs[current_triangle][nbs[edge_id]]

            # Get the material and building_id of next building
            next_material, next_building_id = self.get_material(ground_tin, building_manager, ground_type_manager,
                                                                current_triangle)

            # Check if the new calculated point is not too close to the previously added point, in MH distance
            if np.sum(abs(cross_section_vertices[-1][0] - interpolated_point)) <= 0.1:
                #print("points are too close, nothing to add")
                if next_building_id == -1:
                    continue
                else:
                    cross_section_vertices[-1] = [interpolated_point, next_material]

            # Check if both this and the next triangle are ground, then append the vertex to the list
            if current_building_id == -1 and next_building_id == -1:  # don't use the mtl because maybe later there will be != mtl for bldgs
                cross_section_vertices.append([interpolated_point, next_material])
                
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
                        cross_section_vertices.append([interpolated_point, next_material])
                        # add roof point
                        cross_section_vertices.append([(interpolated_point[0], interpolated_point[1],
                                                        next_height_building), next_material])
                        
                        in_building = True

                    else:
                        print("Roof height is lower than ground height, for building ", next_building_id)

                # we are in a building
                else:

                    current_height_building = building_manager.buildings[current_building_id].roof_level

                    # We will stay in Building, check if building is higher than the ground (negative buildings considered)
                    if current_height_building > interpolated_point[2] and next_building_id != -1:

                        next_height_building = building_manager.buildings[next_building_id].roof_level

                        # no collinear vertical points, so we are going from one building to another building with a different height
                        if current_material != next_material or abs(current_height_building - next_height_building) > 0.1:
                            # add current roof height
                            cross_section_vertices.append(
                                [(interpolated_point[0], interpolated_point[1], current_height_building), current_material])
                            # add new roof height
                            cross_section_vertices.append(
                                [(interpolated_point[0], interpolated_point[1], next_height_building), next_material])
                            

                    # Will go down from building again
                    elif current_height_building > interpolated_point[2] and next_building_id == -1:
                        '''# Check if the ray only crosses the corner of the building, then ignore
                        if np.sum(abs(cross_section_vertices[-2][0] - interpolated_point)) <= 0.1:
                            cross_section_vertices = cross_section_vertices[:-2]
                            cross_section_vertices.append([interpolated_point, next_material])
                            in_building = False
                        else:
                            # add the roof top
                            cross_section_vertices.append([(interpolated_point[0], interpolated_point[1],
                                                            current_height_building), current_material])
                            # add the ground point
                            cross_section_vertices.append([interpolated_point, next_material])
                            in_building = False'''
                        # add the roof top
                        cross_section_vertices.append([(interpolated_point[0], interpolated_point[1],
                                                        current_height_building), current_material])
                        # add the ground point
                        cross_section_vertices.append([interpolated_point, next_material])
                        in_building = False
                    else:
                        print("Roof height is lower than ground height, for building ", current_building_id)

        # Reached source triangle, add this point as well.
        source_height = ground_tin.interpolate_triangle(current_triangle, self.source)

        source_material, building_id = self.get_material(ground_tin, building_manager, ground_type_manager, current_triangle)

        cross_section_vertices.append([(self.source[0], self.source[1], source_height), source_material])
        # Invert the path to go from source to receiver (materials are taken care of.)
        cross_section_vertices.reverse()
        return cross_section_vertices

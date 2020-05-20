import misc
import numpy as np
class CrossSection:

    def __init__(self):
        self.source = []
        
        #Please add any other data that belongs to a cross section here eg, maybe intermidiate points?
        #self.intermidiate_points - []

    def get_cross_section(self, source, receiver, receiver_tr, ground_tin, ground_type_manager, building_manager):
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
        print("=== cross_section ===")
        check_tr = receiver_tr

        # the first vertex is the receiver projected into its triangle
        receiver_height = ground_tin.interpolate_triangle(check_tr, receiver)

        # Finrd the material of the point
        if ground_tin.attributes[check_tr] in building_manager.buildings:
            cross_section_vertices = [[(receiver[0], receiver[1], receiver_height), "A0"]]
        else:
            if(ground_type_manager.grd_division[ground_tin.attributes[check_tr]].index == 0): 
                cross_section_vertices = [[(receiver[0], receiver[1], receiver_height), "G"]]
            else:
                cross_section_vertices = [[(receiver[0], receiver[1], receiver_height), "C"]]
                
        nbs = [5, 3, 4]
        count = 0
        while not ground_tin.point_in_triangle(source, check_tr):
            assert (check_tr != -1)
            edges = ((ground_tin.trs[check_tr][0], ground_tin.trs[check_tr][1]),
                     (ground_tin.trs[check_tr][1], ground_tin.trs[check_tr][2]),
                     (ground_tin.trs[check_tr][2], ground_tin.trs[check_tr][0]))

            for i, edge in enumerate(edges):
                if (misc.side_test(receiver, source, ground_tin.vts[edge[0]]) <= 0 and
                        misc.side_test(receiver, source, ground_tin.vts[edge[1]]) >= 0):

                    # get intersection point between edge and receiver-source segment
                    inter_pt = ground_tin.intersection_point(edge, source, receiver)

                    # Check if the new calculated point is not too close to the previously added point, in MH distance
                    if np.sum(abs(cross_section_vertices[-1][0] - inter_pt)) <= 0.1:
                        print("points are too close, nothing to add")
                        check_tr = ground_tin.trs[check_tr][nbs[i]]
                        break
                    # Check if there are any building intersection
                    else:
                        inter_pt = tuple(inter_pt)
                        if ground_tin.attributes[check_tr] in building_manager.buildings:
                            current_tr_mtl = "A0"
                            current_bldg = ground_tin.attributes[check_tr]
                        else:
                            current_bldg = -1
                            if(ground_type_manager.grd_division[ground_tin.attributes[check_tr]].index == 0): 
                                current_tr_mtl = "G"
                            else:
                                current_tr_mtl = "C"

                        check_tr = ground_tin.trs[check_tr][nbs[i]]
                        if ground_tin.attributes[check_tr] in building_manager.buildings:
                            next_tr_mtl = "A0"
                            next_bldg = ground_tin.attributes[check_tr]
                        else:
                            next_bldg = -1
                            if(ground_type_manager.grd_division[ground_tin.attributes[check_tr]].index == 0): 
                                next_tr_mtl = "G"
                            else:
                                next_tr_mtl = "C"
                                
                        if current_bldg == -1 and next_bldg == -1:  # don't use the mtl because maybe later there will be != mtl for bldgs
                            cross_section_vertices.append([inter_pt, next_tr_mtl])
                            break
                            
                        elif current_bldg != -1 and next_bldg == -1 and count == 0:
                            pass

                        else:
                            if count == 0:

                                #print("{}".format(self.attributes[check_tr]))
                                '''next_build_info = buildings.get(next_bldg)
                                
                                next_h_bldg = build_info['properties']['h_dak']'''

                                next_h_bldg = building_manager.buildings[next_bldg].roof_level
                                if next_h_bldg > inter_pt[2]:
                                    cross_section_vertices.append([inter_pt, next_tr_mtl])
                                    cross_section_vertices.append([(inter_pt[0], inter_pt[1], next_h_bldg),
                                                                   next_tr_mtl])
                                    count = 1
                                    break
                                else:
                                    print("Roof height is lower than ground height, for building ", next_bldg)
                                    break
                            else:
                                '''build_info = buildings.get(current_bldg)
                                current_h_bldg = build_info['properties']['h_dak']'''
                                
                                current_h_bldg = building_manager.buildings[current_bldg].roof_level
                                if current_h_bldg > inter_pt[2] and next_bldg != -1:
                                    '''next_build_info = buildings.get(next_bldg)
                                    next_h_bldg = build_info['properties']['h_dak']'''
                                    next_h_bldg = building_manager.buildings[next_bldg].roof_level
                                    # no collinear horizontal points
                                    if current_tr_mtl == next_tr_mtl and current_h_bldg == next_h_bldg:
                                        break
                                    # no collinear vertical points
                                    else:
                                        cross_section_vertices.append([(inter_pt[0], inter_pt[1], current_h_bldg),
                                                                       current_tr_mtl])
                                        cross_section_vertices.append([(inter_pt[0], inter_pt[1], next_h_bldg),
                                                                       next_tr_mtl])
                                        break
                                # down back to DTM
                                elif current_h_bldg > inter_pt[2] and next_bldg == -1:
                                    cross_section_vertices.append([(inter_pt[0], inter_pt[1], current_h_bldg),
                                                                   current_tr_mtl])
                                    cross_section_vertices.append([inter_pt, next_tr_mtl])
                                    count = 0
                                    break
                                else:
                                    print("Roof height is lower than ground height, for building ", current_bldg)
                                    break
        source_tr = check_tr
        source_height = ground_tin.interpolate_triangle(source_tr, source)
        if ground_tin.attributes[source_tr] in building_manager.buildings:
            source_tr_mtl = "A0"
        else:
            if(ground_type_manager.grd_division[ground_tin.attributes[check_tr]].index == 0): 
                source_tr_mtl = "G"
            else:
                source_tr_mtl = "C"

        cross_section_vertices.append([(source[0], source[1], source_height), source_tr_mtl])
        cross_section_vertices.reverse()
        return cross_section_vertices
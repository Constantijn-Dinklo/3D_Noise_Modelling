import bisect
from crossSection import CrossSection
from pprint import pprint
import numpy as np
from misc import interpolate_edge, reverse_bisect_left, write_cross_section_to_obj


class CrossSectionManager:

    def __init__(self, propagation_paths_dict_direct, propagation_paths_dict_reflect, reflection_building_heights,
                 source_height, receiver_height):
        self.propagation_paths_dict_direct = propagation_paths_dict_direct
        self.propagation_paths_dict_reflect = propagation_paths_dict_reflect
        self.reflection_building_heights = reflection_building_heights
        self.paths = {}
        self.extensions = {}
        self.materials = {}
        self.source_height = source_height
        self.receiver_height = receiver_height

    def get_cross_sections(self, tin, ground_type_manager, building_manager):
        """
        Explanation: Finds cross-sections while walking to the source point, for all sections from the receiver.
        ---------------
        Input:
            receiver : (x,y,z) - the receiver point we walk from
            source : (x,y,z) - the source point we want to walk to
            tr_receiver : integer - triangle id of triangle underneath receiver point
            buildings : Fiona's Collection where each record/building holds a 'geometry' and a 'property' key
        ---------------
        Output:
            void (fills self.paths with a list of paths)
        """

        for receiver, paths_to_sources in self.propagation_paths_dict_direct.items():
            self.paths[receiver] = []
            self.extensions[receiver] = []
            self.materials[receiver] = []

            receiver_triangle = tin.find_receiver_triangle(2, receiver)
            # pprint("paths to sources: {}".format(paths_to_sources))
            # print(" ")
            for points_to_source in paths_to_sources:
                # print("direct path: {} -> {}".format(receiver, points_to_source[-1]))
                cross_section = []
                # direct path:
                receiver_section = CrossSection([points_to_source[-1]], receiver, self.source_height,
                                                self.receiver_height)
                path_direct, material, extension = receiver_section.get_cross_section(receiver_triangle, tin,
                                                                                      ground_type_manager,
                                                                                      building_manager)
                self.paths[receiver].append(path_direct)
                self.extensions[receiver].append(extension)
                self.materials[receiver].append(material)

                if (len(points_to_source) > 1):
                    for point in points_to_source[:-1]:
                        extension = {}
                        # find where the intermediate sources lie in the 'complete' cross-section
                        if path_direct[-1][0] - path_direct[0][0] < 0:
                            split_idx = reverse_bisect_left(path_direct, point)
                        elif path_direct[-1][0] - path_direct[0][0] == 0 and path_direct[-1][1] - path_direct[0][1] < 0:
                            split_idx = reverse_bisect_left(path_direct, point)
                        else:
                            split_idx = bisect.bisect_left(path_direct, point)
                        if point == path_direct[split_idx][:2]:  # better to add a distance threshold
                            self.paths[receiver].append(path_direct[split_idx:])
                            extension[0] = ["source", self.source_height]
                            extension[split_idx + 1] = ["receiver", self.receiver_height]
                            self.extensions[receiver].append(extension)
                            self.materials[receiver].append(material[split_idx:])
                        else:
                            part_path_direct = path_direct[split_idx:]
                            source_ground_height = interpolate_edge(path_direct[split_idx - 1], path_direct[split_idx],
                                                                    point)
                            part_path_direct = [(point[0], point[1], source_ground_height)] + part_path_direct
                            self.paths[receiver].append(part_path_direct)
                            extension[0] = ["source", self.source_height]
                            extension[split_idx + 1] = ["receiver", self.receiver_height]
                            self.extensions[receiver].append(extension)
                            part_path_direct_material = [material[split_idx]] + material[split_idx:]
                            self.materials[receiver].append(part_path_direct_material)

            for receiver, paths_to_sources in self.propagation_paths_dict_reflect.items():

                reflection_counter = 0
                # pprint("paths to sources: {}".format(paths_to_sources))
                # print(" ")
                for points_to_source in paths_to_sources:
                    # print("reflected path: {} -> {}".format(receiver, points_to_source))
                    receiver_section = CrossSection(points_to_source, receiver, self.source_height,
                                                    self.receiver_height,
                                                    self.reflection_building_heights[receiver][reflection_counter])
                    path_reflected, material, extension = receiver_section.get_cross_section(receiver_triangle, tin,
                                                                                             ground_type_manager,
                                                                                             building_manager)
                    self.paths[receiver].append(path_reflected)
                    self.extensions[receiver].append(extension)
                    self.materials[receiver].append(material)

    def write_obj(self, filename):
        """
        Explanation: Write the paths of this receiver to an obj file, calls write_cross_section_to_obj
        ---------------
        Input:
            filename : string - filename, including path and extension(.obj)
        ---------------
        Output:
            void (writes obj file)
        """
        i = 0
        for receiver, paths in self.paths.items():
            write_cross_section_to_obj(str(i) + filename, paths)
            i += 1

    def get_paths_and_extensions(self):
        return self.paths, self.extensions, self.materials


from crossSection import CrossSection
from pprint import pprint

class CrossSectionManager:

    def __init__(self, receiver, receiver_tr, sources_list):
        # one manager per receiver.
        self.sources_list = sources_list
        self.receiver = receiver
        self.receiver_triangle = receiver_tr

    def add_cross_section(self, cross_section):
        receiver_point = cross_section.receiver
        if receiver_point not in self.cross_sections:
            self.cross_sections[receiver_point] = []
        self.cross_sections[receiver_point].append(cross_section)
    
    def get_cross_sections(self, tin, ground_type_manager, building_manager):
        receiver_paths = []
        for source in self.sources_list:
            print("{} -> {}".format(self.receiver, source))
            section = CrossSection()
            path = section.get_cross_section(source, self.receiver, self.receiver_triangle, tin, ground_type_manager, building_manager)
            pprint(path)
            receiver_paths.append(path)
        return receiver_paths

    def write_obj(self, path):
        pass


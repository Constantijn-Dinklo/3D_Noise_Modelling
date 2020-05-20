
from crossSection import CrossSection

class CrossSectionManager:

    def __init__(self):
        self.cross_sections = {} #Should be a dict where key = receiver point, value = list of all cross sections from it.

        self.start_triangle = {} #A dict that stores at what triangle to start for a receiver point, key = receiver point, value = starting triangle id

    def add_cross_section(self, cross_section):
        receiver_point = cross_section.receiver
        if receiver_point not in self.cross_sections:
            self.cross_sections[receiver_point] = []
        self.cross_sections[receiver_point].append(cross_section)
    
    def get_cross_section(self, receiver_point):
        return self.cross_sections[receiver_point]

    def get_start_triangle(self, receiver_point):
        return self.start_triangle[receiver_point]

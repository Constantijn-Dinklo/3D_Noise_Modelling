from xmlParser import XmlParser
from pprint import pprint

class XmlParserManager:

    def __init__(self):
        self.prepared_paths = {}

    def write_xml_files(self, cross_sections_manager):
        j = 0
        cross_sections_dict = cross_sections_manager.cross_sections
        for receiver, cross_sections in cross_sections_dict.items():
            self.prepared_paths[receiver] = []
            for i, cross_section in enumerate(cross_sections):
                extension = cross_section.extension
                path = cross_section.vertices
                material = cross_section.materials
                
                #pprint(material)
                
                xml = XmlParser(path, extension, material)
                xml.normalize_path()
                print("=== write output/path_{}_{}.xml ===".format(j, i))
                xml.write_xml("output/path_{}_{}.xml".format(j, i), True)
                self.prepared_paths[receiver].append(xml)

            j += 1

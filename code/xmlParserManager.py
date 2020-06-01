from xmlParser import XmlParser
from pprint import pprint

class XmlParserManager:

    def __init__(self):
        self.prepared_paths = {}

    def write_xml_files(self, cross_sections_manager):
        j = 0
        cross_sections_dict = cross_sections_manager.cross_sections
        for receiver, cross_sections in cross_sections_dict.items():
            with open('input/map_receiver_id.txt', '+a') as f:
                f.write('{} {} {}\n'.format(j, receiver[0], receiver[1]))
            self.prepared_paths[receiver] = []
            for i, cross_section in enumerate(cross_sections):
                extension = cross_section.extension
                path = cross_section.vertices
                material = cross_section.materials
                
                #pprint(material)
                
                xml = XmlParser(path, extension, material)
                xml.normalize_path()
                output_file_path = "output/xml/path_{}_{}.xml".format(j, i)
                print("=== write {} ===".format(output_file_path))
                xml.write_xml(output_file_path, True)
                self.prepared_paths[receiver].append(xml)

            j += 1

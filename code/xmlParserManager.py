from xmlParser import XmlParser
from misc import write_default_noise

class XmlParserManager:

    def __init__(self):
        self.prepared_paths = {}

    def write_xml_files(self, cross_sections_manager, Lw, source_height):
        output_folder = "output/xml/"

        j = 0
        receiver_list = []
        cross_sections_dict = cross_sections_manager.cross_sections
        for receiver, cross_sections in cross_sections_dict.items():
            # save the receiver, so the order is saved, later written to seperate file with all receivers.
            receiver_list.append(receiver)

            self.prepared_paths[receiver] = []
            for i, cross_section in enumerate(cross_sections):
                source = cross_section.source
                extension = cross_section.extension
                path = cross_section.vertices
                material = cross_section.materials
                                
                xml = XmlParser(source, path, extension, material)
                xml.normalize_path()
                output_file_path = "{}path_{}_{}.xml".format(output_folder, j, i)
                
                xml.write_xml(output_file_path, Lw, True)
                self.prepared_paths[receiver].append(xml)

            j += 1
            
            with open('output/map_receiver_id.txt', 'w') as f:
                for i, receiver in enumerate(receiver_list):
                    f.write('{} {} {}\n'.format(i, receiver[0], receiver[1]))


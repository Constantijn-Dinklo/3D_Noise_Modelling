from xmlParser import XmlParser
from misc import write_default_noise

class XmlParserManager:

    def __init__(self):
        self.prepared_paths = {}

    def write_xml_files(self, cross_sections_manager, Lw, source_height):
        output_folder = "output/xml/"
        output_default_noise = "Default_Road_Noise.xml"
        # write the default noise output file
        #write_default_noise(output_folder + output_default_noise, Lw, source_height)

        j = 0
        cross_sections_dict = cross_sections_manager.cross_sections
        for receiver, cross_sections in cross_sections_dict.items():
            with open('input/map_receiver_id.txt', '+a') as f:
                f.write('{} {} {}\n'.format(j, receiver[0], receiver[1]))

            self.prepared_paths[receiver] = []
            for i, cross_section in enumerate(cross_sections[:1]):
                extension = cross_section.extension
                path = cross_section.vertices
                material = cross_section.materials
                                
                xml = XmlParser(path, extension, material)
                xml.normalize_path()
                output_file_path = "{}path_{}_{}.xml".format(output_folder, j, i)
                #print("=== write {} ===".format(output_file_path))
                xml.write_xml(output_file_path, output_default_noise, Lw, True)
                self.prepared_paths[receiver].append(xml)

            j += 1

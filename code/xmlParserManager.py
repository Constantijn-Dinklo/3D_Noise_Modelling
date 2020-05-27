from xmlParser import XmlParser
from pprint import pprint

class XmlParserManager:

    def __init__(self, paths, extensions, materials):
        self.paths = paths
        self.extensions = extensions
        self.materials = materials

    def write_xml_files(self):
        j = 0
        for receiver, paths in self.paths.items():
            pprint(len(paths))
            for i in range(len(paths)):
                extension = self.extensions[receiver][i]
                path = self.paths[receiver][i]
                material = self.materials[receiver][i]
                
                #pprint(material)
                
                xml = XmlParser(path, extension, material)
                xml.normalize_path()
                print("=== write output/path_{}_{}.xml ===".format(j, i))
                xml.write_xml("output/path_{}_{}.xml".format(j, i), True)
            j += 1

from xmlParser import XmlParser

class XmlParserManager:

    def __init__(self):
        self.prepared_paths = {}

    def write_xml_files(self, cross_sections_manager, Lw, output_folder):
        """
        Explination: prepare cross sections for writing to xml, compute the noise level per section and then write them to xml.
        ---------------
        Input:
            cross_section_maanger (dictionary) - holds all the cross sections per receiver
            Lw (dictionary) - dictionary holding the default noise values, type of source etc.
            output_folder (list) - the path to write the files to, split up into map items ("outut/", "xml/")
        ---------------
        Output: void (writes the xml files)
        """

        j = 0
        receivers = ""

        # Loop over each list of cross_sections per receiver.
        for receiver, cross_sections in cross_sections_manager.cross_sections.items():
            # save the receiver, so the order is saved, later written to seperate file with all receivers.
            receivers += '{} {:.2f} {:.2f}\n'.format(j, receiver[0], receiver[1])

            # for optional continuous processing, store the prepared path in this class.
            self.prepared_paths[receiver] = []

            # Loop over each cross_section
            for i, cross_section in enumerate(cross_sections):
                extension = cross_section.extension
                path = cross_section.vertices
                material = cross_section.materials

                # Create an xml instance
                xml = XmlParser(path, extension, material)
                # Makes it local, lift its such that z is also positive, and path is in positive direction
                xml.normalize_path()

                # Optionally, simplify the path (using Douglas Peucker algorithm) (Currently not used)
                #xml.douglas_Peucker(0.1)

                # write the xml to the output file
                output_file_path = "{}/path_{}_{}.xml".format(output_folder[1], j, i)
                xml.write_xml(output_file_path, Lw, False)
                self.prepared_paths[receiver].append(xml)

            j += 1
        
        # write the receivers to a text file so the receiver location can be retrieved after analyzing the xml file.
        with open('{}/receiver_dict.txt'.format(output_folder[0]), 'w') as f:
            f.write(receivers)


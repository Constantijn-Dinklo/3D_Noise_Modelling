import xml.etree.cElementTree as ET
import numpy as np
import bisect
import misc
# to be removed later, for debugging
import matplotlib.pyplot as plt
from pprint import pprint

class XmlParser:
    
    def __init__(self, path, ext, mat):
        self.vts = np.array(path)
        self.mat = mat
        self.ext = ext

    def normalize_path(self):
        """
        Explination: Move 3D Cartesian coordinates relative to the starting point (receiver) by subtraction P0 from everypoint
        ---------------
        Input: void
        ---------------
        Output: void
        """
        # move all vertices relative to first vertex
        self.vts -= self.vts[0]

    def get_offsets_perpendicular(self, start, end):
        """
        Explination:
            calculates the perpendicular distance from points to the the line
        ---------------
        Input: 
            Start: integer - id of the start point
            end: integer - id of the end point
        ---------------
        Output: 
            numpy array - array of the offsets of points along line segment
        """
        p_start = self.vts[start]
        p_end = self.vts[end]
        line_length = ((p_end[2] - p_start[2]) ** 2 + (p_end[0] - p_start[0]) ** 2) ** 0.5
        offsets = []

        for id in range(start+1, end):
            # do side test (return lenght of line x perpendicualr distace) so devide it by the length and voila
            diff = abs(misc.side_test((p_start[0], p_start[2]), (p_end[0], p_end[2]), (self.vts[id,0], self.vts[id,2]))) / line_length
            offsets.append(diff)

        return np.array(offsets)

    def douglas_Peucker(self, threshold):
        """
        Explination:
            simplifies the path using douglas peucker algorithm
        ---------------
        Input: 
            Threshold: the minimal perpendicular distance between a line and a point for the point to be imported.
        ---------------
        Output: 
            void (updates self.vts)
        """
        # === create initial path ===
        # initalize simple path with all points that have an extension (source, receiver, barrier, etc)
        path_simple = []
        assert(len(self.ext) > 1)
        for key in self.ext:
            bisect.insort(path_simple, key)

        # maintain the line material, insert every points where the material changes
        for i in range(len(self.mat)-1):
            if(self.mat[i] != self.mat[i+1]):
                if i not in self.ext:
                    bisect.insort(path_simple, i)

        # == insert relevant points ===
        i = 0
        while(i < len(path_simple) - 1):
            #print(path_simple)
            start = path_simple[i]
            end = path_simple[i+1]

            if(end - start < 2):
                i += 1 # go to bext segment
                continue

            # Get the offset between the line from start to end, and the points in between
            offsets = self.get_offsets_perpendicular(start, end)
            
            # get the id of the highest offset
            id_max = np.argmax(offsets)

            # Check if the offset is above the treshold, if so, add the point to the list
            if(offsets[id_max] > threshold):
                # Make sure to get the right id, id_max starts at 0, but 0 is already 1 further than the start point.
                path_simple.insert(i+1, id_max + start + 1)
            else:
                i += 1
        
        # === post-processing; update extension dictionary, materials and vertices ===
        # Update the extensions with the new positions in the list.
        for id, id_old in enumerate(path_simple):
            if id_old in self.ext and id != id_old:
                # Create a new key, with the correct id, and assign is het value of the old id that is popped.
                self.ext[id] = self.ext.pop(id_old)

        self.mat = [self.mat[id] for id in path_simple]
        self.vts = np.array([self.vts[id] for id in path_simple])

    def write_xml(self, filename, default_noise_file, Lw, validate):
        """
        Explination:
            1. create a element tree and set general information
            2. insert points in tree
            3. set point types (source, receiver etc)
            4. write to file
        ---------------
        Input: 
            filename of the output file (including the path)
        ---------------
        Output: void (writes output file)
        """
        # intialize element tree
        root = ET.Element("CNOSSOS-EU", version="1.001")
        method = ET.SubElement(root, "method")

        # Set the Method (same for all)
        ET.SubElement(method, "select", id="JRC-2012")

        # when validate is True, then the xml file will be validated by the TestCnossos software, if validate is false it is not checked, this will save time when we know the input it horizontal and orientation is correct
        if(not validate):
            options = ET.SubElement(method, "options")
            ET.SubElement(options, "option", id="CheckHorizontalAlignment", value="false")
            ET.SubElement(options, "option", id="ForceSourceToReceiver", value="false")

        meteo = ET.SubElement(method, "meteo", model="DEFAULT")
        ET.SubElement(meteo, "pFav").text = "0.3"
        
        # create the path
        path = ET.SubElement(root, "path")

        for id in range(len(self.vts)):
            # create a control point
            cp = ET.Element("cp")

            # insert the pos (position)
            pos = ET.SubElement(cp, "pos")
            ET.SubElement(pos, "x").text = "{:.2f}".format(self.vts[id,0])
            ET.SubElement(pos, "y").text = "{:.2f}".format(self.vts[id,1])
            ET.SubElement(pos, "z").text = "{:.2f}".format(self.vts[id,2])

            # Insert the material
            ET.SubElement(cp, "mat", id=self.mat[id])

            # append the created control point to the path
            path.append(cp)

        for id, val in self.ext.items():
            # set the first point as receiver
            ext = ET.Element("ext")
            ext_type = ET.SubElement(ext, val[0])
            # if its a source, this comes before the height
            if(val[0] == "source"):
                #ET.SubElement(ext_type, "import", file=default_noise_file)
                ET.SubElement(ext_type, "h").text = "{:.2f}".format(val[1])
                power_levels = Lw['power'] + 10 * np.log10(val[2])
                power_levels_str = ""
                for dB in power_levels:
                    power_levels_str += " {:.1f}".format(dB)
                ET.SubElement(ext_type, "Lw", 
                    sourceType=Lw['sourceType'],
                    measurementType=Lw['measurementType'],
                    frequencyWeighting=Lw['frequencyWeighting']
                ).text = power_levels_str

                #geom = ET.SubElement(ext_type, "extGeometry")
                #line_source = ET.SubElement(geom, "lineSource")
                # make sure to put the lenth in extension
                #ET.SubElement(line_source, "length").text = "{:.2f}".format(val[2])

            elif (val[0] == "wall" or val[0] == "edge"):
                ET.SubElement(ext_type, "mat").text = str(val[2])
            else:
                ET.SubElement(ext_type, "h").text = "{:.2f}".format(val[1])

            
            path[id].append(ext)

        # set the last point as source
        #ext_srs = ET.Element("ext")
        #srs = ET.SubElement(ext_srs, "source")
        #ET.SubElement(srs, "h").text = str(self.source_height)

        #path[-1].append(ext_srs)
        # Put the whole root in the tree, and write the tree to the file
        tree = ET.ElementTree(root)
        tree.write(filename, encoding="UTF-8", xml_declaration=True)

    def visualize_path(self):
        """
        Explination:
            Visualizes the cross Section
        ---------------
        Input:  void
        ---------------
        Output: void
        """
        # color: if it is reflective ground, take black, othewise, take brown.
        color = ['k' if x == 'G' else 'brown' for x in self.mat]

        for i in range(len(self.vts) -2, -1, -1):
            plt.plot(self.vts[i:i+2,0], self.vts[i:i+2,2], color=color[i+1], marker="o")

        # plot input points, and both source and receiver
        
        # plot the lines for both input and translated lines
        #plt.plot(self.vts[:,0], self.vts[:,2])
        
        plt.show()

if __name__ == "__main__":

    path = [
        [[93606.0, 441900.0, -4.904254700249789], 'G'],
        [[ 9.36058074e+04,  4.41900000e+05, -4.91151646e+00], 'G'],
        [[ 9.36036186e+04,  4.41900000e+05, -4.60547266e+00], 'G'],
        [[ 9.36022807e+04,  4.41900000e+05, -4.52621185e+00], 'G'],
        [[ 9.36001751e+04,  4.41900000e+05, -4.55178834e+00], 'G'],
        [[ 9.35981648e+04,  4.41900000e+05, -4.62516807e+00], 'G'],
        [[ 9.35943784e+04,  4.41900000e+05, -4.62364169e+00], 'G'],
        [[ 9.3591028e+04,  4.4190000e+05, -4.6534186e+00], 'G'],
        [[ 9.35896109e+04,  4.41900000e+05, -4.65267961e+00], 'G'],
        [[ 9.35891827e+04,  4.41900000e+05, -4.66882258e+00], 'G']
        ]

    #Materials = ["G", "G", "G", "G", "G", "G", "G", "A0", "A0", "A0", "A0", "A0", "A0", "G"]
    # input:
    # The xmlParser part will deviate differently over direct path than over the others. therefore the function can be called as follows:
    # Direct path:
    #   xmlParser(vertices, material)
    # (1st order) reflected or diffracted path or barriers:
    #   xmlParser(vertices, material, extensions)

    # === vertices and material ===
    # numpy array with arrays/tuples of the coordinates, this includes barriers (TIN point below the point) and reflection edges.
    # vertices = [[(x,y,z), mat], [(x,y,z), mat], [...]]

    # where mat: string
    # groundType: absorbtion index 1: "C"
    # groundType: absorbtion index 0: "G"
    # Building in DSM: "A0"

    # === Extensions ===
    # Extension holds information about reflection and diffraction. It is a dictionary
    # the key is the index of the related vertex, the value is a list with the type, material and the height
    # ext = {
    #   "0":   ["source", 2],       # The source (and receiver) don't have a material.
    #   "id0": [type, height above TIN, material],
    #   "id1": ["wall", 5, "A0"],     # for a reflection against a building 
    #   "id2": ["edge", 3, "A0"],      # For a diffractions around a building (horizontal)
    #   "id3": ["barrier", 4, "A0"]   # for a sound barrier (we currently don't have them, but it could come)
    #   "last":["receiver", 2]
    # }

    extension = {
        0: ['source', 0.05], 
        9: ['receiver', 2]}
    
    path = np.array(path)
    pprint(path)
    #xml_section = XmlParser(vertices, Materials, extension)
    xml_section = XmlParser(path, extension)
    
    xml_section.normalize_path()

    xml_section.douglas_Peucker(0.3)

    xml_section.write_xml("test.xml", True)

    xml_section.visualize_path()

    # test with CNOSSOS like this:
    # put the produced xml file in the CNOSSOS/code / data folder adn run:
    # TestCnossos -w -i="..\data\sample_py.xml"
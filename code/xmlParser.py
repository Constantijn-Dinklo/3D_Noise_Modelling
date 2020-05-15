import xml.etree.cElementTree as ET
import numpy as np
import bisect
import misc
# to be removed later, for debugging
import matplotlib.pyplot as plt

class XmlParser:
    
    def __init__(self, vts, mat, ext):
        self.vts = np.array(vts)
        self.mat = mat
        self.ext = ext


    def normalize_path(self):
        """
        Explination: Move 3D Casrtesian coordinates relative to the starting point (receiver) by subtraction P0 from everypoint
        ---------------
        Input: void
        ---------------
        Output: void
        """
        self.vts -= self.vts[0]

    def align_cross_section_with_x_axis(self):
        """
        Explination: calculate the pythagoras distance and make a new array with the distance d, y=0 and the height z
        ---------------
        Input: void
        ---------------
        Output: void (updates self.vts to align the coordinates with the x axis)
        """
        # calc the diagonal distance for all vertices
        d = (self.vts[:,0] ** 2 + self.vts[:,1] ** 2) ** 0.5

        y = np.zeros(len(self.vts), dtype=float)

        # stack the diagonal distance with the height
        self.vts = np.vstack((d, y, self.vts[:,2])).T

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
        # initalize simple path first first and last point
        path_simple = [0, len(self.vts)-1]
        i = 0

        while(i < len(path_simple) - 1):
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
        
        self.vts = np.array([self.vts[id] for id in path_simple])
                    
    def write_xml(self, filename, validate):
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
            ET.SubElement(ext_type, "h").text = "{:.2f}".format(val[1])
            if (len(ext) > 2):
                ET.SubElement(ext_type, "mat").text = str(val[2])
            
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
        # plot input points, and both source and receiver
        #plt.scatter(abs(self.vts_xyz[:,0]), abs(self.vts_xyz[:,2]))
        
        # plot the lines for both input and translated lines
        #plt.plot(abs(self.vts_xyz[:,0]), abs(self.vts_xyz[:,2]))
        plt.plot(abs(self.vts[:,0]), abs(self.vts[:,2]))
        #plt.plot(abs(self.vts_simple[:,0]), abs(self.vts_simple[:,2]))
        
        plt.show()

if __name__ == "__main__":

    vertices = [
        (7.6, 0.8, 0.6000000000000002), 
        (7.232432432432432, 0.7675675675675676, 0.7675675675675676), 
        (6.72258064516129, 0.7225806451612904, 0.7225806451612904), 
        (5.394594594594595, 0.6054054054054054, 0.6054054054054054), 
        (4.529032258064516, 0.5290322580645161, 1.0), 
        (3.556756756756757, 0.44324324324324327, 0.5567567567567567), 
        (2.335483870967742, 0.335483870967742, 0.664516129032258), 
        (2.2, 0.32352941176470595, 0.9262808349146111), 
        (2.2, 0.32352941176470595, 2.0),
        (1.8, 0.2882352941176471, 2.0), 
        (1.8, 0.2882352941176471, 3.0), 
        (1.2, 0.23529411764705882, 3.0), 
        (1.2, 0.23529411764705882, 0.7823529411764707), 
        (0.8, 0.2, 0.5)
        ]

    Materials = ["G", "G", "G", "G", "G", "G", "G", "G", "G", "G", "G", "G", "G", "G"]
    extension = {}
    # input:
    # The xmlParser part will deviate differently over direct path than over the others. therefore the function can be called as follows:
    # Direct path:
    #   xmlParser(vertices, material)
    # (1st order) reflected or diffracted path or barriers:
    #   xmlParser(vertices, material, extensions)

    # === vertices ===
    # numpy array with arrays/tuples of the coordinates, this includes barriers (TIN point below the point) and reflection edges.
    # vertices = [(x,y,z), (x,y,z), ...]

    # === material ====
    # List with material (string) for each vertex: ["G", "C", "A0"]
    # Which material to choose: 
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

    source = [0, 0, 2]
    receiver = [8, 16, 3]

    extension[0] = ["source", source[2] - vertices[0][2]]
    extension[len(vertices)-1] = ["receiver", receiver[2] - vertices[-1][2]]
    

    #xml_section = XmlParser(vertices, Materials, extension)
    xml_section = XmlParser(vertices, Materials, extension)
    
    xml_section.normalize_path()

    # For direct path only:
    xml_section.align_cross_section_with_x_axis()

    #xml_section.douglas_Peucker(0.3)

    xml_section.write_xml("test.xml", True)

    #xml_section.visualize_path()

    # test with CNOSSOS like this:
    # put the produced xml file in the CNOSSOS/code / data folder adn run:
    # TestCnossos -w -i="..\data\sample_py.xml"
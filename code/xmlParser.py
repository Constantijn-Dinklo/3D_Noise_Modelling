import xml.etree.cElementTree as ET
import numpy as np
import bisect
import misc
# to be removed later, for debugging
import matplotlib.pyplot as plt

class XmlParser:
    
    def __init__(self, vts, srs, rec):
        self.vts_xyz = np.array(vts)
        self.vts_dz = []
        self.vts_dx_simple = []

        self.source_height = srs[2] - vts[0][2]
        self.receiver_height = rec[2] - vts[-1][2]

    def set_coordinates_local(self):
        """
        Explination: Move 3D Casrtesian coordinates relative to the starting point (receiver) by subtraction P0 from everypoint
        ---------------
        Input: void
        ---------------
        Output: void
        """
        self.vts_xyz -= self.vts_xyz[0]

    def unfold_straight_path(self):
        """
        Explination: calculate the pythagoras distance and make a new array with the distance d and the height z
        ---------------
        Input: void
        ---------------
        Output: void (fills self.vts_dz)
        """
        # calc the diagonal distance for all vertices
        D = (self.vts_xyz[:,0] ** 2 + self.vts_xyz[:,1] ** 2) ** 0.5

        # stack the diagonal distance with the height
        self.vts_dz = np.vstack((D, self.vts_xyz[:,2])).T

    def get_offsets_perpendicular(self, start, end):
        """
        Explination:
            calculates the perpendicular distance from points to the the line
        ---------------
        Input: 
            Start = id of the start point
            end = id of the end point
        ---------------
        Output: 
            List of distances
        """
        p_start = self.vts_dz[start]
        p_end = self.vts_dz[end]
        line_length = ((p_end[1] - p_start[1]) ** 2 + (p_end[0] - p_start[0]) ** 2) ** 0.5
        offsets = []

        for id in range(start+1, end):
            # do side test (return lenght of line x perpendicualr distace) so devide it by the length and voila
            diff = abs(misc.side_test(p_start, p_end, self.vts_dz[id])) / line_length
            offsets.append(diff)

        return np.array(offsets)

    def douglas_Peucker(self, threshold):
        # initalize simple path first first and last point
        path_simple = [0, len(self.vts_dz)-1]
        i = 0

        while(True):
            print(i)
            # if we reach the end of the path, we are done.
            if(i == len(path_simple) - 1): 
                # add the values of the simplified list to the class variable.
                self.vts_dx_simple = np.array([self.vts_dz[id] for id in path_simple])
                return

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
                bisect.insort(path_simple, (id_max + start + 1)) # 
            else:
                i += 1
                    
    def write_xml(self, filename):
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
        meteo = ET.SubElement(method, "meteo", model="DEFAULT")
        ET.SubElement(meteo, "pFav").text = "0.3"
        
        # create the path
        path = ET.SubElement(root, "path")

        for point in self.vts_dz:
            # create a control point
            cp = ET.Element("cp")

            # insert the pos (position)
            pos = ET.SubElement(cp, "pos")
            ET.SubElement(pos, "x").text = str(point[0])
            ET.SubElement(pos, "z").text = str(point[1])

            # Insert the material
            ET.SubElement(cp, "mat", id="H")

            # append the created control point to the path
            path.append(cp)

        # set the first point as receiver
        ext_rec = ET.Element("ext")
        rec = ET.SubElement(ext_rec, "receiver")
        ET.SubElement(rec, "h").text = str(self.receiver_height)

        path[0].append(ext_rec)
        # set the last point as source
        ext_srs = ET.Element("ext")
        srs = ET.SubElement(ext_srs, "source")
        ET.SubElement(srs, "h").text = str(self.source_height)

        path[-1].append(ext_srs)
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
        plt.scatter(0, self.vts_dz[0,1] + self.receiver_height)
        plt.scatter(abs(self.vts_dz[-1,0]), self.vts_dz[-1,1] + self.source_height)
        
        # plot the lines for both input and translated lines
        #plt.plot(abs(self.vts_xyz[:,0]), abs(self.vts_xyz[:,2]))
        plt.plot(abs(self.vts_dz[:,0]), abs(self.vts_dz[:,1]))
        plt.plot(abs(self.vts_dx_simple[:,0]), abs(self.vts_dx_simple[:,1]))
        
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

    source = [0, 0, 2]
    receiver = [8, 16, 3]

    xml_section = XmlParser(vertices, source, receiver)
    xml_section.set_coordinates_local()
    xml_section.unfold_straight_path()
    xml_section.douglas_Peucker(0.3)

    #xml_section.write_xml("test.xml")

    xml_section.visualize_path()

    # test with CNOSSOS like this:
    # put the produced xml file in the CNOSSOS/code / data folder adn run:
    # TestCnossos -w -i="..\data\sample_py.xml"
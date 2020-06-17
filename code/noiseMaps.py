import fiona
import numpy as np
import sys
from collections import OrderedDict
from fiona.crs import from_epsg


def dbsum(levels, axis=None):
    """ code from https://github.com/python-acoustics/python-acoustics/blob/master/acoustics/decibel.py
    Energetic summation of levels.
    :param levels: Sequence of levels.
    :param axis: Axis over which to perform the operation.
    .. math:: L_{sum} = 10 \\log_{10}{\\sum_{i=0}^n{10^{L/10}}}
    """
    levels = np.asanyarray(levels)
    return 10.0 * np.log10((10.0 ** (levels / 10.0)).sum(axis=axis))


def read_file_db(filename):
    levels_per_receiver = {}
    with open(filename, 'r') as f:
        lines = f.readlines()
        for line in lines:
            values = line.split()
            receiver_id = int(values[0])
            if receiver_id in levels_per_receiver.keys():
                levels_per_receiver[receiver_id].append(float(values[1]))
            else:
                levels_per_receiver[receiver_id] = [float(values[1])]
    return levels_per_receiver


def read_file_receivers(filename):
    id_receiver = {}
    with open(filename, 'r') as f:
        lines = f.readlines()
        for line in lines:
            values = line.split()
            receiver_id = int(values[0])
            receiver_location = (float(values[1]), float(values[2]))
            id_receiver[receiver_id] = receiver_location
    return id_receiver


def get_noise_levels(levels_per_receiver, receivers_coords):
    sum_per_receiver = []
    for receiver, levels in levels_per_receiver.items():
        sum_per_receiver.append({'geometry': {'type': 'Point',
                                              'coordinates': (
                                                  receivers_coords[receiver][0], receivers_coords[receiver][1])},
                                 'properties': OrderedDict([('id', receiver), ('soundLevel', dbsum(levels))])})
    return sum_per_receiver


def write_to_shp(sum_per_receiver, filepath):
    receiver_schema = {'geometry': 'Point', 'properties': OrderedDict([('id', 'int'), ('soundLevel', 'float')])}
    receivers_crs = from_epsg(28992)
    output_driver = 'ESRI Shapefile'
    with fiona.open(filepath, 'w', driver=output_driver, crs=receivers_crs,
                    schema=receiver_schema) as c:
        for receiver in sum_per_receiver:
            c.write(receiver)


if __name__ == '__main__':
    #main(sys.argv)
    input_file = sys.argv[1]
    input_2_file = sys.argv[2]
    output_file = sys.argv[3]

    file_db = 'input/temp_out (1).txt'
    raw_data = read_file_db(input_file)

    file_receivers = 'output/receiver_dict.txt'
    map_id = read_file_receivers(input_2_file)

    levels_summed = get_noise_levels(raw_data, map_id)
    write_to_shp(levels_summed, output_file)


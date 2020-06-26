# 3D_Noise_Modelling
*maybe a better title?*

*the abstract from your report*

*link to your report once it is uploaded to the TU Delft repository https://repository.tudelft.nl *

This repository is for the 3D Noise Modelling Synthesis Project of the course GEO1011 at the MSc Geomatics program at the Delft Unversity of Technology.

This project is part of the research on [automated reconstruction of 3D input data for noise studies](https://3d.bk.tudelft.nl/projects/noise3d/) at the 3D geoinformation research group of Delft Unversity of Technology.

## Installation

*how to install the software, on which platform*

## Usage

*describe how to run the software*

To run the program the following command can be ran on the command line:

python main.py [constrained_tin] [semantics] [receivers] [sources] [output_folder]

Where:

constrained_tin = the file path to the constrained tin, this should be a 'objp' file type

semantics = the file path to the semantics, these are the buildings and ground types of the area

receivers = the file path to the receiver points

sources = the file path to the sources that generate noise, this should be a 'gml' file type

output_folder = this is the folder where the files will be outputted

### Generating an OBJP file

*describe how to make objp file*

## Limitations

*what are the things that one would expect from this software but it doesn't do them, or not correctly*

#### Spikes
When there is a discrepancy between the precision of vertices in the constrained TIN and the semantics (buildings) in some cases (where the semantics file polygon is rounded of to the inner side, compared to the building in the constrained TIN) a reflection on that wall will have a spike in the cross section, making the computed value incorrect for that cross section.

#### Noise sources
the noise level of a road source is computed using a default noise per meter, and an estimation of the segment length of the noise source. Therefore it does not take speed limit, cars per hour or other types of sources in consideration

## Authors

#!/bin/bash

echo -n "Please provide path to code "
read code_path
echo -n "Please provide path to Test_cnossos Release Folder path "
read cnossos_release_folder_path
echo -n "Please provide path to output Test_cnossos XML files "
read output_xml_folder_path
echo -n "Please provide path to output shapefile containing the sound level at each receiver "
read output_shape_file
# do we need a specific path for receiver_dict

echo -n "Would you like to convert the json constrained TIN to objp constrained TIN? [y] [n] "
read text
case $text in
[Yy])    # both Y and y work
    echo "Please provide input JSON file path"
    read json_file_path
    echo "Please provide output file path"
    read constrained_tin_file_path
    echo "Constraining TIN"
    python $code_path/create_objp.py $json_file_path $constrained_tin_file_path
    echo -n "Please provide the following input files to run the software "
    echo "Please provide the file path to the semantics, these are the buildings and ground types of the area "
    read semantics
    echo "Please provide the file path to the receiver points"
    read receivers
    echo "Please provide the file path to the sources that generate noise, this should be a 'gml' file type"
    read sources
    echo "Please provide this is the folder where the files will be outputted"
    read output_folder
    echo -n "Preparing XML files for Test_cnossos"
    python $code_path/main.py $constrained_tin_file_path $semantics $receivers $sources $output_folder
    echo -n "Getting sound level per receiver"
    sh ./test_cnossos.sh  #change test_cnossos to take input arguments
    echo -n "Done!"
    ;;
[Nn])     # N or n
    echo "You already have a constrained TIN in objp format. Skipping constraining TIN."
    echo -n "Please provide the following input files to run the software "
    echo "Please provide the file path to the constrained tin, this should be an 'objp' file type "
    read constrained_tin_file_path
    echo "Please provide the file path to the semantics, these are the buildings and ground types of the area "
    read semantics
    echo "Please provide the file path to the receiver points"
    read receivers
    echo "Please provide the file path to the sources that generate noise, this should be a 'gml' file type"
    read sources
    echo "Please provide this is the folder where the files will be outputted"
    read output_folder
    echo -n "Preparing XML files for Test_cnossos"
    python $code_path/main.py $constrained_tin_file_path $semantics $receivers $sources $output_folder
    echo -n "Getting sound level per receiver"
    sh ./test_cnossos.sh  #change test_cnossos to take input arguments
    echo -n "Done!"
    ;;
*)         # Anything else
    echo "Please answer y, Y, n or N."
    ;;
esac

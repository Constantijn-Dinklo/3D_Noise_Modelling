#!/bin/bash


#CNOSSOS_RELEASE_FOLDER_PATH=/c/Users/laure/Documents/synthesis/CNOSSOS/cnosses_code/Release
#CNOSSOS_RELEASE_FOLDER_PATH=/c/Users/cosdi/OneDrive/TUDelft/GEOG1011/Cnossos_info/Cnossos_code/cnosses_code/Release
CNOSSOS_RELEASE_FOLDER_PATH=$1

#CODE_PATH=/C/Users/laure/Documents/synthesis
#CODE_PATH=/c/Users/cosdi/OneDrive/TUDelft/3D_Noise_Modelling/code
CODE_PATH=$2

#INPUT_XML_FOLDER_PATH=/c/Users/cosdi/OneDrive/TUDelft/3D_Noise_Modelling/code/scenario_000/output/xml/*
INPUT_XML_FOLDER_PATH=$3/*
#OUTPUT_XML_FOLDER_PATH=/c/Users/cosdi/OneDrive/TUDelft/3D_Noise_Modelling/code/scenario_000/output/output_xml/
OUTPUT_XML_FOLDER_PATH=$4/

TEMP_OUT=temp_out.txt
#receiver_dict=scenario_000/output/receiver_dict.txt
receiver_dict=$5
#output_shape_file=scenario_000/output/receiver_noise_level.shp
output_shape_file=$6

truncate -s 0 $TEMP_OUT

#Loop through all input files
for input_file_path in $INPUT_XML_FOLDER_PATH
do
    #Split the filepath by the / delimiter and store them in the file_path_elements array
    delimiter=/
    s=$input_file_path$delimiter
    file_path_elements=();
    while [[ $s ]]; do
        file_path_elements+=( "${s%%"$delimiter"*}" );
        s=${s#*"$delimiter"};
    done;

    #The last element is always the actual file name
    file_name=${file_path_elements[-1]}

    #Split the filename by the _ delimiter and store  in the file_name_elements array
    delimiter=_
    s=$file_name$delimiter
    file_name_elements=();
    while [[ $s ]]; do
        file_name_elements+=( "${s%%"$delimiter"*}" );
        s=${s#*"$delimiter"};
    done;

    #The second element is always the receiver number
    receiver_number=${file_name_elements[1]}

    #Create an output file for this input file with the same end name, but to a different folder
    output_file_path=$OUTPUT_XML_FOLDER_PATH$file_name

    $CNOSSOS_RELEASE_FOLDER_PATH/TestCnossos.exe -i=$input_file_path -o=$output_file_path
    #If the output file exists then
    if [ -f "$output_file_path" ]; then

        output_value=($(grep -oP '(?<=LeqA>)[^<]+' $output_file_path))
        #echo $output_value

        output_value=$receiver_number" "$output_value

        echo $output_value >> $TEMP_OUT
    fi
done

python $CODE_PATH/noiseMaps.py $TEMP_OUT $receiver_dict $output_shape_file

rm -rf $TEMP_OUT

#!/bin/bash
# ./complete.sh json_file_path constrained_tin_file_path semantics receivers sources xml_for_testcnossos cnossos_release code_path output_xml receiver_dict output_sound_level

python ./create_objp.py $1 $2
python ./main.py $2/constrainted_tin.objp $3 $4 $5 $6
sh ./test_cnossos.sh $7 $8 $6 $9 $10 $11

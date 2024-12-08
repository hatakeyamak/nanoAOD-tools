#!/bin/bash

## Run ./scripts/crab_TTJets.sh CMD [TST] [OPT1] ... [OPT7]
## Where CMD = 'submit' or 'status',
##   and TST = 'test' for test mode
## See crab/README.md for some typical options, or run
## 'crab --help' for a more complete list, including:
## <<< crab status >>>
## '--verboseErrors' : Additional info on failed jobs
## '--long'   : Lists status of each individual job
## <<< crab resubmit >>> and <<< crab getlog >>>
## '--jobids' : Comma-separated list of job IDs
## <<< crab resubmit >>>
## '--force'  : What it sounds like
## '--maxjobruntime=3000' : Allow job to run for 2 days


## Construct the string for 'SUSY_ZH_ZToAll_HToAATo4B_Pt150_M*' samples in DAS (https://cmsweb.cern.ch/das/)
## dasgoclient --query="dataset=/*/Run2018*-UL2018_MiniAODv2_GT36*/MINIAOD"
declare -a datasets=()

# Data
datasets+=(
    "/JetHT/Run2018A-UL2018_MiniAODv2_GT36-v1/MINIAOD"
    "/JetHT/Run2018B-UL2018_MiniAODv2_GT36-v1/MINIAOD"
    "/JetHT/Run2018C-UL2018_MiniAODv2_GT36-v1/MINIAOD"
   " /JetHT/Run2018D-UL2018_MiniAODv2_GT36-v1/MINIAOD"    
) 




 

CMD=$1
TST=$2
if [ "$TST" != "test" ] && [ "$TST" != "Test" ] && [ "$TST" != "TEST" ]; then
    OPTS="$2 $3 $4 $5 $6 $7 $8"
else
    OPTS="$3 $4 $5 $6 $7 $8 $9"
fi

## Run in "test mode" if 2nd command is "test"
if [ "$TST" != "test" ] && [ "$TST" != "Test" ] && [ "$TST" != "TEST" ]; then
    echo -e "\nGoing to run: 'crab $CMD $OPTS'\n"
else
    echo -e "\nGoing to run: 'crab $CMD $OPTS' (in TEST mode)\n"
fi

## Check to make sure the CRAB command is valid
if [ "$CMD" != "submit" ] && [ "$CMD" != "status" ] && [ "$CMD" != "resubmit" ] && [ "$CMD" != "getlog" ]; then
    echo -e "\n'crab $CMD' not an option! Quitting.\n"
    exit
fi 


if [ ! -d "crab/r1" ]; then
    mkdir -p "crab/r1"
fi

# Loop over datasets
for dataset in "${datasets[@]}"
do
    printf "\n\nRunning crab job for ${dataset} \n"

    # Use first part of dataset as directory name for crab job.
    # Add 'ext1' suffix to the directory name if dataset name contains 'ext' substring  
    IFS='/' read -r -a datasetNameInParts <<< "${dataset}"   # split dataset by '/'      
    datasetNamePart1=${datasetNameInParts[1]} # dataset (physics) name is at index 1
    datasetNamePart2=${datasetNameInParts[2]}
    datasetName_toUse=$datasetNamePart1

    # Check if datasetNamePart2 contains 'ext1' strin, and if so, then update datasetName_toUse  
    IFS='_' read -r -a datasetNamePart2_subparts <<< "${datasetNamePart2}"    # split dataset by '_' 
    for substr1 in "${datasetNamePart2_subparts[@]}"
    do
        IFS='-' read -r -a substr1_parts <<< "${substr1}"  # split dataset by '_' 
        for substr2 in "${substr1_parts[@]}"
        do
            if [[ $substr2 = *ext* ]]; then
                datasetName_toUse="${datasetName_toUse}_${substr2}"
            fi
        done
    done
    printf "datasetName_toUse: ${datasetName_toUse} \n" 


    ## <<< *********************************** >>>
    ## <<< ** crab status, resubmit, getlog ** >>>
    ## <<< *********************************** >>>
    if [ "$CMD" = "status" ] || [ "$CMD" = "resubmit" ] || [ "$CMD" = "getlog" ]; then
	    echo crab ${CMD} -d crab/r1/crab_${datasetName_toUse} $OPTS
	    if [ "$TST" != "test" ] && [ "$TST" != "Test" ] && [ "$TST" != "TEST" ]; then
	        crab ${CMD} -d crab/r1/crab_${datasetName_toUse} $OPTS
	    fi
    fi


    ## <<< ***************** >>>
    ## <<< ** crab submit ** >>>
    ## <<< ***************** >>>
    if [ "$CMD" = "submit" ]; then
	    ## Submit crab jobs
	    echo crab submit -c crab_config.py $OPTS Data.inputDataset="${dataset}" General.requestName="${datasetName_toUse}"
	    if [ "$TST" != "test" ] && [ "$TST" != "Test" ] && [ "$TST" != "TEST" ]; then
	        crab submit -c crab_config.py $OPTS Data.inputDataset="${dataset}" General.requestName="${datasetName_toUse}"
	    fi
    fi

done

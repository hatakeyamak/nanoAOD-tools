# nanoAOD-tools
A minimal set of tool for working with NanoAODs (with dependencies on only python + root, not on the CMSSW framework)

**Please note that, starting with CMSSW_13_3_0 (with backports for the coming 13_0_16 and 13_1_2), the framework part of NanoAODTools is maintained as a CMSSW package, in [PhysicsTools/NanoAODTools](https://github.com/cms-sw/cmssw/tree/master/PhysicsTools/NanoAODTools)**. 

This repository and the instructions below are still relevant only for older CMSSW releases.

## Checkout instructions: standalone

You need to setup python 2.7 and a recent ROOT version first.

    git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git NanoAODTools
    cd NanoAODTools
    bash standalone/env_standalone.sh build
    source standalone/env_standalone.sh

Repeat only the last command at the beginning of every session.

Please never commit neither the build directory, nor the empty init.py files created by the script.

## Checkout instructions: CMSSW (CMSSW 12X and below)

    cd $CMSSW_BASE/src
    git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools
    cd PhysicsTools/NanoAODTools
    cmsenv
    scram b

## General instructions to run the post-processing step

The script to run the post-processing step is `scripts/nano_postproc.py`.

The basic syntax of the command is the following:

    python scripts/nano_postproc.py /path/to/output_directory /path/to/input_tree.root

Here is a summary of its features:
* the `-s`,`--postfix` option is used to specify the suffix that will be appended to the input file name to obtain the output file name. It defaults to *_Friend* in friend mode, *_Skim* in full mode.
* the `-c`,`--cut` option is used to pass a string expression (using the same syntax as in TTree::Draw) that will be used to select events. It cannot be used in friend mode.
* the `-J`,`--json` option is used to pass the name of a JSON file that will be used to select events. It cannot be used in friend mode.
* if run with the `--full` option (default), the output will be a full nanoAOD file. If run with the `--friend` option, instead, the output will be a friend tree that can be attached to the input tree. In the latter case, it is not possible to apply any kind of event selection, as the number of entries in the parent and friend tree must be the same.
* the `-b`,`--branch-selection` option is used to pass the name of a file containing directives to keep or drop branches from the output tree. The file should contain one directive among `keep`/`drop` (wildcards allowed as in TTree::SetBranchStatus) or `keepmatch`/`dropmatch` (python regexp matching the branch name) per line, as shown in the [this](python/postprocessing/examples/keep_and_drop.txt) example file.
  * `--bi` and `--bo` allows to specify the keep/drop file separately for input and output trees.  
* the `--justcount` option will cause the script to printout the number of selected events, without actually writing the output file.

Please run with `--help` for a complete list of options.

## How to write and run modules

It is possible to import modules that will be run on each entry passing the event selection, and can be used to calculate new variables that will be included in the output tree (both in friend and full mode) or to apply event filter decisions.

We will use `python/postprocessing/examples/exampleModule.py` as an example. The module definition [file](python/postprocessing/examples/exampleModule.py), containing a simple constructor
```
   exampleModuleConstr = lambda : exampleProducer(jetSelection= lambda j : j.pt > 30)
```
should be imported using the following syntax:

```
python scripts/nano_postproc.py outDir /eos/cms/store/user/andrey/f.root -I PhysicsTools.NanoAODTools.postprocessing.examples.exampleModule exampleModuleConstr
```

Let us now examine the structure of the `exampleProducer` module class. All modules must inherit from `PhysicsTools.NanoAODTools.postprocessing.framework.eventloop.Module`.
* the `__init__` constructor function should be used to set the module options.
* the `beginFile` function should create the branches that you want to add to the output file, calling the `branch(branchname, typecode, lenVar)` method of `wrappedOutputTree`. `typecode` should be the ROOT TBranch type ("F" for float, "I" for int etc.). `lenVar` should be the name of the variable holding the length of array branches (for instance, `branch("Electron_myNewVar","F","nElectron")`). If the `lenVar` branch does not exist already - it can happen if you create a new collection, see an example [here](python/postprocessing/examples/collectionMerger.py)) - it will be automatically created.
* the `analyze` function is called on each event. It should return `True` if the event is to be retained, `False` if it should be dropped.

### Keep/drop branches
See the effect of keep/drop instructions by running:
```
python scripts/nano_postproc.py outDir /eos/cms/store/user/andrey/f.root -I PhysicsTools.NanoAODTools.postprocessing.examples.exampleModule exampleModuleConstr -s _exaModu_keepdrop --bi scripts/keep_and_drop_input.txt --bo scripts/keep_and_drop_output.txt
```
comparing to the previous command (without `--bi` and `--bo`).
The output branch created by _exampleModuleConstr_ produces the same result in both cases. But this one drops all other branches when creating output tree. It also runs faster.

The event interface, defined in `PhysicsTools.NanoAODTools.postprocessing.framework.datamodule`, allows to dynamically construct views of objects organized in collections, based on the branch names, for instance:

    electrons = Collection(event, "Electron")
    if len(electrons)>1: print electrons[0].someVar+electrons[1].someVar
    electrons_highpt = filter(lambda x: x.pt>50, electrons)

and this will access the elements of the `Electron_someVar`, `Electron_pt` branch arrays. Event variables can be accessed simply by `event.someVar`, for instance `event.rho`.

The output branches should be filled calling the `fillBranch(branchname, value)` method of `wrappedOutputTree`. `value` should be the desired value for single-value branches, an iterable with the correct length for array branches. It is not necessary to fill the `lenVar` branch explicitly, as this is done automatically using the length of the passed iterable.


### mht producer
Now, let's have a look at another example, `python/postprocessing/examples/mhtjuProducerCpp.py`, [file](python/postprocessing/examples/mhtjuProducerCpp.py). Similarly, it should be imported using the following syntax:

```
python scripts/nano_postproc.py outDir /eos/cms/store/user/andrey/f.root -I PhysicsTools.NanoAODTools.postprocessing.examples.mhtjuProducerCpp mhtju
```
This module has the same structure of its producer as `exampleProducer`, but in addition it utilizes a C++ code to calculate the mht variable, `src/mhtjuProducerCppWorker.cc`. This code is loaded in the `__init__` method of the producer.


## HToAATo4b NanoAOD v2 production: instructions

### Setting up repository

```
cmssw-el7
cmsrel CMSSW_10_6_30

cd CMSSW_10_6_30/src
cmsenv
scram b -j 6

git cms-addpkg RecoBTag/Combined
git cms-addpkg RecoBTag/ONNXRuntime
git cms-addpkg PhysicsTools/NanoAOD
git cms-addpkg PhysicsTools/PatAlgos
git cms-addpkg DataFormats/PatCandidates
git cms-addpkg CommonTools/RecoAlgos
git cms-addpkg SimDataFormats/JetMatching


git clone -b HtoAA_PNet_PFCand_v2_2024_09_03_AWB_dev git@github.com:abrinke1/RecoBTag-Combined.git RecoBTag/Combined/data

git remote add abrinke1 https://gitlab.cern.ch/abrinke1/cmssw.git 
git checkout -b HtoAA_PNet_PFCand_v2_2024_09_03_AWB_dev
git pull abrinke1 HtoAA_PNet_PFCand_v2_2024_09_03_AWB_dev

git clone -b HtoAA_PNet_PFCand_v2_2024_09_03_AWB_dev git@github.com:abrinke1/PFNano.git PhysicsTools/PFNano
git clone -b nanoPostProc_SS git@github.com:siddhesh86/nanoAOD-tools.git PhysicsTools/NanoAODTools

scram b -j 6
```

### SUbmitting CRAB jobs

```
cd CMSSW_10_6_30/src
cmssw-el7
cmsenv

# set up CRAB environment
voms-proxy-init -voms cms -rfc -valid 192:00
source /cvmfs/cms.cern.ch/crab3/crab.sh

cd PhysicsTools/NanoAODTools/crab_haa4b_NanoAOD_2018_mc
```

To submit crab jobs for 2018 MC signal (or background) samples:
```
cd crab_haa4b_NanoAOD_2018_mc
```
Edit 'datasets' variable in crab_job_signal.sh (or crab_job.sh for brackground samples). 

To submit CRAB jobs:
```
./crab_job_signal.sh submit  # or ./crab_job.sh submit
```

To check status of crab jobs:
```
./crab_job_signal.sh status  # or ./crab_job.sh status
```

To resubmit failed crab jobs:
```
./crab_job_signal.sh resubmit  # or ./crab_job.sh resubmit
```




#this is not mean to be run locally
#
echo Check if TTY
if [ "`tty`" != "not a tty" ]; then
  echo "YOU SHOULD NOT RUN THIS IN INTERACTIVE, IT DELETES YOUR LOCAL FILES"
else

echo "ENV..................................."
env 
echo "VOMS"
voms-proxy-info -all
echo "CMSSW BASE, python path, pwd"
echo "CMSSW_BASE: " $CMSSW_BASE 
echo "PYTHON_PATH: " $PYTHON_PATH
echo "PWD: " $PWD 
echo "ls: " 
ls

echo Found Proxy in: $X509_USER_PROXY
echo "Here there are all the input arguments"
echo $@
echo "argument 1: " $1

kCrabJob=$1

# If you are curious, you can have a look at the tweaked PSet. This however won't give you any information...
#echo "================= PSet.py file =================="
#cat PSet.py
#echo "================= PSet.py file END =================="

# This is what you need if you want to look at the tweaked parameter set!!
#echo "================= Dumping PSet ===================="
#python -c "import PSet; print PSet.process.dumpPython()"
#echo "================= Dumping PSet END ===================="

## Your cmsRun config file is named as PSet.py
echo 'cmsRun -j FrameworkJobReport.xml -p PSet.py'
cmsRun -j FrameworkJobReport.xml -p PSet.py
echo 'DONE cmsRun Nano_MC_addHto4bPlus_crab_cfg.py'

echo "After cmsRun Nano_MC_addHto4bPlus_crab_cfg.py PWD: " $PWD 
echo "After cmsRun Nano_MC_addHto4bPlus_crab_cfg.py ls:"
ls

echo "ls PNet_v1*.root"
ls PNet_v1*.root

echo "python example_postproc_1.py ${kCrabJob} "
python example_postproc_1.py ${kCrabJob}
echo "DONE python example_postproc_1.py ${kCrabJob} "

echo "After python example_postproc_1.py PWD: " $PWD 
echo "After python example_postproc_1.py ls:"
ls

echo "crab_script.sh Done"

fi

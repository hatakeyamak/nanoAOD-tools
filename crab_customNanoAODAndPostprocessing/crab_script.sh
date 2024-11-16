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
rm -rf $CMSSW_BASE/lib/
rm -rf $CMSSW_BASE/src/
rm -rf $CMSSW_BASE/module/
rm -rf $CMSSW_BASE/python/
mv lib $CMSSW_BASE/lib
mv src $CMSSW_BASE/src
mv module $CMSSW_BASE/module
mv python $CMSSW_BASE/python

echo Found Proxy in: $X509_USER_PROXY

echo "Here there are all the input arguments"
echo $@
echo "argument 1: " $1
echo "PWD: " $PWD 
echo ls
ls
echo "ls CMSSW_10_6_30/src/RecoBTag/Combined/data/ParticleNetAK8/Hto4bMassRegressionA/V02 : "
ls CMSSW_10_6_30/src/RecoBTag/Combined/data/ParticleNetAK8/Hto4bMassRegressionA/V02


# If you are curious, you can have a look at the tweaked PSet. This however won't give you any information...
#echo "================= PSet.py file =================="
#cat PSet.py
#echo "================= PSet.py file END =================="

# This is what you need if you want to look at the tweaked parameter set!!
#echo "================= Dumping PSet ===================="
#python -c "import PSet; print PSet.process.dumpPython()"
#echo "================= Dumping PSet END ===================="

#python crab_script.py $1
#python example_postproc_1.py $1
#echo 'cmsRun Nano_MC_addHto4bPlus_crab_cfg.py'
#cmsRun Nano_MC_addHto4bPlus_crab_cfg.py
echo 'cmsRun -j FrameworkJobReport.xml -p PSet.py'
cmsRun -j FrameworkJobReport.xml -p PSet.py
#echo 'cmsRun -j FrameworkJobReport.xml -p Nano_MC_addHto4bPlus_crab_cfg.py'
#cmsRun -j FrameworkJobReport.xml -p Nano_MC_addHto4bPlus_crab_cfg.py
echo 'DONE cmsRun Nano_MC_addHto4bPlus_crab_cfg.py'

echo "After cmsRun Nano_MC_addHto4bPlus_crab_cfg.py PWD: " $PWD 
echo "After cmsRun Nano_MC_addHto4bPlus_crab_cfg.py ls:"
ls

echo "ls PNet_v1*.root"
ls PNet_v1*.root

echo "python example_postproc_1.py"
python example_postproc_1.py 
echo "DONE python example_postproc_1.py"

echo "After python example_postproc_1.py PWD: " $PWD 
echo "After python example_postproc_1.py ls:"
ls

echo "crab_script.sh Done"

fi

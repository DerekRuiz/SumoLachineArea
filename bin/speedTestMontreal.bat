@ECHO OFF

set /p sumocfg="Enter file path of the SUMO configuration file: >"
for %%f in (%~dp0.) do set ParentDirectory=%%~dpf
set sumoplustools=%ParentDirectory%sumoplustools\

@ECHO ON

python %sumoplustools%speedTest\speedTest.py -c %sumocfg% --initial 100 --increment 100 --loop 1 --stop-spawning 300
@ECHO OFF

set /p sumocfg="Enter file path of the SUMO configuration file: >"

@ECHO ON

python speedTest.py -c %sumocfg% --initial 100 --increment 100 --loop 1 --stop-spawning 300
@ECHO OFF
set /p net="Enter file path of the SUMO network file: >"
set /p csv="Enter file path of the intersection csv file: >"
set /p output="Enter file path of the output SUMO network file: >"
set /p useSched="Do you wish to use a file containing schedules for the intersections? (y/n): >"
set sumoplustools=../sumoplustools/

if %useSched% == y (
    set /p schedules="Enter path of the schedules for the intersections file. >"
)

@ECHO ON

python %sumoplustools%TLIntersection/addTLS.py -n %net% -c %csv% -o "tls.nod.xml"

netconvert --sumo-net-file %net% --node-files "tls.nod.xml" -o %output% --tls.allred.time 3 --tls.cycle.time 100 --tls.discard-loaded

if %useSched% != y exit

python addTLSPrograms.py -n %net% -o "tlsProgram.add.xml" -c %schedules%

netconvert -s %net% -i "tlsProgram.add.xml" -o %output%

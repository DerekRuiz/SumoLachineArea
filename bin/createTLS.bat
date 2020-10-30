@ECHO OFF
set /p net="Enter file path of the SUMO network file: >"
set /p csv="Enter file path of the intersection csv file: >"
set /p output="Enter file path of the output SUMO network file: >"
set /p useSched="Do you wish to use a file containing schedules for the intersections? (y/n): >"
for %%f in (%~dp0.) do set ParentDirectory=%%~dpf
set sumoplustools=%ParentDirectory%sumoplustools\

if %useSched% == y (
    set /p schedules="Enter path of the schedules for the intersections file. >"
)

@ECHO ON

python %sumoplustools%TLIntersection\createTLS.py -n %net% -c %csv% -o %sumoplustools%TLIntersection\tls.nod.xml

netconvert --sumo-net-file %net% --node-files %sumoplustools%TLIntersection\tls.nod.xml -o %output% --tls.allred.time 3 --tls.cycle.time 100 --tls.discard-loaded --tls.guess-signals true --tls.guess-signals.dist 300

del %sumoplustools%TLIntersection\tls.nod.xml

if %useSched% != y exit

python createTLSPrograms.py -n %net% -o %sumoplustools%TLIntersection\tlsProgram.add.xml -c %schedules%

netconvert -s %net% -i %sumoplustools%TLIntersection\tlsProgram.add.xml -o %output%

del %sumoplustools%TLIntersection\tlsProgram.add.xml

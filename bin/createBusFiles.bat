@ECHO OFF
set /p net="Enter file path of the SUMO network file: >"
set /p stops="Enter file path of the bus stop shape file: >"
set /p lines="Enter file path of the bus lines shape file: >"
set /p stopOut="Enter file path of the output SUMO bus stops file: >"
set /p lineOut="Enter file path of the output SUMO bus lines file: >"
set /p tripsOut="Enter file path of the output SUMO bus trips file: >"
set /p numBuses="Enter the number of bus on each bus line: >"
set /p interv="Enter the time difference (in seconds) between two buses on a single line: >"

set /p verbose="Do you wish to have detail about the current actions (y/n): >"
IF %verbose%==y (SET verbose=-v) else (SET verbose=)

for %%f in (%~dp0.) do set ParentDirectory=%%~dpf
set sumoplustools=%ParentDirectory%sumoplustools\

@ECHO ON

python %sumoplustools%busnetwork\createBusStops.py -n %net% -s %stops% -o %stopOut% %verbose%

python %sumoplustools%busnetwork\createBusLines.py -n %net% -l %lines% -s %stopOut% -o %lineOut% %verbose%

python %sumoplustools%busnetwork\createBusTrips.py -l %lineOut% -o %tripsOut% -n %numBuses% -i %interv% %verbose%

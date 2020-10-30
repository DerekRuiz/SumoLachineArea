@ECHO OFF
rem Functionality of batch file:
rem - Create traffic analysis zones from net file and shape TAZ file
rem - Create/update configuration file to reference all origin destination matrices
rem - Create trip file for passenger vehicles, add necessary element to file, validate trips can be performed by passenger vehicles
rem - Create trip file for motorcycles, add necessary element to file, validate trips can be performed by motorcycles
rem - Create trip file for buses, add necessary element to file, validate trips can be performed by buses
rem - Create trip file for trucks, add necessary element to file, validate trips can be performed by trucks
rem - Convert trips to routes for all vehicle types
rem - Add stops to routes for all vehicle types

set /p netFile="Enter path of SUMO net file: >"
set /p tazFile="Enter path of TAZ additional file: >"
set /p odDir="Enter the directory containing the origin destination matrices: >"
for %%f in (%~dp0.) do set ParentDirectory=%%~dpf
set sumoplustools=%ParentDirectory%sumoplustools\
set odMatrix=%sumoplustools%OD2Trips\OD_matrix.conf.xml
set edgeTaz=%sumoplustools%OD2Trips\taz_edges.taz.xml

echo Creating trips from OD Matrices ...
python %SUMO_HOME%tools\edgesindistricts.py -n %netFile% -t %tazFile% -o %edgeTaz%

python %sumoplustools%OD2Trips\updateMatrixConf.py -c %odMatrix% --od-matrix-dir %odDir% -t %edgeTaz%

echo.

if %ERRORLEVEL% neq 0 (
    echo Error: Could not create taz data
    echo Exiting script
    pause
    exit
)

set /p tripFolder="Enter path of the folder to store the trip files: >"
set /p routeFolder="Enter path of the folder to store the route files: >"
set /p prefix="Enter a prefix for the trip/route files: >"

rem Ensure trip directory has slashes to attach to the file name
if not %tripFolder:~-2%==\\ (
    if %tripFolder:~-1%==\ (
        set tripFolder=%tripFolder%\
    ) else (
        if not %tripFolder:~-1%==/ set tripFolder=%tripFolder%/
    ) 
)

rem Ensure route directory has slashes to attach to the file name
if not %routeFolder:~-2%==\\ (
    if %routeFolder:~-1%==\ (
        set routeFolder=%routeFolder%\
    ) else (
        if not %routeFolder:~-1%==/ set routeFolder=%routeFolder%/
    ) 
)

rem Attach the directory and file name
set tripPath=%tripFolder%%prefix%
set routePath=%routeFolder%%prefix%


echo Creating trips for passenger vehicles ...
%SUMO_HOME%bin\od2trips -c %odMatrix% -o %tripPath%.passenger.odtrips.xml --scale 3 --vtype "veh_passenger" --prefix "veh"
python %sumoplustools%OD2Trips\addClassToTrips.py -od %tripPath%.passenger.odtrips.xml -i "veh_passenger" -v "passenger"
python %sumoplustools%OD2Trips\validateTrips.py -n %netFile% -t %tripPath%.passenger.odtrips.xml -v "passenger"
echo.

echo Creating trips for motorcyles ...
%SUMO_HOME%bin\od2trips -c %odMatrix% -o %tripPath%.motorcycle.odtrips.xml --scale 1.5 --vtype "moto_motorcycle" --prefix "moto"
python %sumoplustools%OD2Trips\addClassToTrips.py -od %tripPath%.motorcycle.odtrips.xml -i "moto_motorcycle" -v "motorcycle"
python %sumoplustools%OD2Trips\validateTrips.py -n %netFile% -t %tripPath%.motorcycle.odtrips.xml -v "motorcycle"
echo.

echo Creating trips for buses ...
%SUMO_HOME%bin\od2trips -c %odMatrix% -o %tripPath%.bus.odtrips.xml --scale 1 --vtype "bus_bus" --prefix "bus"
python %sumoplustools%OD2Trips\addClassToTrips.py -od %tripPath%.bus.odtrips.xml -i "bus_bus" -v "bus"
python %sumoplustools%OD2Trips\validateTrips.py -n %netFile% -t %tripPath%.bus.odtrips.xml -v "bus"
echo.

echo Creating trips for trucks ...
%SUMO_HOME%bin\od2trips -c %odMatrix% -o %tripPath%.truck.odtrips.xml --scale 0.5 --vtype "truck_truck" --prefix "truck"
python %sumoplustools%OD2Trips\addClassToTrips.py -od %tripPath%.truck.odtrips.xml -i "truck_truck" -v "truck"
python %sumoplustools%OD2Trips\validateTrips.py -n %netFile% -t %tripPath%.truck.odtrips.xml -v "truck"
echo.

echo Converting trips to Routes ...
%SUMO_HOME%bin\duarouter -n %netFile% -r %tripPath%.passenger.odtrips.xml -o %routePath%.passenger.rou.xml
%SUMO_HOME%bin\duarouter -n %netFile% -r %tripPath%.motorcycle.odtrips.xml -o %routePath%.motorcycle.rou.xml
%SUMO_HOME%bin\duarouter -n %netFile% -r %tripPath%.bus.odtrips.xml -o %routePath%.bus.rou.xml
%SUMO_HOME%bin\duarouter -n %netFile% -r %tripPath%.truck.odtrips.xml -o %routePath%.truck.rou.xml
echo.

echo Adding stops to Routes ...
python %sumoplustools%StopSigns\createStops.py -n %netFile% -r %routePath%.passenger.rou.xml -v "passenger"
python %sumoplustools%StopSigns\createStops.py -n %netFile% -r %routePath%.motorcycle.rou.xml -v "motorcycle"
python %sumoplustools%StopSigns\createStops.py -n %netFile% -r %routePath%.bus.rou.xml -v "bus"
python %sumoplustools%StopSigns\createStops.py -n %netFile% -r %routePath%.truck.rou.xml -v "truck"
echo.

del %edgeTaz%
del %odMatrix%

echo Done
pause
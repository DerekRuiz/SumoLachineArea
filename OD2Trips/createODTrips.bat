@ECHO OFF

python %SUMO_HOME%/tools/edgesindistricts.py -n ../lachine.net.xml -t taz_shapes.add.xml -o taz_edges.taz.xml

python updateMatrixConf.py

if %ERRORLEVEL% neq 0 (
    exit
)

echo Creating trips for passenger vehicles
%SUMO_HOME%/bin/od2trips -c OD_matrix.conf.xml -o ODTrips/OD_matrix.passenger.odtrips.xml --scale 3 --vtype "veh_passenger" --prefix "veh"
python addClassToTrips.py -od ODTrips/OD_matrix.passenger.odtrips.xml -i "veh_passenger" -c "passenger"
python removeErrorVehicles.py -n ../lachine.net.xml -t ODTrips/OD_matrix.passenger.odtrips.xml -c "passenger"

echo Creating trips for motorcyles
%SUMO_HOME%/bin/od2trips -c OD_matrix.conf.xml -o ODTrips/OD_matrix.motorcycle.odtrips.xml --scale 1.5 --vtype "moto_motorcycle" --prefix "moto"
python addClassToTrips.py -od ODTrips/OD_matrix.motorcycle.odtrips.xml -i "moto_motorcycle" -c "motorcycle"
python removeErrorVehicles.py -n ../lachine.net.xml -t ODTrips/OD_matrix.motorcycle.odtrips.xml -c "motorcycle"

echo Creating trips for buses
%SUMO_HOME%/bin/od2trips -c OD_matrix.conf.xml -o ODTrips/OD_matrix.bus.odtrips.xml --scale 1 --vtype "bus_bus" --prefix "bus"
python addClassToTrips.py -od ODTrips/OD_matrix.bus.odtrips.xml -i "bus_bus" -c "bus"
python removeErrorVehicles.py -n ../lachine.net.xml -t ODTrips/OD_matrix.bus.odtrips.xml -c "bus"

echo Creating trips for trucks
%SUMO_HOME%/bin/od2trips -c OD_matrix.conf.xml -o ODTrips/OD_matrix.truck.odtrips.xml --scale 0.5 --vtype "truck_truck" --prefix "truck"
python addClassToTrips.py -od ODTrips/OD_matrix.truck.odtrips.xml -i "truck_truck" -c "truck"
python removeErrorVehicles.py -n ../lachine.net.xml -t ODTrips/OD_matrix.truck.odtrips.xml -c "truck"

rem Convert trips to Routes
%SUMO_HOME%/bin/duarouter -n ../lachine.net.xml -r ODTrips/OD_matrix.passenger.odtrips.xml -o ODRoutes/OD_matrix.passenger.rou.xml
%SUMO_HOME%/bin/duarouter -n ../lachine.net.xml -r ODTrips/OD_matrix.motorcycle.odtrips.xml -o ODRoutes/OD_matrix.motorcycle.rou.xml
%SUMO_HOME%/bin/duarouter -n ../lachine.net.xml -r ODTrips/OD_matrix.bus.odtrips.xml -o ODRoutes/OD_matrix.bus.rou.xml
%SUMO_HOME%/bin/duarouter -n ../lachine.net.xml -r ODTrips/OD_matrix.truck.odtrips.xml -o ODRoutes/OD_matrix.truck.rou.xml

echo Done
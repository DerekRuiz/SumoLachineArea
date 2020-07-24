python %SUMO_HOME%/tools/edgesindistricts.py -n ../lachine.net.xml -t taz_shapes.add.xml -o taz_edges.taz.xml

rem Create trips for passenger vehicles
%SUMO_HOME%/bin/od2trips -c OD_matrix.conf.xml -o ODTrips/OD_matrix.passenger.odtrips.xml --scale 20 --vtype "veh_passenger" --prefix "veh"
python addClassToTrips.py -od ODTrips/OD_matrix.passenger.odtrips.xml -i "veh_passenger" -c "passenger"

rem Create trips for motorcyles
%SUMO_HOME%/bin/od2trips -c OD_matrix.conf.xml -o ODTrips/OD_matrix.motorcycle.odtrips.xml --scale 5 --vtype "moto_motorcycle" --prefix "moto"
python addClassToTrips.py -od ODTrips/OD_matrix.motorcycle.odtrips.xml -i "moto_motorcycle" -c "motorcycle"

rem Create trips for passenger vehicles
%SUMO_HOME%/bin/od2trips -c OD_matrix.conf.xml -o ODTrips/OD_matrix.bus.odtrips.xml --scale 1 --vtype "bus_bus" --prefix "bus"
python addClassToTrips.py -od ODTrips/OD_matrix.bus.odtrips.xml -i "bus_bus" -c "bus"

rem Convert trips to Routes
rem %SUMO_HOME%/bin/duarouter -n ../lachine.net.xml -r ODTrips/OD_matrix.passenger.odtrips.xml -o ODTrips/OD_matrix.passenger.rou.xml
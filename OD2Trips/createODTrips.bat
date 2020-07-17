python %SUMO_HOME%/tools/edgesindistricts.py -n ../lachine.net.xml -t taz_shapes.add.xml -o taz_edges.taz.xml

rem Create trips for passenger vehicles
%SUMO_HOME%/bin/od2trips -c OD_matrix.conf.xml -o OD_matrix.odtrips.xml --vtype "veh_passenger" --prefix "veh"

rem Create trips for motorcyles
rem %SUMO_HOME%/bin/od2trips -c OD_matrix.conf.xml -o OD_matrix.odtrips.xml --vtype "moto_motorcycle" --prefix "moto"

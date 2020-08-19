@ECHO OFF

rem information at: "https://sumo.dlr.de/docs/Tools/Trip.html"
rem -p: the frequency of trips in a second. ex -p 0.5 => a trip is added every 0.5 seconds
rem -b: the beginning time that the first trip arrives
rem -e: the end time that the last trip arrives
rem --seed: an initial seed for psuedo randomness
rem --fringe-factor: the probability that a trip starts at an edge with no successor or predecessor
rem Total number of vehicles is: (e - b) / p

@ECHO ON

python "%SUMO_HOME%tools\randomTrips.py" -n lachine.net.xml --seed 42 --fringe-factor 1 -p 1 -o Trips/tripLachine.pedestrian.trips.xml -e 360 -r Trips\tripLachine.pedestrian.rou.xml --vehicle-class pedestrian --pedestrians --prefix ped --max-distance 2000
python "%SUMO_HOME%tools\randomTrips.py" -n lachine.net.xml --seed 42 --fringe-factor 2 -p 1 -o Trips/tripLachine.bicycle.trips.xml -e 360 --vehicle-class bicycle --vclass bicycle --prefix bike --fringe-start-attributes "departSpeed=\"max\"" --max-distance 8000 --trip-attributes "departLane=\"best\"" --validate
python "%SUMO_HOME%tools\randomTrips.py" -n lachine.net.xml --seed 42 --fringe-factor 2 -p 1.5 -o Trips/tripLachine.motorcycle.trips.xml -e 360 --vehicle-class motorcycle --vclass motorcycle --prefix moto --fringe-start-attributes "departSpeed=\"max\"" --max-distance 1200 --trip-attributes "departLane=\"best\"" --validate
python "%SUMO_HOME%tools\randomTrips.py" -n lachine.net.xml --seed 42 --fringe-factor 5 -p 0.75 -o Trips/tripLachine.passenger.trips.xml -e 360 --vehicle-class passenger --vclass passenger --prefix veh --min-distance 300 --trip-attributes "departLane=\"best\"" --fringe-start-attributes "departSpeed=\"max\"" --allow-fringe.min-length 1000 --lanes --validate
python "%SUMO_HOME%tools\randomTrips.py" -n lachine.net.xml --seed 42 --fringe-factor 5 -p 2.5 -o Trips/tripLachine.truck.trips.xml -e 360 --vehicle-class truck --vclass truck --prefix truck --min-distance 600 --fringe-start-attributes "departSpeed=\"max\"" --trip-attributes "departLane=\"best\"" --validate
python "%SUMO_HOME%tools\randomTrips.py" -n lachine.net.xml --seed 42 --fringe-factor 5 -p 2 -o Trips/tripLachine.bus.trips.xml -e 360 --vehicle-class bus --vclass bus --prefix bus --min-distance 600 --fringe-start-attributes "departSpeed=\"max\"" --trip-attributes "departLane=\"best\"" --validate
python "%SUMO_HOME%tools\randomTrips.py" -n lachine.net.xml --seed 42 --fringe-factor 40 -p 10 -o Trips/tripLachine.rail.trips.xml -e 360 --vehicle-class rail --vclass rail --prefix rail --fringe-start-attributes "departSpeed=\"max\"" --min-distance 2400 --trip-attributes "departLane=\"best\"" --validate

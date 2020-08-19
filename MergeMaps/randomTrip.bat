@ECHO OFF

rem information at: "https://sumo.dlr.de/docs/Tools/Trip.html"
rem -p: the frequency of trips in a second. ex -p 0.5 => a trip is added every 0.5 seconds
rem -b: the beginning time that the first trip arrives
rem -e: the end time that the last trip arrives
rem --seed: an initial seed for psuedo randomness
rem --fringe-factor: the probability that a trip starts or ends at an edge with no successor or predecessor
rem Total number of vehicles is: (e - b) / p

@ECHO ON

python "%SUMO_HOME%tools\randomTrips.py" -n montreal.net.xml --seed 42 --fringe-factor 2 -p 1.5 -e 600 -o Trips/montreal.motorcycle.trips.xml --vehicle-class motorcycle --vclass motorcycle --prefix moto --fringe-start-attributes "departSpeed=\"max\"" --min-distance 400 --trip-attributes "departLane=\"best\"" --validate
python "%SUMO_HOME%tools\randomTrips.py" -n montreal.net.xml --seed 42 --fringe-factor 5 -p 0.75 -e 600 -o Trips/montreal.passenger.trips.xml --vehicle-class passenger --vclass passenger --prefix veh --min-distance 300 --trip-attributes "departLane=\"best\"" --fringe-start-attributes "departSpeed=\"max\"" --allow-fringe.min-length 1000 --lanes --validate
python "%SUMO_HOME%tools\randomTrips.py" -n montreal.net.xml --seed 42 --fringe-factor 5 -p 2.5 -e 600 -o Trips/montreal.truck.trips.xml --vehicle-class truck --vclass truck --prefix truck --min-distance 600 --fringe-start-attributes "departSpeed=\"max\"" --trip-attributes "departLane=\"best\"" --validate
python "%SUMO_HOME%tools\randomTrips.py" -n montreal.net.xml --seed 42 --fringe-factor 5 -p 2 -e 600 -o Trips/montreal.bus.trips.xml --vehicle-class bus --vclass bus --prefix bus --min-distance 600 --fringe-start-attributes "departSpeed=\"max\"" --trip-attributes "departLane=\"best\"" --validate

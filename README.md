# SumoLachineArea
Simulate the Lachine and Montreal area traffic

To run a SUMO simulation, ensure that SUMO is installed by downloading from the following webpage: "https://sumo.dlr.de/docs/Downloads.php".

<table>
  <tr>
    <th> Table of Contents </th>
  </tr>
</table>
<ul>
 <li> Added SUMO Tools(#-tools-) </li>
 <ul>
  <li> [Charging Stations](#-charging-station-) </li>
  <li> [Create Map](#-create-map-) </li>
  <li> [Emissions of Vehicles](#-emissions-) </li>
  <li> [Origin to Destination Trips](#-odtrips-) </li>
  <li> [Performance Test](#-speed-test-) </li>
  <li> [Stop Signs](#-stop-signs-) </li>
  <li> [Traffic Light Intersection](#-tl-intersection-) </li>
 </ul>
 <li> [Pre-Built Functions](#-functions-) </li>
 <li> [Examples Simulations](#-examples-) </li>
</ul>

SUMO github page:

        https://github.com/eclipse/sumo

SUMOlib and TraCI are two python modules to communicate with the SUMO application.
SUMOlib pydocs page:

        https://sumo.dlr.de/pydoc/sumolib.html

TraCI pydocs page:

        https://sumo.dlr.de/pydoc/traci.html


<label id="tools"><h2> Added SUMO Tools </h2></label>
Note: All folders and files are located in the 'sumoplustools' directory <br/>
<label id="chargingStation"><h3> Charging Station </h3></label>
Works with charging stations and vehicles with batteries.

Contains the following files:
* addChargingStations.py
* routeToCharge.py

addChargingStation.py : Creates a SUMO additional file containing the charging stations provided by a CSV, JSON, or XML. <br/>
routeToCharge.py : Reroutes vehicles to the closest charging station when low on battery power. Can only be run while a traCI connection has been established to a SUMO server.

<label id="createMaps"><h3> Create Map </h3></label>
Creates SUMO network files from OSM files. OSM files can be given directly or a larger OSM file and a boundary file can be provided.

contains the following files:
* createBoundaryFile.py
* addOSM.py

createBoundaryFile.py : Transforms a geoJSON to a boundary file. <br/>
addOSM.py : Adds an OSM tag to the end of an OSM file if missing.

<label id="emissions"><h3> Emissions of Vehicles </h3></label>
Deals with emission outputs generated from vehicles in the simulation.

Contains the following files:
* displayEmission.py
* emissionIO.py
* generateEmissions.py
* sumoEmission.py

displayEmission.py : Displays the emissions generated in a GeoPackage using plots. <br/>
emissionIO.py : Connects with input / output methods dealing with emissions. <br/>
generateEmissions.py : Gathers options from the command line and calls sumoEmission.py with the inputted options. <br/>
sumoEmission.py : Generates GeoPackage files containg the emission outputs of vehicles for a given. timestep

<label id="odtrips"><h3> Origin to Destination Trips </h3></label>
Uses origin to destination matrices to create trips.

Contains the following files:
* addClassToTrips.py
* updateMatrixConf.py
* validateTrips.py

addClassToTrips.py : Creates a vehicle class and adds it to the trip file. <br/>
updateMatrixConf.py : Updates the given configuration file to reference all OD matrices in a given directory. <br/>
validateTrips.py : Validates the given trip to ensure that the vehicles can travel on it.

<label id="speedTest"><h3> Performance Test </h3></label>
Does performance tests on a configuration file with increasing amount of vehicles.

Contains the following files:
* speedTest.py

speedTest.py : Tests the performance of of the SUMO simulation and outputs it to an output file.

<label id="stopSigns"><h3> Stop Signs </h3></label>
Works with the stops in SUMO.

Contains the following files:
addStops.py

addStops.py : Adds stops to vehicle routes to indicate where the stop signs are.

<label id="tlIntersection"><h3> Traffic Light Intersection </h3></label>
Works with traffic lights in SUMO

Contains the following files:
* addTLS.py
* addTLSPrograms.py

addTLS.py : Creates a SUMO node file containg the traffic light locations. <br/>
addTLSPrograms.py : Creates a SUMO additional file containing the programs of the traffic lights.

<label id="functions"><h2> Pre-Built Functions </h2></label>
Note: All folders and files are located in the 'bin' directory <br/>

* buildRandomTrips.bat : Creates random trips for pedestrians, bicycles, motorcycles, passenger vehicles, trucks, buses, and railways.
* createMap.bat : Creates a SUMO network file from an OSM file and a boundry.
* createODTrips.bat : Creates SUMO route files for passenger vehicles, motorcycles, buses, and trucks using origin to destination matrices.
* createOutputFiles.bat : Generates emission outputs, vehicles positions, lane changes, and VTK files.
* createTLS.bat : Adds traffic lights and their programs to a SUMO network file.
* runWithTraci.py : Runs a SUMO simulation with the traCI program running in the program. This allows parallel integration of custom rerouting.
* speedTestMontreal.bat : Tests the performance of a SUMO simulation with specific arguments.

<label id="examples"><h2> Example Simulations </h2></label>

* Montreal
* Lachine
* Charging Station

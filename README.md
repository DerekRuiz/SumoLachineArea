# SumoLachineArea
Simulate the Lachine and Montreal area traffic

To run a SUMO simulation, ensure that SUMO is installed by downloading from the following webpage: "https://sumo.dlr.de/docs/Downloads.php".

<table>
  <tr>
    <th> Table of Contents </th>
  </tr>
</table>

* [Getting Stated](#-getting-started-)
* [Added SUMO Tools](#-added-sumo-tools-)
  * [Charging Stations](#-charging-station-)
  * [Create Map](#-create-map-)
  * [Emissions of Vehicles](#-emissions-of-vehicles-)
  * [Origin to Destination Trips](#-origin-to-destination-trips-)
  * [Performance Test](#-performance-test-)
  * [Stop Signs](#-stop-signs-)
  * [Traffic Light Intersection](#-traffic-light-intersection-)

* [Pre-Built Functions](#-pre-built-functions-)
* [Example Simulations](#-example-simulations-)


SUMO github page:

        https://github.com/eclipse/sumo

SUMOlib and TraCI are two python modules to communicate with the SUMO application.
SUMOlib pydocs page:

        https://sumo.dlr.de/pydoc/sumolib.html

TraCI pydocs page:

        https://sumo.dlr.de/pydoc/traci.html

<label><h2> Getting Started </h2></label>
Simulation of Urban Mobility has 3 primary types of files necessary to start a simulation: [network](https://github.com/DerekRuiz/SumoLachineArea/wiki/Network-Files) \(.net.xml\), [route](../wiki/Route-Files) \(.rou.xml\), and [SUMO configuration](https://github.com/DerekRuiz/SumoLachineArea/wiki/SUMO-Configuration-Files) \(.sumocfg\) files. Only the extention 'xml' is neccessary to load these files, however, to keep the files organized it is recommended to use the prefix-extention when applicable.

Network files contains all the nodes and edges that represent the intersections and streets of a map. Route files contain the vehicles and the paths that they will take during the simulation. SUMO configuration files allows the ability to run the simulation by referencing the network, route, and any other files.
All of these files can created and edited in the NETEDIT application that comes joined with SUMO.

---
<h3> How to Create Network File </h3>
SUMO has created a webwizard to create an OSM and convert it to a SUMO application. Located in the "%SUMO_HOME%/tools" directory, the file is titled "osmWebWizard.py" (it requires python to start up).
<br/><br/>
If you already have an OSM file that you wish to use, then use SUMO netconvert application. Located in the "%SUMO_HOME%/bin" directory, the file is titled "netconvert.exe". This application must be opened using the command prompt. To convert an OSM file to a SUMO network file, enter the following into the command prompt "%SUMO_HOME%/bin/netconvert.exe --osm-files PATH/TO/OSM_FILE.osm -o PATH/TO/OUTPUT_NETWORK.net.xml" while replacing with relevent file paths. For more available options enter the command "%SUMO_HOME%/bin/netconvert.exe --help".

<h3> How to Start a SUMO Application </h3>
From the NETEDIT application, after importing all the additional and route files, go to the "edit" tab then select "Open in SUMO-GUI" option. This will open the SUMO-GUI application and start the simulation that was opened in the NETEDIT application.

To use the SUMO-GUI, go to the "%SUMO_HOME%/bin" directory and open sumo-gui.exe. Go to the "file" tab then select "Open Simulation..." if you have a .sumocfg file or select "Open Network..." if you have a SUMO network file.

To start a simulation in a command prompt without the SUMO-GUI, open the command prompt and enter "%SUMO_HOME%/bin/sumo.exe" followed by the desired arguments. The most common argument used is "-c PATH/TO/SUMOCONFIG.sumocfg" where the .sumocfg file contains references to all other files used in the simulation. For other options use the argument "--help".

If you have a .sumocfg file then double click on the file or run it in a command prompt. To run in a prompt, type "sumo-gui.exe PATH/TO/SUMOCONFIG.sumocfg" to start the simulation, "sumo-gui.exe" can be omitted from the command if the default application to open a .sumocfg file is the SUMO-GUI application.

<label><h2> Added SUMO Tools </h2></label>
Note: All folders and files are located in the 'sumoplustools' directory <br/>
<label><h3> Charging Station </h3></label>
Works with charging stations and vehicles with batteries.

Contains the following files:
* addChargingStations.py
* routeToCharge.py

addChargingStation.py : Creates a SUMO additional file containing the charging stations provided by a CSV, JSON, or XML. <br/>
routeToCharge.py : Reroutes vehicles to the closest charging station when low on battery power. Can only be run while a traCI connection has been established to a SUMO server.

<label><h3> Create Map </h3></label>
Creates SUMO network files from OSM files. OSM files can be given directly or a larger OSM file and a boundary file can be provided.

contains the following files:
* createBoundaryFile.py
* addOSM.py

createBoundaryFile.py : Transforms a geoJSON to a boundary file. <br/>
addOSM.py : Adds an OSM tag to the end of an OSM file if missing.

<label><h3> Emissions of Vehicles </h3></label>
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

<label><h3> Origin to Destination Trips </h3></label>
Uses origin to destination matrices to create trips.

Contains the following files:
* addClassToTrips.py
* updateMatrixConf.py
* validateTrips.py

addClassToTrips.py : Creates a vehicle class and adds it to the trip file. <br/>
updateMatrixConf.py : Updates the given configuration file to reference all OD matrices in a given directory. <br/>
validateTrips.py : Validates the given trip to ensure that the vehicles can travel on it.

<label><h3> Performance Test </h3></label>
Does performance tests on a configuration file with increasing amount of vehicles.

Contains the following files:
* speedTest.py

speedTest.py : Tests the performance of of the SUMO simulation and outputs it to an output file.

<label><h3> Stop Signs </h3></label>
Works with the stops in SUMO.

Contains the following files:
addStops.py

addStops.py : Adds stops to vehicle routes to indicate where the stop signs are.

<label><h3> Traffic Light Intersection </h3></label>
Works with traffic lights in SUMO

Contains the following files:
* addTLS.py
* addTLSPrograms.py

addTLS.py : Creates a SUMO node file containg the traffic light locations. <br/>
addTLSPrograms.py : Creates a SUMO additional file containing the programs of the traffic lights.

<label><h2> Pre-Built Functions </h2></label>
Note: All folders and files are located in the 'bin' directory <br/>

* buildRandomTrips.bat : Creates random trips for pedestrians, bicycles, motorcycles, passenger vehicles, trucks, buses, and railways.
* createMap.bat : Creates a SUMO network file from an OSM file and a boundry.
* createODTrips.bat : Creates SUMO route files for passenger vehicles, motorcycles, buses, and trucks using origin to destination matrices.
* createOutputFiles.bat : Generates emission outputs, vehicles positions, lane changes, and VTK files.
* createTLS.bat : Adds traffic lights and their programs to a SUMO network file.
* runWithTraci.py : Runs a SUMO simulation with the traCI program running in the program. This allows parallel integration of custom rerouting.
* speedTestMontreal.bat : Tests the performance of a SUMO simulation with specific arguments.

<label><h2> Example Simulations </h2></label>

* Montreal
* Lachine
* Charging Station

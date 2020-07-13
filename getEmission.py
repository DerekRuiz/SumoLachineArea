import sumolib
import traci
import rtree
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import osmnx as ox
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import os, sys

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:   
    sys.exit("Please declare environment variable 'SUMO_HOME'")

sumob = sumolib.checkBinary('sumo')

def setEmissionFile(filename="Outputs/traceEmission.xml"):
    """
    Set the emission output file.
    """
    if not os.path.exists(filename):
        assert Exception('File at "' + str(os.path.abspath(filename)) + '" does not exist. \nCreate emission file in location or change given path using "setEmissionFile(filename)" method.')
    global emission_tree_root
    emission_tree = ET.parse(filename)
    emission_tree_root = emission_tree.getroot()

def setOSMFile(filename="lachine_bbox.osm.xml"):
    """
    Set the OSM file. Creates and initializes the streets GeoDataFrame using OSM file.
    """
    if not os.path.exists(filename):
        assert Exception('File at "' + str(os.path.abspath(filename)) + '" does not exist. \nCreate OSM file in location or change given path using "setOSMFile(filename)" method.')
    global streets_gdf
    lachine = ox.graph_from_xml(filename)
    nodes, streets = ox.graph_to_gdfs(lachine)
    streets_gdf = gpd.GeoDataFrame(streets)
    resetStreetDFEmission()

def setNetworkFile(filename="lachine.net.xml"):
    """
    Set the Network file.
    """
    if not os.path.exists(filename):
        assert Exception('File at "' + str(os.path.abspath(filename)) + '" does not exist. \nCreate network file in location or change given path using "setNetworkFile(filename)" method.')
    global network
    network = sumolib.net.readNet(filename)

def setAllInputFiles(emissionFilename="Outputs/traceEmission.xml", OSMFilename="lachine_bbox.osm.xml", networkFilename="lachine.net.xml"):
    """
    Set all the input files using one function. Equivalent to calling each method individually, used to initialize all inputs.
    """
    setEmissionFile(filename=emissionFilename)
    setOSMFile(filename=OSMFilename)
    setNetworkFile(filename=networkFilename)

def getStreetDF():
    """
    getStreetDF() -> GeoDataFrame
    Return the streets GeoDataFrame.
    """
    global streets_gdf
    return streets_gdf

def resetStreetDFEmission():
    """
    Sets the 'fuel', 'CO2', 'CO', 'HC', 'NOx', 'PMx' columns to 0 in the streets GeoDataFrame.
    """
    global streets_gdf
    streets_gdf['fuel'] = 0
    streets_gdf['CO2'] = 0
    streets_gdf['CO'] = 0
    streets_gdf['HC'] = 0
    streets_gdf['NOx'] = 0
    streets_gdf['PMx'] = 0

def setStreetEmissionTraci(fromStep, toStep=0):
    """
    Sets the emissions of the streets GeoDataFrame using TraCI to create a simulation.
    The simulation steps start at fromStep and end at toStep (not included)
    
    Parameters
    ----------
    fromStep : float
        Initial step to start TraCI at
    toStep : float
        The time step that the TraCI simulation will stop at
        If = 0 then will perform only 1 step
        If < 0 then will continue until no more vehicles in the simulation
    """
    try:
        traci.getConnection()
    except traci.TraCIException:
        traci.start([sumob, '-c','lachine.sumocfg'])

    if traci.simulation.getCurrentTime() / 1000 > fromStep:
        traci.close()
        traci.start([sumob, '-c','lachine.sumocfg'])

    traci.simulationStep(fromStep)

    resetStreetDFEmission()

    if toStep < 0:
        isVehLeft = traci.simulation.getMinExpectedNumber() != 0
        toStep = np.inf
    elif toStep == 0:
        toStep = fromStep + traci.simulation.getDeltaT()
    else:
        isVehLeft = True

    while traci.simulation.getCurrentTime() / 1000 < toStep and isVehLeft:

        calculated_edges = []
        vehicles_running = traci.vehicle.getIDList()

        for vehID in vehicles_running:
            if traci.vehicle.getFuelConsumption(vehID) > 0.00:
                edgeID = traci.lane.getEdgeID(traci.vehicle.getLaneID(vehID))
                if not edgeID in calculated_edges:
                    vehicle_point = traci.vehicle.getPosition(vehID)
                    lon, lat = network.convertXY2LonLat(vehicle_point[0], vehicle_point[1])
                    vehicle_point = Point(lon, lat)

                    fuel_output = traci.edge.getFuelConsumption(edgeID)
                    CO2_output = traci.edge.getCO2Emission(edgeID)
                    CO_output = traci.edge.getCOEmission(edgeID)
                    HC_output = traci.edge.getHCEmission(edgeID)
                    NOx_output = traci.edge.getNOxEmission(edgeID)
                    PMx_output = traci.edge.getPMxEmission(edgeID)

                    calculated_edges.append(edgeID)

                    # Determine street in dataframe from closest position
                    addOutputs(vehicle_point, edgeID, fuel_output, CO2_output, CO_output, HC_output, NOx_output, PMx_output)
        
        traci.simulationStep()
        if toStep < 0:
            isVehLeft = traci.simulation.getMinExpectedNumber() != 0

def setStreetEmissionFile(fromStep, toStep=0):
    """
    Sets the emissions of the streets GeoDataFrame using the traceEmission file to create a simulation.
    The file parses steps starting at fromStep and ending at toStep (not included)
    
    Parameters
    ----------
    fromStep : float
        Initial step to start file parsing at
    toStep : float
        The time step that the file parsing will stop at.
        If = 0 then will perform only 1 step
        If < 0 then will continue until the end of the file
    """
    if toStep == 0:
        toStep = fromStep + 1
    elif toStep < 0:
        toStep = len(emission_tree_root.findall('.//timestamp'))

    resetStreetDFEmission()

    for step in range(fromStep, toStep):
        step_root = emission_tree_root.find('.//timestep[@time="%i.00"]' % step)
        for vehicle in step_root.findall('.//vehicle'):
            fuel_output = float(vehicle.attrib["fuel"])
            if fuel_output > 0.00:
                lane = vehicle.attrib["lane"]
                edge = lane[:-2]

                lon, lat = network.convertXY2LonLat(float(vehicle.attrib["x"]), float(vehicle.attrib["y"]))
                vehicle_point = Point(lon, lat)

                CO2_output = float(vehicle.attrib["CO2"])
                CO_output = float(vehicle.attrib["CO"])
                HC_output = float(vehicle.attrib["HC"])
                NOx_output = float(vehicle.attrib["NOx"])
                PMx_output = float(vehicle.attrib["PMx"])

                # Determine street in dataframe from closest position
                addOutputs(vehicle_point, edge, fuel_output, CO2_output, CO_output, HC_output, NOx_output, PMx_output)

def addOutputs(vehicle_point, edge, fuel_output=0, CO2_output=0, CO_output=0, HC_output=0, NOx_output=0, PMx_output=0):
    global streets_gdf
    for index, row in streets_gdf.iterrows():
                    street_line = row.geometry
                    if (str(row.osmid) in edge): #(street_line.distance(vehicle_point) < 1e-4) and 
                        streets_gdf.loc[index,'fuel'] += fuel_output
                        streets_gdf.loc[index,'CO2'] += CO2_output
                        streets_gdf.loc[index,'CO'] += CO_output
                        streets_gdf.loc[index,'HC'] += HC_output
                        streets_gdf.loc[index,'NOx'] += NOx_output
                        streets_gdf.loc[index,'PMx'] += PMx_output

def closeTraCI():
    try:
        traci.close()
    except traci.FatalTraCIError:
        pass


# TESTING Data

setOSMFile()
setNetworkFile()

user_output = input('Do you wish to use the traceEmission output file?\nIf you select "no" then a simulation will run emission will be generated. (y/n): ')

if('y' in user_output):
    setEmissionFile()
    setStreetEmissionFile(1,10)
else:
    setStreetEmissionTraci(1,10)

closeTraCI()

fig, ax = plt.subplots(1, 1) 
streets_gdf.plot(column="fuel", ax=ax, legend=True)
plt.show()


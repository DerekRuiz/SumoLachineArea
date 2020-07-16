import sumolib
import traci
import rtree
import numpy as np
import math
import geopandas as gpd
from shapely.geometry import Point
import osmnx as ox
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import os, sys
import gc

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:   
    sys.exit("Please declare environment variable 'SUMO_HOME'")

## Global ##

_SUMOB = sumolib.checkBinary('sumo')
streets_gdf = gpd.GeoDataFrame()
emission_tree_root = None
_IS_FIGURE_SET = False

def checkStreetsDF():
    global streets_gdf
    if streets_gdf.empty:
        raise Warning("Streets DataFrame was not set. Use CreateStreetsDF() method to initialize it.")

def checkEmissionFile():
    global emission_tree_root
    if emission_tree_root == None:
        raise Warning("Emission file was not set. Use setEmissionFile() method to initialize it.")

def setEmissionFile(filepath="Outputs/traceEmission.xml"):
    """
    Set the emission output file.
    """
    if not os.path.exists(filepath):
        raise Exception('File at "' + str(os.path.abspath(filepath)) + '" does not exist. \nCreate emission file in location or change given path using "setEmissionFile(filepath)" method.')
    global emission_tree_root
    emission_tree = ET.parse(filepath)
    emission_tree_root = emission_tree.getroot()

def createStreetsDF(filepath="lachine_bbox.osm.xml"):
    """
    Creates and initializes the streets GeoDataFrame using the OSM file.
    """
    if not os.path.exists(filepath):
        raise Exception('File at "' + str(os.path.abspath(filepath)) + '" does not exist. \nCreate OSM file in location or change given path using "createStreetsDF(filepath)" method.')
    global streets_gdf
    lachine = ox.graph_from_xml(filepath)
    nodes, streets = ox.graph_to_gdfs(lachine)
    streets_gdf = gpd.GeoDataFrame(streets)
    streets_gdf['osmid'] = streets_gdf['osmid'].astype(str)
    resetStreetDFEmission()

def setNetworkFile(filepath="lachine.net.xml"):
    """
    Set the Network file.
    """
    if not os.path.exists(filepath):
        raise Exception('File at "' + str(os.path.abspath(filepath)) + '" does not exist. \nCreate network file in location or change given path using "setNetworkFile(filepath)" method.')
    global network
    network = sumolib.net.readNet(filepath)

def setAllInputFiles(emissionfilepath="Outputs/traceEmission.xml", OSMfilepath="lachine_bbox.osm.xml", networkfilepath="lachine.net.xml"):
    """
    Set all the input files using one function. Equivalent to calling each method individually, used to initialize all inputs.
    """
    setEmissionFile(filepath=emissionfilepath)
    createStreetsDF(filepath=OSMfilepath)
    setNetworkFile(filepath=networkfilepath)

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
    checkStreetsDF()

    global streets_gdf
    streets_gdf['fuel'] = 0
    streets_gdf['CO2'] = 0
    streets_gdf['CO'] = 0
    streets_gdf['HC'] = 0
    streets_gdf['NOx'] = 0
    streets_gdf['PMx'] = 0

def setStreetsDFTraci(fromStep, toStep=0, toEnd=False, duration=1, useDuration=False, saveFigures=False, directory="Images"):
    """
    Sets the emissions of the streets GeoDataFrame using TraCI to create a simulation.
    The simulation steps start at fromStep and end at toStep (not included)
    
    Parameters
    ----------
    fromStep : float
        Initial step to start TraCI at

    toStep : float
        The time step that the TraCI simulation will stop at
        If <= 0 then will perform only 1 step

    duration : int
        The amount of unit time (default 1 sec) that the simulation will stop at.
        This will only be used if useDuration is True

    useDuration : bool
        Toggles to use the duration instead of the step number.

    toEnd : bool
        If True then will continue until no more vehicles in the simulation and will ignore toStep

    saveFigures : bool
        If True then will create and save images at each step in the directory under a folder for each category.

    directory : string
        Directory where the emission images will be saved.
    """
    if saveFigures:
        if not os.path.exists(directory):
            raise Exception('Directory "' + str(os.path.abspath(directory)) + '" does not exist.')
        elif not os.path.isdir(directory):
            raise Exception('Directory "' + str(os.path.abspath(directory)) + '" is not a directory.')

    try:
        traci.getConnection()
    except traci.TraCIException:
        traci.start([_SUMOB, '-c','lachine.sumocfg'])

    if traci.simulation.getTime() > fromStep:
        traci.close()
        traci.start([_SUMOB, '-c','lachine.sumocfg'])

    traci.simulationStep(fromStep)

    resetStreetDFEmission()

    if fromStep <= 0:
        fromStep = 1
    
    if toEnd:
        toStep = np.inf
    elif useDuration:
        toStep = fromStep + (traci.simulation.getDeltaT() * duration)
    
    if toStep <= 0 or toStep <= fromStep:
        toStep = fromStep + traci.simulation.getDeltaT()
    
    while traci.simulation.getTime() < toStep and traci.simulation.getMinExpectedNumber() != 0:
        calculated_edges = []
        vehicles_running = traci.vehicle.getIDList()

        for vehID in vehicles_running:
            if traci.vehicle.getFuelConsumption(vehID) > 0.00:
                edgeID = traci.lane.getEdgeID(traci.vehicle.getLaneID(vehID))
                
                if not edgeID in calculated_edges:
                    fuel_output = traci.edge.getFuelConsumption(edgeID)
                    CO2_output = traci.edge.getCO2Emission(edgeID)
                    CO_output = traci.edge.getCOEmission(edgeID)
                    HC_output = traci.edge.getHCEmission(edgeID)
                    NOx_output = traci.edge.getNOxEmission(edgeID)
                    PMx_output = traci.edge.getPMxEmission(edgeID)

                    calculated_edges.append(edgeID)

                    edgeID = edgeID.replace(":","")
                    if 'cluster' in edgeID:
                        edgeID = edgeID.replace("cluster","")
                        cluster = edgeID.split("_")[0:-1]
                        cluster = list(filter(None, cluster))
                    else:
                        edgeID = edgeID.split("_")[0]
                        edgeID = edgeID.split("#")[0]
                        cluster = [str(abs(int(edgeID)))]

                    for edge in cluster:
                        # Determine street in dataframe from closest position
                        addOutputs(edge, fuel_output, CO2_output, CO_output, HC_output, NOx_output, PMx_output)
        
        if saveFigures:
            createFigure(all=False, fuel=True)
            saveFigure(directory + "/Fuel/fuel_" + str(traci.simulation.getTime()))
            createFigure(all=False, CO2=True)
            saveFigure(directory + "/CO2/co2_" + str(traci.simulation.getTime()))
            createFigure(all=False, CO=True)
            saveFigure(directory + "/CO/co_" + str(traci.simulation.getTime()))
            createFigure(all=False, HC=True)
            saveFigure(directory + "/HC/hc_" + str(traci.simulation.getTime()))
            createFigure(all=False, NOx=True)
            saveFigure(directory + "/NOx/nox_" + str(traci.simulation.getTime()))
            createFigure(all=False, PMx=True)
            saveFigure(directory + "/PMx/pmx_" + str(traci.simulation.getTime()))

        traci.simulationStep()

def setStreetsDFFile(fromStep, toStep=0, duration=1, useDuration=False, toEnd=False, saveFigures=False, directory="Images"):
    """
    Sets the accumulated emissions of the streets GeoDataFrame using the traceEmission file to create a simulation.
    The file parses steps starting at fromStep and ending at toStep (not included)
    
    Parameters
    ----------
    fromStep : float
        Initial step to start file parsing at

    toStep : float
        The time step that the file parsing will stop at.
        If <= 0 then will perform only 1 step

    duration : int
        The amount of unit time (default 1 sec) that the file will stop at.
        This will only be used if useDuration is True

    useDuration : bool
        Toggles to use the duration instead of the step number.

    toEnd : bool
        If True then will continue until the end of the file and will ignore toStep and duration

    saveFigures : bool
        If True then will create and save images at each step in the directory under a folder for each category.

    directory : string
        Directory where the emission images will be saved.
    """
    if saveFigures:
        if not os.path.exists(directory):
            raise Exception('Directory "' + str(os.path.abspath(directory)) + '" does not exist.')
        elif not os.path.isdir(directory):
            raise Exception('Directory "' + str(os.path.abspath(directory)) + '" is not a directory.')
        
        if not os.path.exists(directory + "/Fuel"):
            os.makedirs(directory + "/Fuel")
        if not os.path.exists(directory + "/CO2"):
            os.makedirs(directory + "/CO2")
        if not os.path.exists(directory + "/CO"):
            os.makedirs(directory + "/CO")
        if not os.path.exists(directory + "/HC"):
            os.makedirs(directory + "/HC")
        if not os.path.exists(directory + "/NOx"):
            os.makedirs(directory + "/NOx")
        if not os.path.exists(directory + "/PMx"):
            os.makedirs(directory + "/PMx")

    checkEmissionFile()

    if fromStep <= 0:
        fromStep = 1

    if toEnd:
        toStep = len(emission_tree_root.findall('.//timestep'))
    elif useDuration:
        toStep = fromStep + duration
    
    if toStep <= 0 or toStep <= fromStep:
        toStep = fromStep + 1

    resetStreetDFEmission()

    for step in range(fromStep, toStep):
        step_root = emission_tree_root.find('.//timestep[@time="%i.00"]' % step)
        for vehicle in step_root.findall('.//vehicle'):
            fuel_output = float(vehicle.attrib["fuel"])

            if fuel_output > 0.00:
                CO2_output = float(vehicle.attrib["CO2"])
                CO_output = float(vehicle.attrib["CO"])
                HC_output = float(vehicle.attrib["HC"])
                NOx_output = float(vehicle.attrib["NOx"])
                PMx_output = float(vehicle.attrib["PMx"])

                lane = vehicle.attrib["lane"]
                edge = lane.replace(":","")
                if 'cluster' in edge:
                    edge = edge.replace("cluster","")
                    cluster = edge.split("_")[0:-2]
                    cluster = list(filter(None, cluster))
                else:
                    edge = edge.split("_")[0]
                    edge = edge.split("#")[0]
                    cluster = [str(abs(int(edge)))]

                for edge in cluster:
                    # Determine street in dataframe from closest position
                    addOutputs(edge, fuel_output, CO2_output, CO_output, HC_output, NOx_output, PMx_output)
        if saveFigures:
            createFigure(all=False, fuel=True)
            saveFigure(directory + "/Fuel/fuel_" + str(step))
            createFigure(all=False, CO2=True)
            saveFigure(directory + "/CO2/co2_" + str(step))
            createFigure(all=False, CO=True)
            saveFigure(directory + "/CO/co_" + str(step))
            createFigure(all=False, HC=True)
            saveFigure(directory + "/HC/hc_" + str(step))
            createFigure(all=False, NOx=True)
            saveFigure(directory + "/NOx/nox_" + str(step))
            createFigure(all=False, PMx=True)
            saveFigure(directory + "/PMx/pmx_" + str(step))

def addOutputs(edge, fuel_output=0, CO2_output=0, CO_output=0, HC_output=0, NOx_output=0, PMx_output=0):
    checkStreetsDF()

    global streets_gdf
    # Gets all indices where the OSM ID == edge ID
    rowIndices = streets_gdf.index[streets_gdf.loc[:,'osmid'] == edge]

    for index in rowIndices:
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

def createFigure(all=True, fuel=False, CO2=False, CO=False, HC=False, NOx=False, PMx=False):
    """
    Uses the streets GeoDataFrame to create a pyplot figure containing the emissions.
    To display or save the image, use showFigure() or saveFigure() methods.
    """
    checkStreetsDF()

    global streets_gdf

    emissions = []
    if all:
        emissions = ['fuel','CO2','CO','HC','NOx','PMx']
    else:
        if fuel:
            emissions += ['fuel']
        if CO2:
            emissions += ['CO2']
        if CO:
            emissions += ['CO']
        if HC:
            emissions += ['HC']
        if NOx:
            emissions += ['NOx']
        if PMx:
            emissions += ['PMx']
    
    if len(emissions) == 0:
        raise Warning("Cannot create a figure with no categories.")
        
    l = math.floor(math.sqrt(len(emissions)))
    w = math.ceil(len(emissions) / l)

    coords = [(x, y) for x in range(l) for y in range(w)]
    plt.cla()
    plt.clf()
    plt.close("all")
    gc.collect()
    
    fig, axs = plt.subplots(l, w)
    for ax, col in zip(coords, emissions):
        if l == 1 and w == 1:
            streets_gdf.plot(column=col, ax=axs, legend=True, linewidth=(2 * streets_gdf[col] / streets_gdf[col].max()) + 0.02)
            axs.set_title('%s Emissions' % (col[0].upper() + col[1:]))
            axs.margins(-0.2)
            axs.yaxis.pan(-1.2)
            axs.xaxis.pan(0.35)
        elif l == 1:
            streets_gdf.plot(column=col, ax=axs[ax[1]], legend=True, linewidth=(2 * streets_gdf[col] / streets_gdf[col].max()) + 0.02)
            axs[ax[1]].set_title('%s Emissions' % (col[0].upper() + col[1:]))
            axs[ax[1]].margins(-0.2)
            axs[ax[1]].yaxis.pan(-1.2)
            axs[ax[1]].xaxis.pan(0.35)
        else :
            streets_gdf.plot(column=col, ax=axs[ax[0],ax[1]], legend=True, linewidth=(2 * streets_gdf[col] / streets_gdf[col].max()) + 0.02)
            axs[ax[0],ax[1]].set_title('%s Emissions' % (col[0].upper() + col[1:]))
            axs[ax[0],ax[1]].margins(-0.2)
            axs[ax[0],ax[1]].yaxis.pan(-1.2)
            axs[ax[0],ax[1]].xaxis.pan(0.35)

    global _IS_FIGURE_SET
    _IS_FIGURE_SET = True


def showFigure():
    """
    Displays the figure using a pyplot figure.
    """
    global _IS_FIGURE_SET
    if not _IS_FIGURE_SET:
        createFigure()
    plt.show()

def saveFigure(filepath):
    """
    Saves the plot image to the file path. Default extension is a png.
    """
    global _IS_FIGURE_SET
    if not _IS_FIGURE_SET:
        createFigure()
    plt.savefig(filepath)
    
def saveStepFigures(directory="Images", fromStep=1, toStep=0, duration=1, useDuration=False, toEnd=False, useFile=True):
    """
    Creates figures using the streets GeoDataFrame of the emissions from the desired steps.
    Saves the individual figures in the directory under a folder for each emission category.
    ex: directory/Fuel/Fuel1.png
    
    Parameters
    ----------
    directory : string
        Directory where the emission images will be saved.

    fromStep : float
        Initial step to start file parsing at

    toStep : float
        The time step that the file parsing will stop at.
        If <= 0 then will perform only 1 step

    duration : int
        The amount of unit time (default 1 sec) that the file will stop at.
        This will only be used if useDuration is True

    useDuration : bool
        Toggles to use the duration instead of the step number.

    toEnd : bool
        If True then will continue until the end of the file and will ignore toStep and duration

    useFile : bool
        If true then will use the emission file,
        else will create a simulation and run it.
    """
    if useFile:
        setStreetsDFFile(fromStep=fromStep, toStep=toStep, duration=duration, useDuration=useDuration, toEnd=toEnd, saveFigures=True, directory=directory)
    else:
        setStreetsDFTraci(fromStep=fromStep, toStep=toStep, duration=duration, useDuration=useDuration, toEnd=toEnd, saveFigures=True, directory=directory)

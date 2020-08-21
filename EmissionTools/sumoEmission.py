from EmissionTools import emissionIO as eio
from os import path
import sys
import numpy as np
from xml.etree import ElementTree as ET
import sumolib
import traci
import osmnx as ox
import geopandas as gpd
import pandas as pd
import warnings

## Global ##
_MAP_ETYPE_TO_INDEX = {"fuel":0,"co2":1,"co":2,"hc":3,"nox":4,"pmx":5}

def validateEtype(eTypes):
    for eType in eTypes:
        try:
            mapEtypeToIndex(eType)
        except KeyError:
            raise Exception('Emission type of "' + str(eType) + '" is not a valid emission')

def checkSumocfgFile():
    global sumocfgFile
    if not "sumocfgFile" in globals():
        raise Exception("SUMO configuration file was not initialized")

def checkEmissionFile():
    global emission_tree_root
    if not "emission_tree_root" in globals():
        raise Exception("Emission file was not initialized")

def checkStreetsDF():
    global streets_gdf
    if not "streets_gdf" in globals():
        raise Exception("OSM file was not initialized")

def setSumocfgFile(filepath):
    """
    Set the SUMO configuration file.
    """
    if not path.exists(filepath):
        raise Exception('SUMO configuration file at "' + str(path.abspath(filepath)) + '" does not exist')
    global sumocfgFile
    sumocfgFile = filepath

def setEmissionFile(filepath):
    """
    Set the emission output file.
    If the file is too large then the file is split into smaller files
    """
    if not path.exists(filepath):
        raise Exception('Emission file at "' + str(path.abspath(filepath)) + '" does not exist')
    global emission_tree_root
    global emission_file_path
    global has_split
    emission_file_path = filepath

    if eio.validateEmissionFileSize(emission_file_path):
        has_split = False
        emission_tree = ET.parse(emission_file_path)
        emission_tree_root = emission_tree.getroot()
    else:
        warnings.warn("Emission file is too large to parse, will split into smaller files first")
        newfile = eio.splitEmissionFile(emission_file_path)
        
        has_split = True
        emission_tree = ET.parse(newfile)
        emission_tree_root = emission_tree.getroot()
    

def createStreetsDF(filepath):
    """
    Creates and initializes the streets GeoDataFrame using the OSM file.
    """
    if not path.exists(filepath):
        raise Exception('OSM file at "' + str(path.abspath(filepath)) + '" does not exist')
    global streets_gdf
    lachine = ox.graph_from_xml(filepath)
    gdfs = ox.graph_to_gdfs(lachine)
    streets_gdf = gpd.GeoDataFrame(gdfs[1])
    streets_gdf = streets_gdf.drop(columns=['oneway','length','landuse','lanes','highway','service','bridge','access','ref','width','junction','area','tunnel','key','u','v'])
    streets_gdf['osmid'] = streets_gdf['osmid'].astype(str)

def setAllInputFiles(emissionfilepath="Outputs/traceEmission.xml", OSMfilepath="lachine_bbox.osm.xml"):
    """
    Set all the input files using one function. Equivalent to calling each method individually, used to initialize all inputs.
    """
    setEmissionFile(filepath=emissionfilepath)
    createStreetsDF(filepath=OSMfilepath)

def getStreetDF():
    """
    getStreetDF() -> GeoDataFrame
    Return the base streets GeoDataFrame.
    """
    global streets_gdf
    return streets_gdf

def resetEmissionArrays():
    global emission_array
    global _MAP_ETYPE_TO_INDEX
    emission_array = np.zeros((len(_MAP_ETYPE_TO_INDEX), streets_gdf.shape[0]))

def mapEtypeToIndex(eType : str):
    global _MAP_ETYPE_TO_INDEX
    return _MAP_ETYPE_TO_INDEX[eType.lower()]

def addOutputs(edge, emission_outputs):
    """
    Accumulates the outputs of the emissions.
    edge: str
        The edge or street with the outputs

    emission_outputs : dict
        The names of outputs associated with their numerical value
    """
    global streets_gdf
    global emission_array
    checkStreetsDF()

    # Gets all indices where the OSM ID == edge ID
    rowIndices = streets_gdf.index[streets_gdf.loc[:,'osmid'] == edge]

    for index in rowIndices:
        for eType in emission_outputs:
            emission_array[mapEtypeToIndex(eType)][index] += emission_outputs[eType]
        
def saveNumpyArrays(eTypes, index):
    global emission_array
    for eType in eTypes:
        filename = eType + '_' + str(index)
        eio.saveNumpyArray(emission_array[mapEtypeToIndex(eType)], filename)

def saveDataFrame(fromStep, toStep, timeInterval, filename, eTypes):
    dataFrame = getStreetDF().copy()
    if '.gpkg' in filename:
        filename = path.splitext(filename)[0]
        
    for eType in eTypes:
        for step in range(fromStep, toStep, timeInterval):
            stepArr = eio.loadNumpyArray(eType + "_" + str(step))

            hr = step // 3600
            mins = (step % 3600) // 60
            sec = (step % 3600) % 60
            fromTime = ("%i:%.2i.%.2i" % (hr,mins,sec))
            
            nextStep = step + timeInterval
            if nextStep >= toStep:
                nextStep = toStep
            hr = nextStep // 3600
            mins = (nextStep % 3600) // 60
            sec = (nextStep % 3600) % 60
            toTime = ("%i:%.2i.%.2i" % (hr,mins,sec))
            
            #addstep
            dataFrame = dataFrame.join(pd.DataFrame(stepArr))
            dataFrame = dataFrame.rename({0: fromTime + "-" + toTime}, axis=1)

        eio.saveDataFrame(dataFrame, filename + '_' + eType)

def setNextEmissionFile(filepath, index):
    global emission_tree_root
    newfile = eio.getNextEmissionFile(filepath, index)

    emission_tree = ET.parse(newfile)
    emission_tree_root = emission_tree.getroot()

def getNextStepRoot(step):
    global emission_file_path
    global emission_file_index
    global has_split

    while True:
        step_root = emission_tree_root.find('.//timestep[@time="%i.00"]' % (step))
        if not step_root is None:
            return step_root
        elif not has_split:
            return step_root
        
        # Try to get next emission file
        try:
            emission_file_index += 1
            setNextEmissionFile(emission_file_path, emission_file_index)
        except OSError:
            return None
        

    # There is another emission file
    step_root = emission_tree_root.find('.//timestep[@time="%i.00"]' % (step))
    return step_root

def getLastEmissionTime():
    global emission_file_path
    global emission_tree_root
    if has_split:
        last_file = eio.getLastEmissionFile(emission_file_path)
        root = ET.parse(last_file).getroot()
    else:
        root = emission_tree_root
    return int(float(root.find('.//timestep[last()]').attrib['time']))

def getFirstEmissionTime():
    global emission_file_path
    global emission_tree_root
    if has_split:
        first_file = eio.getFirstEmissionFile(emission_file_path)
        root = ET.parse(first_file).getroot()
    else:
        root = emission_tree_root
    return int(float(root.find('.//timestep[1]').attrib['time']))

def collectEmissionsFromFile(filepath, eTypes, fromStep=-1, toStep=-1, timeInterval=0, useDuration=False, duration=1, toEnd=False):
    """
    Gathers emission data from the emission file and saves the output as a GeoPackage file
    The file parses steps starting at fromStep and ending at toStep (not included),
    unless useDuration is True, in which case it uses duration
    
    Parameters
    ----------
    filepath : string
        File path where the geoDataFrame will be saved.
    
    eTypes : List
        List of string containing the emission types that will be collected.

    fromStep : int
        Initial step to start file parsing at

    toStep : int
        The time step that the file parsing will stop at.
        If < 0 then will perform only 1 step

    timeInterval : int
        The number of steps in an interval. Measured in seconds.
        If = 0 then will have a time interval equal to the total run time of the simulation

    useDuration : bool
        Toggles to use the duration instead of the step number.

    duration : int
        The amount of unit time (default 1 sec) that the file will stop at.
        This will only be used if useDuration is True

    toEnd : bool
        If True then will continue until the end of the file and will ignore toStep and duration
    """
    global emission_file_index

    checkEmissionFile()
    validateEtype(eTypes)
    emission_file_index = -1

    if fromStep < 0:
        fromStep = getFirstEmissionTime()

    if toEnd:
        toStep = getLastEmissionTime()
    elif useDuration:
        toStep = fromStep + duration
    
    if toStep >= 0 and toStep <= fromStep:
        raise Exception("Ending time cannot be smaller than start time")
    if toStep < 0:
        toStep = fromStep + 1
    
    if timeInterval <= 0 or timeInterval > toStep - fromStep:
        timeInterval = toStep - fromStep

    for step in range(fromStep, toStep, timeInterval):

        resetEmissionArrays()

        for step_interval in range(timeInterval):
            if step + step_interval >= toStep:
                break
            
            step_root = getNextStepRoot(step + step_interval)

            if step_root is None:
                hr = (step + step_interval) // 3600
                mins = ((step + step_interval) % 3600) // 60
                sec = int(((step + step_interval) % 3600) % 60)
                raise Exception("Time of %i:%.2i.%.2i was not generated in the emission file" % (hr, mins, sec))

            for vehicle in step_root.findall('//vehicle'):
                fuel_output = float(vehicle.attrib["fuel"])

                if fuel_output > 0.00:
                    CO2_output = float(vehicle.attrib["CO2"])
                    CO_output = float(vehicle.attrib["CO"])
                    HC_output = float(vehicle.attrib["HC"])
                    NOx_output = float(vehicle.attrib["NOx"])
                    PMx_output = float(vehicle.attrib["PMx"])
                    emission_output = {'Fuel':fuel_output, 'CO2':CO2_output, 'CO':CO_output, 'HC':HC_output, 'NOx':NOx_output, 'PMx':PMx_output}

                    lane = vehicle.attrib["lane"]
                    edge = lane.replace(":","")
                    if 'cluster' in edge:
                        edge = edge.replace("cluster","")
                        cluster = edge.split("_")[0:-2]
                        cluster = list(filter(None, cluster))
                    else:
                        edge = edge.split("_")[0]
                        edge = edge.split("#")[0]
                        cluster = [edge.replace("-","")]
                        
                    for edge in cluster:
                        # Determine street in dataframe from closest position
                        addOutputs(edge, emission_output)
        
        saveNumpyArrays(eTypes, step)
    
    saveDataFrame(fromStep, toStep, timeInterval, filepath, eTypes)



def collectEmissionsFromTraCI(filepath, eTypes, fromStep, toStep=-1, timeInterval=0, useDuration=False, duration=1, toEnd=False):
    """
    Sets the emissions of the streets GeoDataFrame using TraCI to create a simulation.
    The simulation steps start at fromStep and end at toStep (not included)
    
    Parameters
    ----------
    filepath : string
        File path where the geoDataFrame will be saved.
    
    eTypes : List
        List of string containing the emission types that will be collected.

    fromStep : int
        Initial step to start TraCI at

    toStep : int
        The time step that the TraCI simulation will stop at
        If < 0 then will perform only 1 step

    timeInterval : int
        The number of steps in an interval. Measured in seconds.
        If = 0 then will have a time interval equal to the total run time of the simulation

    useDuration : bool
        Toggles to use the duration instead of the step number.

    duration : int
        The amount of unit time (default 1 sec) that the simulation will stop at.
        This will only be used if useDuration is True

    toEnd : bool
        If True then will continue until no more vehicles in the simulation and will ignore toStep
    """
    global sumocfgFile

    validateEtype(eTypes)
    checkSumocfgFile()
    
    sumob = sumolib.checkBinary('sumo')
    try:
        traci.getConnection()
    except traci.TraCIException:
        traci.start([sumob, '-c', sumocfgFile])

    if traci.simulation.getTime() > fromStep:
        traci.close()
        traci.start([sumob, '-c', sumocfgFile])

    if fromStep < 0:
        raise Exception("Cannot start from a negative time")

    if toEnd:
        toStep = np.inf
    elif useDuration:
        toStep = fromStep + int(traci.simulation.getDeltaT() * duration)
    
    if toStep >= 0 and toStep <= fromStep:
        raise Exception("Ending time cannot be smaller than start time")
    if toStep < 0:
        toStep = fromStep + int(traci.simulation.getDeltaT())
    
    if timeInterval <= 0 or timeInterval > toStep - fromStep:
        timeInterval = toStep - fromStep
    
    traci.simulationStep(fromStep)
    while traci.simulation.getTime() < toStep and traci.simulation.getMinExpectedNumber() != 0:
        
        resetEmissionArrays()

        for step_interval in range(timeInterval):
            if traci.simulation.getTime() + (step_interval * traci.simulation.getDeltaT()) >= toStep:
                break

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
                        emission_output = {'Fuel':fuel_output, 'CO2':CO2_output, 'CO':CO_output, 'HC':HC_output, 'NOx':NOx_output, 'PMx':PMx_output}

                        calculated_edges.append(edgeID)

                        edgeID = edgeID.replace(":","")
                        if 'cluster' in edgeID:
                            edgeID = edgeID.replace("cluster","")
                            cluster = edgeID.split("_")[0:-1]
                            cluster = list(filter(None, cluster))
                        else:
                            edgeID = edgeID.split("_")[0]
                            edgeID = edgeID.split("#")[0]
                            cluster = [edgeID.replace("-","")]

                        for edge in cluster:
                            # Determine street in dataframe from closest position
                            addOutputs(edge, emission_output)            
            traci.simulationStep()

        saveNumpyArrays(eTypes, int(traci.simulation.getTime()))

    if toStep == np.inf:
        toStep = int(traci.simulation.getTime() + traci.simulation.getDeltaT())

    saveDataFrame(fromStep, toStep, timeInterval, filepath, eTypes)

def closeTraCI():
    try:
        traci.close()
    except traci.FatalTraCIError:
        pass


def collectEmissions(filepath, eTypes, fromStep, toStep=-1, timeInterval=0, useDuration=False, duration=1, toEnd=False, useFile=True):
    """
    Wrapper method that allows for easy selection of method and ensures final code is excecuted.

    Gathers emission data from the emission file and saves the output as a GeoPackage file
    The file parses steps starting at fromStep and ending at toStep (not included),
    unless useDuration is True, in which case it uses duration
    
    Parameters
    ----------
    filepath : string
        File path where the geoDataFrame will be saved.
    
    eTypes : List
        List of string containing the emission types that will be collected.

    fromStep : int
        Initial step to start file parsing at

    toStep : int
        The time step that the file parsing will stop at.
        If < 0 then will perform only 1 step

    timeInterval : int
        The number of steps in an interval. Measured in seconds.
        If = 0 then will have a time interval equal to the total run time of the simulation

    useDuration : bool
        Toggles to use the duration instead of the step number.

    duration : int
        The amount of unit time (default 1 sec) that the file will stop at.
        This will only be used if useDuration is True

    toEnd : bool
        If True then will continue until the end of the file and will ignore toStep and duration

    useFile : bool
        If True then will use the emission file, otherwise will create a simulation using TraCI
    """
    try:
        if useFile:
            collectEmissionsFromFile(filepath=filepath, eTypes=eTypes, fromStep=fromStep, toStep=toStep, timeInterval=timeInterval, useDuration=useDuration, duration=duration, toEnd=toEnd)
        else:
            collectEmissionsFromTraCI(filepath=filepath, eTypes=eTypes, fromStep=fromStep, toStep=toStep, timeInterval=timeInterval, useDuration=useDuration, duration=duration, toEnd=toEnd)
    except:
        raise
    finally:
        eio.removeProjectTempFolder()

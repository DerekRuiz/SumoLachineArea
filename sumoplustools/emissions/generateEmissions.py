import os, sys
import numpy as np
from xml.etree import ElementTree as ET
import sumolib
import geopandas as gpd
from rtree import index
from shapely.geometry import LineString

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sumoplustools.emissions import emissionIO as eio
from sumoplustools.emissions import displayEmissions
from sumoplustools.postgresql.psqlObjects import emissionConnection
from sumoplustools import createElement

class EmissionGenerator():
    # Global
    _MAP_ETYPE_TO_INDEX = {"FUEL":0,"CO2":1,"CO":2,"HC":3,"NOX":4,"PMX":5}

    @staticmethod
    def mapEtypeToIndex(eType : str) -> int:
        return EmissionGenerator._MAP_ETYPE_TO_INDEX[eType.upper()]
    
    def __init__(self, net : sumolib.net.Net):
        self.sqlConnection = emissionConnection()
        self.net = net
        self.dataFrameTemplate = self.sqlConnection.getReferenceDF()
        self.mapNetToDF = self.sqlConnection.getNetToDFMap()
        self.resetEmissionArrays()

    def addOutputs(self, edgeID, emission_outputs):
        """
        Accumulates the outputs of the emissions.
        
        Parameters
        ----------
        edgeID : str
            Edge or street with the outputs

        emission_outputs : dict
            Names of outputs associated with their numerical value
        """
        try:
            edgeIndex = self.mapNetToDF[edgeID]
        except KeyError:
            raise Exception('No network edge with id "%s" in net file' % edgeID)
        
        for eType in emission_outputs:
            self.emission_array[self.mapEtypeToIndex(eType)][edgeIndex] += emission_outputs[eType]

    def resetEmissionArrays(self):
        self.emission_array = np.zeros((len(self._MAP_ETYPE_TO_INDEX), self.dataFrameTemplate.shape[0]))

    def saveEmissionArray(self, eTypes, index):
        for eType in eTypes:
            filename = '%s_%.2f' % (eType, index)
            eio.saveNumpyArray(self.emission_array[self.mapEtypeToIndex(eType)], filename)

    def resetSavedEmissions(self, reference=True):
        self.sqlConnection.dropAll_eTables()
        self.sqlConnection.createAll_eTables(reference=reference)

    def saveDataFrame(self, fromStep, toStep, timeInterval, eTypes, filename=None, toSQL=True):
        if toSQL:
            self.resetSavedEmissions()

        # Determine if dataframe will be too large if columns are added per emission type
        largeDF = len(eio.getFilesInTemp(extension=".npy")) / len(eTypes) >= 1000
        
        for eType in eTypes:
            tempFiles = eio.getFilesInTemp(prefix='%s_' % eType, extension=".npy")
            if len(tempFiles) == 0:
                Warning('Cannot save emission type "%s" as no data has been collected for it' % eType)
                continue

            # Initialize table/dataframe
            if not largeDF:
                dataFrame = self.dataFrameTemplate.copy()

            for f in tempFiles:
                time = float(os.path.splitext(f)[0].split("_")[1])
                if time < fromStep:
                    continue
                    
                hr = time // 3600
                mins = (time % 3600) // 60
                sec = (time % 3600) % 60
                fromTime = "%i:%.2i:%.2f" % (hr,mins,sec)
                
                time += timeInterval
                if time > toStep:
                    time = toStep
                
                hr = time // 3600
                mins = (time % 3600) // 60
                sec = (time % 3600) % 60
                toTime = "%i:%.2i:%.2f" % (hr,mins,sec)

                # Do not save time steps of length 0
                if fromTime == toTime:
                    continue
                
                # Adds step to table/dataframe
                stepArr = eio.loadNumpyArray(f)
                if largeDF:
                    if toSQL:
                        self.sqlConnection.addColumn('%s-%s' % (fromTime, toTime), stepArr, eType)
                else:
                    dataFrame = dataFrame.join(gpd.pd.DataFrame(stepArr))
                    dataFrame = dataFrame.rename({0: '%s-%s' % (fromTime, toTime)}, axis=1)
            
            if largeDF:
                if filename:
                    Warning("Cannot save dataframe with too many columns")
            else:
                if '.' in filename:
                    filename = os.path.splitext(filename)[0]
                eio.saveDataFrame(dataFrame, '%s_%s' % (filename, eType))
                if toSQL:
                    dataFrame = gpd.pd.DataFrame(dataFrame.drop('geometry', axis=1))
                    self.sqlConnection.saveDataFrame(dataFrame, eType, overide=True)

            
    def collectEmissions(self, fromStep, toStep, timeInterval, stepLength, eTypes, xmlSource):
        """
        Parses the XML Element Tree iterator and collects the emission data, saving it as numpy arrays to a temporary folder.\n
        The file parses steps starting at fromStep and ending at toStep (not included).

        If the file starts at a time after fromStep, then data will only be collected from the initial file time.\n
        If the file ends at a time before toStep, then the data will only be collected up to the final file time, imitating if the toStep = final time + stepLength
        
        Parameters
        ----------
        fromStep : float
            Initial step to collect emission data

        toStep : float
            Time step that the file parsing will stop at

        timeInterval : float
            Amount of time elapsed when the emission data will be combined. Measured in seconds

        stepLength : float
            Time difference between two steps

        eTypes : List
            List of strings containing the emission types that will be collected.
        
        xmlSource : Iterator
            Iterator containing the XML Element Tree
        """
        def getSecond(arr):
            return arr[1]
        
        self.resetEmissionArrays()
        time = lastTime = fromStep
        
        for _, elem in xmlSource:
            if elem.tag != "timestep":
                continue
            
            time = float(elem.get("time"))
            if time < fromStep:
                elem.clear()
                del elem
                continue
            if time >= toStep:
                break
            
            if time - lastTime >= timeInterval:
                ## SAVE TO SERVER ##
                self.saveEmissionArray(eTypes, lastTime)
                self.resetEmissionArrays()
                lastTime = time

            for vehicle in elem.findall('vehicle'):
                fuel_output = float(vehicle.attrib["fuel"]) * stepLength

                if fuel_output > 0.00:
                    CO2_output = float(vehicle.attrib["CO2"]) * stepLength
                    CO_output = float(vehicle.attrib["CO"]) * stepLength
                    HC_output = float(vehicle.attrib["HC"]) * stepLength
                    NOx_output = float(vehicle.attrib["NOx"]) * stepLength
                    PMx_output = float(vehicle.attrib["PMx"]) * stepLength
                    emission_output = {'Fuel':fuel_output, 'CO2':CO2_output, 'CO':CO_output, 'HC':HC_output, 'NOx':NOx_output, 'PMx':PMx_output}

                    laneID = vehicle.attrib["lane"]
                    if laneID[0] == ":":
                        # vehicle is on a junction
                        x = float(vehicle.attrib["x"])
                        y = float(vehicle.attrib["y"])
                        edges = []
                        radius = 10
                        while len(edges) == 0:
                            edges = self.net.getNeighboringEdges(x, y, radius)
                            radius *= 10
                        
                        closestEdge, _ = sorted(edges, key=getSecond)[0]
                        edgeID = closestEdge.getID()
                    else:
                        # vehicle is on a street
                        laneObj = self.net.getLane(laneID)
                        edgeObj = laneObj.getEdge()
                        edgeID = edgeObj.getID()
                        
                    self.addOutputs(edgeID, emission_output)


            elem.clear()
            del elem
        del xmlSource

        if time < fromStep:
            raise Exception("No emissions between times %.2f - %.2f" % (fromStep. toStep))
        
        # Source does not have enough steps to complete an interval, so the partial interval is saved
        if time != lastTime and time <= toStep:
            ## SAVE TO SERVER ##
            self.saveEmissionArray(eTypes, lastTime)

    def close(self):
        eio.removeProjectTempFolder()
        self.sqlConnection.close()

def generateEmissionDataFrame(net : sumolib.net.Net, fromStep, toStep, timeInterval, stepLength, eTypes, xmlSource, filename=None):
    """
    Convenience function to create EmissinoGeneration object and call collectEmissions and saveDataFrame methods
    """
    emissions = EmissionGenerator(net)
    emissions.collectEmissions(fromStep=fromTime, toStep=toTime, timeInterval=timeInterval, stepLength=step_length, eTypes=eTypes, xmlSource=xmlIter)
    emissions.saveDataFrame(fromStep=fromTime, toStep=toTime, timeInterval=timeInterval, eTypes=eTypes, filename=filename)
    emissions.close()

def getFirstEmissionTime(xmlFile) -> float:
    source = ET.iterparse(xmlFile)
    for _, elem in source:
        if elem.tag == "timestep":
            return float(elem.get("time"))
    del source
    raise Exception("Cannot locate first time step")
        

def getStepLength(xmlFile) -> float:
    times = []
    source = ET.iterparse(xmlFile)
    for _, elem in source:
        if elem.tag == "timestep":
            times += [float(elem.get("time"))]
        if len(times) > 1:
            return times[1] - times[0]
    del source
    return 0.0

if __name__ == "__main__":
    import argparse
    
    def fillOptions(argParser):
        argParser.add_argument("-n", "--net-file", 
                                metavar="FILE", required=True,
                                help="read SUMO network from FILE (mandatory)")
        argParser.add_argument("-e", "--emission-file",
                                metavar="FILE", required=True,
                                help="use FILE to populate data using XML (mandatory)")
        argParser.add_argument("-t", "--emission-types", 
                                type=str, metavar='STR[,STR]*', required=True,
                                help="the emission types that will be collected and saved. Seperate types with a comma (mandatory)")
        argParser.add_argument("-o", "--output-file", 
                                metavar="FILE",
                                help="save emissions with prefix to FILE")
        argParser.add_argument("-s", "--start-time",
                                metavar='INT[:INT:INT]',
                                help="initial time that data is collected from. Can be in seconds or with format of 'hr:min:sec'. Starts at begining if omitted")
        argParser.add_argument("-f", "--finish-time",
                                metavar='INT[:INT:INT]',
                                help="last time that data is collected from. Can be in seconds or with format of 'hr:min:sec'. Terminates 1 second after start if omitted")
        argParser.add_argument("-d", "--duration",
                                metavar='INT[:INT:INT]',
                                help="amount of time that data is collected from. Can be in seconds or with format of 'hr:min:sec'. Terminates after 1 second has elapsed if omitted. Has priority over --finish-time")
        argParser.add_argument("-g", "--go-to-end",
                                action='store_true', dest='toEnd', default=False,
                                help="collect data until the end of file or simulation. Has priority over --duration")
        argParser.add_argument("-i", "--time-interval",
                                metavar='INT[:INT:INT]',
                                help="save the emissions every interval. Can be in seconds or with format of 'hr:min:sec'. Interval equals total runtime if omitted")
        argParser.add_argument("-v", "--verbose",
                                action='store_true', default=False,
                                help="gives a description of the current task")

    def parse_args(args=None):
        argParser = argparse.ArgumentParser(description="Generate emissions and save them to a database")
        fillOptions(argParser)
        return argParser.parse_args(args), argParser
    
    options, argParser = parse_args()
    if options.verbose:
        createElement.addVerboseSteps(["reading SUMO network file","validating inputs","establishing connection to database","collecting emissions","saving emissions"])

    if options.verbose:
        createElement.writeToConsole()
    # Set net file
    try:
        net = sumolib.net.readNet(options.net_file)
    except ValueError:
        argParser.error('could not read "%s" as a SUMO network file' % os.path.abspath(options.net_file))
    if options.verbose:
        createElement.writeToConsole(done=True)

    # Set emission types
    eTypes = options.emission_types.split(",")
    for eType in eTypes:
        try:
            EmissionGenerator.mapEtypeToIndex(eType)
        except KeyError:
            argParser.error('emission type of "%s" is not a valid emission' % str(eType))
    try:
        xmlIter = ET.iterparse(options.emission_file)
        step_length = getStepLength(options.emission_file)
    except FileNotFoundError:
        argParser.error('could not locate emission file "%s"' % os.path.abspath(options.emission_file))

    # Set start time
    if options.start_time:
        try:
            fromTime = float(options.start_time)
        except ValueError:
            try:
                split = options.start_time.split(':')
                fromTime = (int(split[0]) * 3600) + (int(split[1]) * 60) + float(split[2])
            except IndexError:
                argParser.error("--start-time is not in the correct format")
    else:
        fromTime = getFirstEmissionTime(options.emission_file)

    # Set end time
    # Using to end
    if options.toEnd:
        toTime = np.inf
    # Using duration
    elif options.duration:
        try:
            duration = float(options.duration)
        except ValueError:
            try:
                split = options.duration.split(':')
                duration = (int(split[0]) * 3600) + (int(split[1]) * 60) + float(split[2])
            except IndexError:
                argParser.error("--duration is not in the correct format")
        toTime = fromTime + duration
    # Using finish time
    elif options.finish_time:
        try:
            toTime = float(options.finish_time)
        except ValueError:
            try:
                split = options.finish_time.split(':')
                toTime = (int(split[0]) * 3600) + (int(split[1]) * 60) + float(split[2])
            except IndexError:
                argParser.error("--finish-time is not in the correct format")
    else:
        toTime = fromTime + 1

    # Set time interval
    if options.time_interval:
        try:
            timeInterval = int(options.time_interval)
        except ValueError:
            try:
                split = options.time_interval.split(':')
                timeInterval = (int(split[0]) * 3600) + (int(split[1]) * 60) + int(split[2])
            except IndexError:
                argParser.error("--time-interval is not in the correct format")
    else:
        timeInterval = toTime - fromTime
    
    # Test edge cases for time inputs to reduce errors
    if toTime <= fromTime:
        argParser.error("ending time cannot be smaller than start time")
    if timeInterval <= 0:
        argParser.error("step interval cannot be less than 0")
    if timeInterval > toTime - fromTime:
        argParser.error("step interval greater than total time elapsed")
    if timeInterval != np.inf and timeInterval % step_length != 0:
        argParser.error('cannot have a time interval of "%.2f" if the time between steps is %.2f' % (timeInterval, step_length))
    

    if options.verbose:
        createElement.writeToConsole(done=True)
    emissions = EmissionGenerator(net)
    if options.verbose:
        createElement.writeToConsole(done=True)
    emissions.collectEmissions(fromStep=fromTime, toStep=toTime, timeInterval=timeInterval, stepLength=step_length, eTypes=eTypes, xmlSource=xmlIter)
    if options.verbose:
        createElement.writeToConsole(done=True)
    emissions.saveDataFrame(fromStep=fromTime, toStep=toTime, timeInterval=timeInterval, eTypes=eTypes, filename=options.output_file)
    if options.verbose:
        createElement.writeToConsole(done=True)

    emissions.close()


import os, sys
import argparse
import sumolib
import traci
import numpy as np
import osmnx as ox
import geopandas as gpd

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sumoplustools.chargingstations.routeToCharge import RerouteChargingDomain
from sumoplustools.emissions.generateEmissionsTraci import TraciEmissions
from sumoplustools.emissions import emissionIO as eio 

def fillOptions(argParser):
    generalGroup = argParser.add_argument_group("General")
    generalGroup.add_argument("-c", "--sumo-config-file", 
                            metavar="FILE", required=True,
                            help="use FILE to populate data using TraCI (mandatory)")
    generalGroup.add_argument("-g", "--gui", 
                            action='store_true', default=False,
                            help="uses the SUMO GUI")
    generalGroup.add_argument("-s", "--start-on-open",
                            action="store_true", default=False,
                            help="starts the simulation automatically after the GUI is loaded")

    emissionGroup = argParser.add_argument_group("Generate Emissions")
    emissionGroup.add_argument("-e", "--generate-emissions",
                            action='store_true', default=False,
                            help="generate emission outputs")
    emissionGroup.add_argument("--net-file", 
                            metavar="FILE", required='--generate-emissions' in sys.argv or '-e' in sys.argv,
                            help="read SUMO network from FILE (mandatory)")
    emissionGroup.add_argument("--emission-output-file", 
                            metavar="FILE", required='--generate-emissions' in sys.argv or '-e' in sys.argv,
                            help="write emissions with prefix to FILE (mandatory)")
    emissionGroup.add_argument("--emission-types", 
                            type=str, metavar='STR[,STR]*', required='--generate-emissions' in sys.argv or '-e' in sys.argv,
                            help="the emission types that will be collected and saved. Seperate types with a comma (mandatory)")
    emissionGroup.add_argument("--osm-file", 
                            metavar="FILE",
                            help="use FILE to create GeoDataFrame to be saved")
    emissionGroup.add_argument("--emission-start-time",
                            metavar='INT[-INT-INT]',
                            help="initial time that data is collected from. Can be in seconds or with format of 'hr-min-sec'. Starts at begining if omitted")
    emissionGroup.add_argument("--emission-finish-time",
                            metavar='INT[-INT-INT]',
                            help="last time that data is collected from. Can be in seconds or with format of 'hr-min-sec'. Terminates 1 second after start if omitted")
    emissionGroup.add_argument("--emission-duration",
                            metavar='INT[-INT-INT]',
                            help="amount of time that data is collected from. Can be in seconds or with format of 'hr-min-sec'. Terminates after 1 second has elapsed if omitted. Has priority over --finish-time")
    emissionGroup.add_argument("--emission-go-to-end",
                            action='store_true', dest='toEnd', default=False,
                            help="collect data until the end of file or simulation. Has priority over --duration")
    emissionGroup.add_argument("--emission-time-interval",
                            metavar='INT[-INT-INT]',
                            help="the number of step in an interval. Can be in seconds or with format of 'hr-min-sec'. Interval of total runtime if omitted")

    batteryGroup = argParser.add_argument_group("Battery Vehicles")
    batteryGroup.add_argument("-r", "--reroute-charging",
                            action='store_true', default=False,
                            help="reroutes battery type vehicles to charging stations when low on battery")
    batteryGroup.add_argument("--reroute-start-threshold",
                            metavar='FLOAT', default=20,
                            help="percentage of the battery when vehicles reroute to a charging station")
    batteryGroup.add_argument("--reroute-finish-threshold",
                            metavar='FLOAT', default=80,
                            help="percentage of the battery when vehicles stop charging")
    batteryGroup.add_argument("--reroute-random-threshold",
                            action='store_true', default=False,
                            help="increases the threshold when vehicles stop charging by a random number up to 100")
    
def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Start SUMO simulation and manipulate the simulation with traci",usage="%s [-h] -c FILE [-g] [-s] [--generate-emissions] [--reroute-charging]" % (__file__))
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    extraCmd = []
    if options.gui:
        binary = "sumo-gui"
        if options.start_on_open:
            extraCmd += ["--start", "1"]
    else:
        binary = "sumo"

    # Initialize variables
    sumoBinary = sumolib.checkBinary(binary)
    sumocfgFile = options.sumo_config_file
    sumoCmd = [sumoBinary, "-c", sumocfgFile] + extraCmd
    connLabel = "mainConn"
    testLabel = "testConn"

    # Establish connection to SUMO server and set connection
    traci.start(sumoCmd, label=connLabel)
    traci.start(sumoCmd, label=testLabel)
    connection = traci.getConnection(label=connLabel)
    test = traci.getConnection(label=testLabel)

    if options.reroute_charging:
        rcd = RerouteChargingDomain(sumocfgFile, connection)
    
    if options.generate_emissions:
        # Set OSM file
        fileType = eio.getOsmFileType(options.osm_file)
        if fileType is None:
            argParser.error('osm file is not a correct file type. Valid types: .osm, .shp, .geojson, .gpkg')
        elif fileType == "osm":
            dataFrame = gpd.GeoDataFrame(ox.graph_to_gdfs(ox.graph_from_xml(options.osm_file))[1])
        else:
            dataFrame = gpd.read_file(options.osm_file)
        
        # Set net file
        try:
            net = sumolib.net.readNet(options.net_file)
        except ValueError:
            argParser.error('could not read "%s" as a SUMO network file' % os.path.abspath(options.net_file))


        # Validate Emission Inputs #

        # Set emission types
        eTypes = options.emission_types.split(",")
        for eType in eTypes:
            try:
                TraciEmissions.mapEtypeToIndex(eType)
            except KeyError:
                argParser.error('emission type of "%s" is not a valid emission' % str(eType))

        # Set start time
        if options.start_time:
            try:
                fromTime = float(options.start_time)
            except ValueError:
                try:
                    split = options.start_time.split('-')
                    fromTime = (int(split[0]) * 3600) + (int(split[1]) * 60) + float(split[2])
                except IndexError:
                    argParser.error("--start-time is not in the correct format")
        else:
            while test.simulation.getDepartedNumber() == 0:
                test.simulationStep()
            fromTime = test.simulation.getTime()

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
                    split = options.duration.split('-')
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
                    split = options.finish_time.split('-')
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
                    split = options.time_interval.split('-')
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
        if toTime != np.inf and timeInterval % connection.simulation.getDeltaT() != 0:
            argParser.error('cannot have a time interval of "%.2f" if the time between steps is %.2f' % (timeInterval, connection.simulation.getDeltaT()))
        
        # Close test connection
        try:
            test.close()
        except traci.FatalTraCIError:
            pass

        # Validate Emission Inputs Complete #

        t_emissions = TraciEmissions(connection, net, dataFrame)

    # Main loop through the simulation #
    while connection.simulation.getMinExpectedNumber() > 0:
        connection.simulationStep()

        if options.reroute_charging:
            rcd.rerouteVehicles(startRerouteThreshold=options.reroute_start_threshold, finishRerouteThreshold=options.reroute_finish_threshold, randomThreshold=options.reroute_random_threshold)
        
        if options.generate_emissions:
            t_emissions.collectEmissions(fromStep=fromTime, toStep=toTime, timeInterval=timeInterval, eTypes=eTypes)
    
    # Close the simulation
    try:
        connection.close()
    except traci.FatalTraCIError:
        pass

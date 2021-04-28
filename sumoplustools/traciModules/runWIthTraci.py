
import os, sys
import argparse
import sumolib
import traci
import numpy as np
from xml.etree import ElementTree as ET

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from sumoplustools.traciModules.routeToCharge import RerouteChargingDomain
from sumoplustools.traciModules.generateEmissionsTraci import TraciEmissions
from sumoplustools.traciModules.generateVisualsTraci import TraciVisuals

def fillOptions(argParser):
    generalGroup = argParser.add_argument_group("General")
    generalGroup.add_argument("-c", "--sumo-config-file", 
                            metavar="FILE", required=True,
                            help="use FILE to populate data using TraCI (mandatory)")
    generalGroup.add_argument("-g", "--gui", 
                            action='store_true', default=False,
                            help="uses the SUMO GUI to display the map")
    generalGroup.add_argument("-s", "--start-on-open",
                            action="store_true", default=False,
                            help="starts the simulation automatically after the GUI is loaded")
    generalGroup.add_argument("-t", "--traci-commands",
                            type=str, metavar='"--CMD ARG[,] "*',
                            help="TraCI commands to be added when TraCI starts. Commands can be seperated by a ',' (comma) or a ' ' (space)")

    visualGroup = argParser.add_argument_group("Generate Visuals")
    visualGroup.add_argument("-v", "--generate-visuals",
                            action='store_true', default=False,
                            help="generate visualization data for each vehicle")
    visualGroup.add_argument("--visual-start",
                            metavar='INT[:INT:INT]',
                            help="initial time that data is collected from. Can be in seconds or with format of 'hr:min:sec'. Starts at beginning if omitted")
    visualGroup.add_argument("--visual-finish",
                            metavar='INT[:INT:INT]',
                            help="last time that data is collected from. Can be in seconds or with format of 'hr:min:sec'. Terminates 1 second after start if omitted")
    visualGroup.add_argument("--visual-duration",
                            metavar='INT[:INT:INT]',
                            help="amount of time that data is collected from. Can be in seconds or with format of 'hr:min:sec'. Terminates after 1 second has elapsed if omitted. Has priority over --finish-time")
    visualGroup.add_argument("--visual-to-end",
                            action='store_true', dest='visualToEnd', default=False,
                            help="collect data until the end of simulation. Has priority over --duration")

    emissionGroup = argParser.add_argument_group("Generate Emissions")
    emissionGroup.add_argument("-e", "--generate-emissions",
                            action='store_true', default=False,
                            help="generate emission outputs")
    emissionGroup.add_argument("--emission-types", 
                            type=str, metavar='STR[,STR]*', required='--generate-emissions' in sys.argv or '-e' in sys.argv,
                            help="the emission types that will be collected and saved. Separate types with a comma (mandatory)")
    emissionGroup.add_argument("--emission-output-file", 
                            metavar="FILE",
                            help="save emissions with prefix to FILE")
    emissionGroup.add_argument("--emission-start",
                            metavar='INT[:INT:INT]',
                            help="initial time that data is collected from. Can be in seconds or with format of 'hr:min:sec'. Starts at beginning if omitted")
    emissionGroup.add_argument("--emission-finish",
                            metavar='INT[:INT:INT]',
                            help="last time that data is collected from. Can be in seconds or with format of 'hr:min:sec'. Terminates 1 second after start if omitted")
    emissionGroup.add_argument("--emission-duration",
                            metavar='INT[:INT:INT]',
                            help="amount of time that data is collected from. Can be in seconds or with format of 'hr:min:sec'. Terminates after 1 second has elapsed if omitted. Has priority over --finish-time")
    emissionGroup.add_argument("--emission-to-end",
                            action='store_true', dest='emissionToEnd', default=False,
                            help="collect data until the end of simulation. Has priority over --duration")
    emissionGroup.add_argument("--emission-interval",
                            metavar='INT[:INT:INT]',
                            help="save the emissions every interval. Can be in seconds or with format of 'hr:min:sec'. Interval equals 1 timestep if omitted")

    batteryGroup = argParser.add_argument_group("Battery Vehicles")
    batteryGroup.add_argument("-r", "--reroute-charging",
                            action='store_true', default=False,
                            help="reroutes battery type vehicles to charging stations when low on battery")
    batteryGroup.add_argument("--reroute-start",
                            metavar='FLOAT', default=20,
                            help="percentage of the battery when vehicles reroute to a charging station. Default is 20%%")
    batteryGroup.add_argument("--reroute-finish",
                            metavar='FLOAT', default=80,
                            help="percentage of the battery when vehicles stop charging. Default is 80%%")
    batteryGroup.add_argument("--reroute-random",
                            action='store_true', default=False,
                            help="sets the percentage of the battery when vehicles stops charging to a random number between --reroute-finish and 100%%")
    
def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Start SUMO simulation and manipulate the simulation with traci",usage="%s [-h] -c FILE [-g] [-s] [--generate-visuals] [--generate-emissions] [--reroute-charging]" % os.path.basename(__file__))
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

    if options.traci_commands:
        traciCmds = options.traci_commands.split(",")
        for cmd in traciCmds:
            extraCmd += cmd.trim().split()


    # Initialize variables
    sumoBinary = sumolib.checkBinary(binary)
    sumocfgFile = options.sumo_config_file
    sumoCmd = [sumoBinary, "-c", sumocfgFile] + extraCmd
    connLabel = "mainConn"

    # Establish connection to SUMO server and set connection
    try:
        traci.start(sumoCmd, label=connLabel)
        connection = traci.getConnection(label=connLabel)
    except traci.FatalTraCIError as err:
        argParser.error("TraCI Error: " + str(err.args))

    if options.reroute_charging:
        rcd = RerouteChargingDomain(sumocfgFile, connection)
    
    if options.generate_emissions:
        # Set net file
        try:
            root = ET.parse(options.sumo_config_file).getroot()
            net = sumolib.net.readNet(os.path.abspath(os.path.join(os.path.dirname(options.sumo_config_file), root.find("input").find("net-file").get("value"))))
        except:
            argParser.error('could not locate SUMO network file from the configuration file %s' % os.path.abspath(options.sumo_config_file))


        # Validate Emission Inputs #

        # Set emission types
        eTypes = [eType.strip() for eType in options.emission_types.split(",")]
        for eType in eTypes:
            try:
                TraciEmissions.mapEtypeToIndex(eType)
            except KeyError:
                argParser.error('emission type of "%s" is not a valid emission' % str(eType))

        # Set start time
        if options.emission_start:
            try:
                e_fromTime = float(options.emission_start)
            except ValueError:
                try:
                    split = options.emission_start.split(':')
                    e_fromTime = (int(split[0]) * 3600) + (int(split[1]) * 60) + float(split[2])
                except IndexError:
                    argParser.error("--emission-start is not in the correct format")
        else:
            e_fromTime = connection.simulation.getTime()

        # Set end time
        # Using to end
        if options.emissionToEnd:
            e_toTime = np.inf
        # Using duration
        elif options.emission_duration:
            try:
                duration = float(options.emission_duration)
            except ValueError:
                try:
                    split = options.emission_duration.split(':')
                    duration = (int(split[0]) * 3600) + (int(split[1]) * 60) + float(split[2])
                except IndexError:
                    argParser.error("--emission-duration is not in the correct format")
            e_toTime = e_fromTime + duration
        # Using finish time
        elif options.emission_finish:
            try:
                e_toTime = float(options.emission_finish)
            except ValueError:
                try:
                    split = options.emission_finish.split(':')
                    e_toTime = (int(split[0]) * 3600) + (int(split[1]) * 60) + float(split[2])
                except IndexError:
                    argParser.error("--emission-finish is not in the correct format")
        else:
            e_toTime = e_fromTime + 1

        # Set time interval
        if options.emission_interval:
            try:
                e_timeInterval = int(options.emission_interval)
            except ValueError:
                try:
                    split = options.emission_interval.split(':')
                    e_timeInterval = (int(split[0]) * 3600) + (int(split[1]) * 60) + int(split[2])
                except IndexError:
                    argParser.error("--emission-interval is not in the correct format")
        else:
            e_timeInterval = connection.simulation.getDeltaT()
        
        # Test edge cases for time inputs to reduce errors
        if e_toTime <= e_fromTime:
            argParser.error("ending time cannot be smaller than start time")
        if e_timeInterval <= 0:
            argParser.error("step interval cannot be less than 0")
        if e_timeInterval > e_toTime - e_fromTime:
            argParser.error("step interval greater than total time elapsed")
        if e_timeInterval % connection.simulation.getDeltaT() != 0:
            argParser.error('cannot have a time interval of "%.2f" if the time between steps is %.2f' % (e_timeInterval, connection.simulation.getDeltaT()))
        

        # Validate Emission Inputs Complete #
        t_emissions = TraciEmissions(net)
        t_emissions.clearSQLEmissions()
    
    if options.generate_visuals:
        # Set net file
        try:
            if not 'net' in locals():
                root = ET.parse(options.sumo_config_file).getroot()
                net = sumolib.net.readNet(os.path.abspath(os.path.join(os.path.dirname(options.sumo_config_file), root.find("input").find("net-file").get("value"))))
        except:
            argParser.error('could not locate SUMO network file from the configuration file %s' % os.path.abspath(options.sumo_config_file))


        # Validate Visual Inputs #

        # Set start time
        if options.visual_start:
            try:
                v_fromTime = float(options.visual_start)
            except ValueError:
                try:
                    split = options.visual_start.split(':')
                    v_fromTime = (int(split[0]) * 3600) + (int(split[1]) * 60) + float(split[2])
                except IndexError:
                    argParser.error("--visual-start is not in the correct format")
        else:
            v_fromTime = connection.simulation.getTime()

        # Set end time
        # Using to end
        if options.visualToEnd:
            v_toTime = np.inf
        # Using duration
        elif options.visual_duration:
            try:
                duration = float(options.visual_duration)
            except ValueError:
                try:
                    split = options.visual_duration.split(':')
                    duration = (int(split[0]) * 3600) + (int(split[1]) * 60) + float(split[2])
                except IndexError:
                    argParser.error("--duration is not in the correct format")
            v_toTime = v_fromTime + duration
        # Using finish time
        elif options.visual_finish:
            try:
                v_toTime = float(options.visual_finish)
            except ValueError:
                try:
                    split = options.visual_finish.split(':')
                    v_toTime = (int(split[0]) * 3600) + (int(split[1]) * 60) + float(split[2])
                except IndexError:
                    argParser.error("--finish-time is not in the correct format")
        else:
            v_toTime = v_fromTime + 1

        
        # Test edge cases for time inputs to reduce errors
        if v_toTime <= v_fromTime:
            argParser.error("ending time cannot be smaller than start time")
        

        # Validate Emission Inputs Complete #
        t_visuals = TraciVisuals(net)
        t_visuals.clearSQLVisuals()

    # Main loop through the simulation #
    while connection.simulation.getMinExpectedNumber() > 0:
        if options.reroute_charging:
            rcd.rerouteVehicles(startRerouteThreshold=options.reroute_start_threshold, finishRerouteThreshold=options.reroute_finish_threshold, randomThreshold=options.reroute_random_threshold)
        if options.generate_emissions:
            collectEmissions = t_emissions.verifyEmissionCollection(fromStep=e_fromTime, toStep=e_toTime, timeInterval=e_timeInterval, eTypes=eTypes, connection=connection)
        if options.generate_visuals:
            collectVisuals = t_visuals.verifyVisualCollection(fromStep=v_fromTime, toStep=v_toTime, connection=connection)

        for vehID in connection.vehicle.getIDList():
            if options.generate_emissions and collectEmissions:
                t_emissions.collectVehicleEmissions(vehID, connection)
            if options.generate_visuals and collectVisuals:
                t_visuals.collectVehicleVisuals(vehID, connection)

        connection.simulationStep()

    if options.generate_emissions:
        if options.emission_output_file:
            t_emissions.saveToDataFrame(fromTime=e_fromTime, toTime=e_toTime, eTypes=eTypes, filename=options.emission_output_file)
        t_emissions.close()
    if options.generate_visuals:
        t_visuals.close()

    # Close the simulation
    try:
        connection.close()
    except traci.FatalTraCIError:
        pass


'''cd C:/Users/epicb/Documents/GitHub/SumoLachineArea/Montreal
python ../bin/runwithtraci.py -c montreal.sumocfg -e --emission-to-end --emission-types fuel
python ../bin/runwithtraci.py -c montreal.sumocfg -v --visual-to-end

10 000:
-v save to sql -> 0.245, 0.245, 0.452

100 000:
-v save to sql -> 0.254, 0.248, 0.249, 0.484, 0.448

-e -v -> [500 veh] 0.513, 0.531, 0.501 [1000 veh] 0.979, 0.935, 0.936

1 veh -> 0.001 sec to compute

'''
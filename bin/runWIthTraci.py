
import sumolib
import traci
import argparse
from sumoplustools.ChargingStation import routeToCharge as cs


def fillOptions(argParser):
    argParser.add_argument("-c", "--sumo-config-file", 
                            metavar="FILE", required=True,
                            help="use FILE to populate data using TraCI (mandatory)")
    argParser.add_argument("-g", "--gui", 
                            action='store_true', default=False,
                            help="uses the SUMO GUI")
    argParser.add_argument("-s", "--start-on-open",
                            action="store_true", default=False,
                            help="starts the simulation automatically after the GUI is loaded")

def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Start SUMO simulation with vehicles with batteries reroute to charging stations")
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

    # Establish connection to SUMO server and set connection
    traci.start(sumoCmd, label=connLabel)
    connection = traci.getConnection(label=connLabel)

    rcd = cs.rerouteChargingDomain(sumocfgFile, connection)

    while connection.simulation.getMinExpectedNumber() > 0:
        connection.simulationStep()

        print("current time: ", connection.simulation.getTime())
        rcd.rerouteVehicles()
    
    # Close the simulation
    try:
        print("done")
        connection.close()
    except:
        pass

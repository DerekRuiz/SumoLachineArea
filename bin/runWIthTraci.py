
import sumolib
import traci
import argparse
import sumoplustools.ChargingStation.retouteTest as cs


def fillOptions(argParser):
    argParser.add_argument("-c", "--sumo-config-file", 
                            metavar="FILE", required=True,
                            help="use FILE to populate data using TraCI (mandatory)")
    argParser.add_argument("-g", "--gui", 
                            action='store_true', default=False,
                            help="appends testing results to FILE")

def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Start SUMO simulation with vehicles with batteries reroute to charging stations")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()
    
    if options.gui:
        binary = "sumo-gui"
    else:
        binary = "sumo"

    sumoBinary = sumolib.checkBinary(binary)
    sumocfgFile = options.sumo_config_file
    sumoCmd = [sumoBinary, "-c", sumocfgFile] #, "--start", "1"

    try:
        traci.getConnection()
    except traci.TraCIException:
        traci.start(sumoCmd)

    while traci.simulation.getMinExpectedNumber() > 0:
        print("current time: ",traci.simulation.getTime())
        
        cs.updateAllElecVehicleChargingRoutes()
        
        traci.simulationStep()

    try:
        print("done")
        traci.close()
    except:
        pass

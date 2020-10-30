import sys, os
import argparse
import sumolib
from xml.etree import ElementTree as ET

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sumoplustools import netHandler
from sumoplustools import verbose

def fillOptions(argParser):
    argParser.add_argument("-l", "--bus-lines", 
                            metavar="FILE", required=True,
                            help="the FILE containing the SUMO bus routes (mandatory)")
    argParser.add_argument("-o", "--output-file", 
                            metavar="FILE", required=True,
                            help="the FILE output with the bus trips elements (mandatory)")
    argParser.add_argument("-n", "--vehicles-per-line", 
                            metavar="INT", default=1, dest="numBuses", type=int,
                            help="the number of buses on a line")
    argParser.add_argument("-i", "--interval",
                            metavar="FLOAT", default=0.0, type=float,
                            help="time interval (in seconds) between two buses departing on the same route")
    argParser.add_argument("-v", "--verbose",
                            action="store_true", default=False,
                            help="gives description of current task")


def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Create route file with the bus trips")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    if options.verbose:
        verbose.addVerboseSteps(["extracting bus lines","adding vehicle trips","writing to file"])
        verbose.writeToConsole()
    xmlSource = ET.iterparse(options.bus_lines)
    root = ET.Element("routes")
    root.append(ET.Element("vType", {"id":"vType_BUS", "vClass":"bus","length":"%.2f" % netHandler.sizeOfBus}))
    # Create roots to for each time interval
    roots = []
    for i in range(options.numBuses):
        roots += [ET.Element("root%i" % i)]
    if options.verbose:
        verbose.writeToConsole(done=True)

    vehIdx = 0
    for _, elem in xmlSource:
        if elem.tag != "route":
            continue

        for vehicle_num in range(options.numBuses):
            # Append vehicle to the time interval root
            roots[vehicle_num].append(ET.Element("vehicle", {"id":"bus_%i" % vehIdx, "type":"vType_BUS", "route":elem.get("id"), "depart":"%.2f" % (vehicle_num*options.interval)}))
            vehIdx += 1
            if options.verbose:
                verbose.writeToConsole(verboseValue=vehIdx)
        
        elem.clear()
        del elem
    del xmlSource

    # Append vehicles in sequence of time
    for elem in roots:
        for veh in elem.iterfind("vehicle"):
            root.append(veh)

    if options.verbose:
        verbose.writeToConsole(done=True)
    tree = ET.ElementTree(root)
    if not options.output_file.endswith('.rou.xml'):
        options.output_file = os.path.splitext(options.output_file)[0] + '.rou.xml'
    tree.write(options.output_file)
    if options.verbose:
        verbose.writeToConsole(done=True)
    


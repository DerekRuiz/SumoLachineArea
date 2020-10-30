import sys, os
import argparse
import sumolib
import geopandas as gpd
from shapely.geometry import polygon
from xml.etree import ElementTree as ET

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sumoplustools import netHandler
from sumoplustools import verbose

def fillOptions(argParser):
    argParser.add_argument("-n", "--net-file", 
                            metavar="FILE", required=True,
                            help="SUMO network file (mandatory)")
    argParser.add_argument("-s", "--bus-stops", 
                            metavar="FILE", required=True,
                            help="the FILE containing the bus stops data. (mandatory)")
    argParser.add_argument("-o", "--output-file", 
                            metavar="FILE", required=True,
                            help="the FILE output with the bus stops elements (mandatory)")
    argParser.add_argument("-v", "--verbose",
                            action="store_true", default=False,
                            help="gives description of current task")


def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Create additional file with the bus stops from shape-like file")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    if options.verbose:
        verbose.addVerboseSteps(["extracting data from SUMO network file", "extracting data from bus stop shape file", "creating bus stops", "writing bus stops to file"])
        verbose.writeToConsole()
    
    # Initialize data from user
    net = sumolib.net.readNet(options.net_file)
    if options.verbose:
        verbose.writeToConsole(done=True)
    busStop_df = gpd.read_file(options.bus_stops)
    busStop_df.to_crs(epsg=4326, inplace=True)
    if options.verbose:
        verbose.writeToConsole(done=True)
        stopsDone = 0
    root = ET.Element("routes")
    stopLanes = []

    # Get each bus stop point and a SUMO busStop element for each of them
    for _, row in busStop_df.iterrows():
        point = row["geometry"]
        routes_id = row["route_id"]
        lon, lat = point.x, point.y
        stop_x, stop_y = net.convertLonLat2XY(lon, lat)

        # If stop_id != code_id, then stop is a metro station door/exit, it is not a bus stop
        if str(row["stop_id"]) != str(row["stop_code"]):
            continue

        # Get each edge that allows buses near the bus stop
        edges = netHandler.getClosestEdges(net, lon, lat, radius=500, allows="bus", geoCoords=True)
        for edge in edges:
            # Check if lane has a bus stop already and the bus can fit
            if edge and not (edge.getLane(idx=0).getID() in stopLanes) and edge.getLane(idx=0).getLength() > netHandler.sizeOfBus + netHandler.edgeMargin:
                # Add bus stop to the lane
                lane = edge.getLane(idx=0)
                busStopElem = ET.Element("busStop", 
                    {"id": "busStop_%s" % lane.getID(), "lane":lane.getID(), "friendlyPos":"1",
                    "endPos":"%.2f" % -netHandler.edgeMargin, "startPos":"%.2f" % -(netHandler.edgeMargin + (netHandler.sizeOfBus * 2.1))})
                busStopElem.append(ET.Element("param",{"key":"routes_id","value":"%s" % routes_id}))
                busStopElem.append(ET.Element("param",{"key":"position","value":"%f %f" % (stop_x, stop_y)}))
                root.append(busStopElem)
                stopLanes += [lane.getID()]
                if options.verbose:
                    stopsDone += 1
                    verbose.writeToConsole(verboseValue=stopsDone)
                break
    
    # Save tree to a file
    if options.verbose:
        verbose.writeToConsole(done=True)
    tree = ET.ElementTree(root)
    if not options.output_file.endswith('.add.xml'):
        options.output_file = os.path.splitext(options.output_file)[0] + '.add.xml'
    tree.write(options.output_file)
    if options.verbose:
        verbose.writeToConsole(done=True)
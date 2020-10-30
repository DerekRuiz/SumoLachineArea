import os, sys
import argparse
import sumolib
import traci

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sumoplustools import netHandler
from sumoplustools import verbose

_duration = 1.0
_start_pos = -1.0
_end_pos = -1.0

def stopAtEdge(net : sumolib.net.Net, edgeID : str, vehicle_class_type : str):
    noStops = ["dead_end","traffic_light"]
    # yesStops = ["rail_crossings","priority","right_before_left"]
    edge = net.getEdge(edgeID)
    toJunction = edge.getToNode()
    if not edge.allows(vehicle_class_type):
        return False
    if toJunction.getType() in noStops:
        return False
    if edge.getLength() < 5:
        return False
    if not ("residential" in edge.getType() or "unclassified" in edge.getType()):
        return False
    
    return True

def getStopParam() -> (float, float, float):
    """
    Returns the parameters for a stop on an edge.
    Returns a tuple containing (start position, end position, time duration)
    """
    return (_start_pos, _end_pos, _duration)

def fillOptions(argParser):
    argParser.add_argument("-n", "--sumo-network-file", 
                            metavar="FILE", required=True,
                            help="SUMO network FILE (mandatory)")
    argParser.add_argument("-r", "--route-file",
                            metavar="FILE", required=True,
                            help="update routes in FILE (mandatory)")
    argParser.add_argument("-o", "--output-file",
                            metavar="FILE",
                            help="write new route to FILE. Writes to --route-file FILE if unspecified")
    argParser.add_argument("-v", "--vehicle-class",
                            metavar="STR", type=str, default="passenger", 
                            help="adds stops for vehicles of this type")

def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Add stops to the routes/trips of vehicles")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()
    
    if not options.output_file:
        options.output_file = options.route_file
    
    from xml.etree import ElementTree as ET

    routeTree = ET.parse(options.route_file)
    net = sumolib.net.readNet(options.sumo_network_file)

    root = routeTree.getroot()
    for vehicle in root.findall("vehicle"):
        edges = []
        # If multiple routes
        for route in vehicle.findall("route"):
            for edgeID in route.get("edges").split(" "):
                if not edgeID in edges:
                    edges += [edgeID]
        # Ensures no duplicates stops on edges
        for edgeID in edges:
            if stopAtEdge(net, edgeID, options.vehicle_class):
                for lane in net.getEdge(edgeID).getLanes():
                    if lane.allows(options.vehicle_class):
                        stopElem = ET.Element("stop")
                        stopElem.set("lane", lane.getID())
                        stopElem.set("startPos", "%.2f" % _start_pos)
                        stopElem.set("endPos", "%.2f" % _end_pos)
                        stopElem.set("duration", "%.2f" % _duration)
                        stopElem.set("friendlyPos", "1")
                        vehicle.append(stopElem)

    routeTree.write(options.output_file)
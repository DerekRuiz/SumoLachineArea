import sys, os
import argparse
import sumolib
import numpy as np
import geopandas as gpd
from xml.etree import ElementTree as ET
from shapely.geometry import polygon
from shapely import ops 

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sumoplustools import createElement

def fillOptions(argParser):
    argParser.add_argument("-n", "--net-file", 
                            metavar="FILE", required=True,
                            help="SUMO network file (mandatory)")
    argParser.add_argument("-l", "--bus-lines", 
                            metavar="FILE", required=True,
                            help="the FILE containg the bus line data. (mandatory)")
    argParser.add_argument("-s", "--bus-stops", 
                            metavar="FILE", required=True,
                            help="the FILE containg the SUMO bus stop elements. (mandatory)")
    argParser.add_argument("-o", "--output-file", 
                            metavar="FILE", required=True,
                            help="the FILE output with the bus route elements (mandatory)")
    argParser.add_argument("-v", "--verbose",
                            action="store_true", default=False,
                            help="gives description of current task")


def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Create route file with the bus lines from shape-like file")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    if options.verbose:
        createElement.addVerboseSteps(["extracting data from SUMO network file","extracting data from bus line shape file","extracting data from bus stop file","creating bus routes","writing bus routes to file"])
        createElement.writeToConsole()
    
    # Initialize data from user
    net = sumolib.net.readNet(options.net_file)
    netEdges = net.getEdges()
    if options.verbose:
        createElement.writeToConsole(done=True)
    busLines_df = gpd.read_file(options.bus_lines)
    busLines_df.to_crs(epsg=4326, inplace=True)
    if options.verbose:
        createElement.writeToConsole(done=True)
    tree = ET.parse(options.bus_stops)
    stopLanes = {}
    for elem in tree.getroot().findall("busStop"):
        stop_routes = [e.get("value") for e in elem.findall("param") if e.get("key") == "routes_id"][0]
        stop_point = [e.get("value") for e in elem.findall("param") if e.get("key") == "position"][0]
        stopLanes[elem.get("lane")] = {"bus_id":elem.get("id"), "routes_id":stop_routes.split(","), "point": polygon.Point([float(i) for i in stop_point.split(" ")])}
    if options.verbose:
        createElement.writeToConsole(done=True)
        linesDone = 0
    root = ET.Element("routes")


    ## FIND PATH ##
    # For each line segment on the stm line,
    #   Get the edges that are close to, aligned, an same direction
    # Sort the edges by projecting to the stm line
    # For each edge
    #   Add edge to the route, add path if needed
    #   Add bus stop to edge if exists


    # Get each bus line and create a SUMO route element for each of them
    for _, row in busLines_df.iterrows():
        lineID = str(row["shape_id"])
        route_id = str(row["route_id"])
        line = row["geometry"]
        

        # If the headsign starts with STATION, then the line is for metros not a bus
        if str(row["headsign"]).startswith("STATION"):
            continue

        busLine = createElement.convertLine(net, line)
        lons,lats = busLine.xy
        busLine_buffer = busLine.buffer(20)
        busLine_RHS = busLine.buffer(-10, single_sided=True)
        routeEdges = []
        possibleEdges = []

         # Get all edges close to the bus line
        for edge in netEdges:
            edgeLine = polygon.LineString(edge.getShape())
            if edgeLine.distance(busLine) < 5:  # OR edgeLine.within(busLine_buffer): # 
                closest_point = ops.nearest_points(busLine, edgeLine)[0]
                distance = busLine.project(closest_point)
                possibleEdges += [(edge, edgeLine, distance)]

        # Initialize route element with no edges
        routeElem = ET.Element("route", {"id": 'busRoute_%s' % lineID,"edges": ''})
        possibleEdges = sorted(possibleEdges, key=createElement.last)

        prev = None
        for lon, lat in zip(lons,lats):
            if prev:
                prev = np.array([lon, lat])
                continue
            vector = prev - np.array([lon,lat])
            unit_v1 = vector / np.linalg.norm(vector)

            for edge, line, _ in possibleEdges:
                x,y = line.xy
                vector = np.array([x[1],y[1]]) - np.array([x[0],y[0]])
                unit_v2 = vector / np.linalg.norm(vector)

                angle = np.arccos(np.clip(np.dot(unit_v1, unit_v2), -1.0, 1.0))
                if angle < (np.pi / 8) and line:
                    pass

        for edge, _, _ in possibleEdges:
            lane = edge.getLane(idx=0)
            # If lane has a stop, and stop is on this route, and stop is on the right hand side of this street, and edge does not repeat 
            if lane.getID() in stopLanes and route_id in stopLanes[lane.getID()]["routes_id"] and stopLanes[lane.getID()]["point"].within(busLine_RHS) and not edge in routeEdges:
                routeEdges += [edge]
                prevEdge = routeElem.get("edges").strip().split(" ")[-1]
                if prevEdge == '':
                    routeElem.set("edges", '%s %s' % (routeElem.get("edges").strip(), edge.getID()))
                    routeElem.append(ET.Element("stop",{"busStop":stopLanes[lane.getID()]["bus_id"], "duration":"10.00", "friendly":"1","parking":'1'}))
                else:
                    # Create a path between the two stops and add it to the route
                    path, _ = net.getShortestPath(net.getEdge(prevEdge), edge, vClass="bus", includeFromToCost=False)
                    # If path was found
                    if path:
                        edges_id = " ".join([edge.getID() for edge in path[1:]])
                        routeElem.set("edges", '%s %s' % (routeElem.get("edges").strip(), edges_id))
                        routeElem.append(ET.Element("stop",{"busStop":stopLanes[lane.getID()]["bus_id"], "duration":"10.00", "friendly":"1","parking":'1'}))
        
        # Add route element to the tree
        if routeElem.get("edges").strip() != '':
            root.append(routeElem) 
            if options.verbose:
                linesDone += 1
                createElement.writeToConsole(verboseValue=linesDone)




    # Save tree to a file
    if options.verbose:
        createElement.writeToConsole(done=True)
    tree = ET.ElementTree(root)
    if not options.output_file.endswith('.rou.xml'):
        options.output_file = os.path.splitext(options.output_file)[0] + '.rou.xml'
    tree.write(options.output_file)
    if options.verbose:
        createElement.writeToConsole(done=True)
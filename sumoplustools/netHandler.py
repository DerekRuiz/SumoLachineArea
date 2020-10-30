import numpy as np
import sumolib
from shapely.geometry import polygon

sizeOfCar = 5.0
sizeOfBus = 10.0
edgeMargin = 5.0

def last(elem):
    return elem[-1]
def getClosestEdge(net: sumolib.net.Net, x, y, radius=100, allows: str=None, geoCoords=False, noLimit=False) -> sumolib.net.edge.Edge:
    """
    Gets the closest SUMO edge object from the coordinate (lon, lat) within a given radius.
    If no limit is given then it finds the closest edge without limit to radius
    """
    if geoCoords:
        x, y = net.convertLonLat2XY(x, y)
    edges = net.getNeighboringEdges(x, y, radius)
    if len(edges) > 0:
        edgeDist = sorted(edges, key=last)
        for edge, _ in edgeDist:
            if allows:
                if edge.allows(allows):
                    return edge
            else:
                return edge
    if noLimit:
        return getClosestEdge(net, x, y, radius=radius*10, allows=allows, noLimit=noLimit)
    return None

def getClosestEdges(net: sumolib.net.Net, x, y, radius=100, allows: str=None, geoCoords=False):
    """
    Gets the a list of SUMO edge objects within a given radius that are sorted by distance from the coordinate (lon, lat).
    """
    if geoCoords:
        x, y = net.convertLonLat2XY(x, y)
    edgesDist = net.getNeighboringEdges(x, y,radius)
    edgesDist = sorted(edgesDist, key=last)
    return [edge for edge,_ in edgesDist if edge.allows(allows)]

def getClosestLane(net : sumolib.net.Net, x, y, radius=100, allows: str=None, geoCoords=False, noLimit=False):
    """
    Gets the closest SUMO lane object from the coordinate (lon, lat) within a given radius.
    If radius is < 0 then it finds the closest lane without limit to radius
    """
    if geoCoords:
        x, y = net.convertLonLat2XY(x, y)
    lanes = net.getNeighboringLanes(x, y, radius)
    if len(lanes) > 0:
        laneDist= sorted(lanes, key=last)
        for lane, _ in laneDist:
            if allows:
                if lane.allows(allows):
                    return lane
            else:
                return lane
    if noLimit:
        return getClosestLane(net, x, y, radius=radius*10, allows=allows, noLimit=noLimit)
    return None

def getClosestLanes(net: sumolib.net.Net, x, y, radius=100, allows: str=None, geoCoords=False):
    """
    Gets the a list of SUMO lane objects within a given radius that are sorted by distance from the coordinate (lon, lat).
    """
    if geoCoords:
        x, y = net.convertLonLat2XY(x, y)
    lanesDist = net.getNeighboringLanes(x, y, radius)
    lanesDist = sorted(lanesDist, key=last)
    return [lane for lane,_ in lanesDist if lane.allows(allows)]

def convertLine(net: sumolib.net.Net, shape : polygon.LineString) -> polygon.LineString:
    lons, lats = shape.xy
    return polygon.LineString([net.convertLonLat2XY(lon,lat) for lon,lat in zip(lons,lats)])

    
import sys
import numpy as np
import sumolib
from shapely.geometry import polygon

sizeOfCar = 5.0
sizeOfBus = 10.0
edgeMargin = 5.0
verboseSteps = []
verboseStep = 0

def writeToConsole(verboseValue=None, done: bool=False):
    global verboseStep
    try:
        sys.stdout.write("Verbose: %s ... %s%s" % (verboseSteps[verboseStep], (str(verboseValue) if verboseValue else ""), (" Done" if done else "")))
        sys.stdout.flush()
        sys.stdout.write('\r')
        if done:
            sys.stdout.write('\n')
            verboseStep += 1
            if len(verboseSteps) > verboseStep:
                writeToConsole()
    except IndexError:
        pass

def addVerboseSteps(steps : list):
    global verboseSteps
    verboseSteps += steps


def last(elem):
    return elem[-1]
def getClosestEdge(net: sumolib.net.Net, lon, lat, radius=100, allows: str=None) -> sumolib.net.edge.Edge:
    """
    Gets the closest SUMO edge object from the coordinate (lon, lat) within a given radius.
    If radius is < 0 then it finds the closest edge without limit to radius
    """
    
    x, y = net.convertLonLat2XY(lon, lat)
    edges = net.getNeighboringEdges(x, y, (np.inf if radius < 0 else radius))
    if len(edges) > 0:
        edgeDist = sorted(edges, key=last)
        for edge, _ in edgeDist:
            if allows:
                if edge.allows(allows):
                    return edge
            else:
                return edge
    return None

def getClosestEdges(net: sumolib.net.Net, lon, lat, radius=100, allows: str=None):
    """
    Gets the a list of SUMO edge objects within a given radius that are sorted by distance from the coordinate (lon, lat).
    If radius is < 0 then it finds the closest edge without limit to radius
    """
    
    x, y = net.convertLonLat2XY(lon, lat)
    edgesDist = net.getNeighboringEdges(x, y, (np.inf if radius < 0 else radius))
    edgesDist = sorted(edgesDist, key=last)
    return [edge for edge,_ in edgesDist if edge.allows(allows)]

def convertLine(net: sumolib.net.Net, shape : polygon.LineString) -> polygon.LineString:
    lons, lats = shape.xy
    return polygon.LineString([net.convertLonLat2XY(lon,lat) for lon,lat in zip(lons,lats)])

    
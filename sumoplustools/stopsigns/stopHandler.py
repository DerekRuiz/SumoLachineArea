import os
import sumolib
import pandas as pd

_duration = 1.0
_start_pos = -1.0
_end_pos = -1.0
_stop_signs = {}
_file_loc = ""

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
    
    if len(_stop_signs) == 0:
        loadStops()
    
    try:
        _stop_signs[edgeID]
    except KeyError:
        return False

    return True

def loadStops():
    with open(_file_loc) as f:
        f.read()
    _stop_signs

def initStops(net : sumolib.net.Net, stopFile : str):
    pd.read_csv(stopFile)
    _file_loc = os.path.join(os.path.dirname(os.path.abspath(stopFile)),"allStops.txt")

def getStopParam() -> (float, float, float):
    """
    Returns the parameters for a stop on an edge.
    Returns a tuple containing (start position, end position, time duration)
    """
    return (_start_pos, _end_pos, _duration)

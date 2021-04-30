import os, sys
import argparse
import sumolib
from xml.etree import ElementTree as ET

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from sumoplustools import netHandler
from sumoplustools import verbose

def getWattage(level, connector="", network=""):
    watts = {
        1:1000,
        2:7000,
        3:50000,
    }
    return watts.get(level,0)

def addChargerToLane(lane, lv1, lv2, lv3, lon, lat, network, connector):    
    global laneDetails

    if lane in laneDetails:
        laneDetails[lane]["lv1"] += lv1
        laneDetails[lane]["lv2"] += lv2
        laneDetails[lane]["lv3"] += lv3
        laneDetails[lane]["lon"] += lon
        laneDetails[lane]["lat"] += lat
        laneDetails[lane]["network"] += (" %s" % network)
        laneDetails[lane]["connectors"] += (" %s" % connector)
    else:
        laneDetails[lane] = {"lv1":lv1, "lv2":lv2, "lv3":lv3, "lon":lon, "lat":lat, "network":network, "connectors":connector}

def createChargeAddFile(net, output):
    root = ET.Element("additional")
    for lane in laneDetails:
        for lv1Veh in range(laneDetails[lane]["lv1"]):
            chargeElem = ET.Element("chargingStation",{
                "id":"chargingStation_%s_1_%i" % (lane,lv1Veh),
                "lane":lane, "power":"%.2f" % getWattage(level=1), 
                "efficiency":"1.00", "friendlyPos":"1", 
                "startPos":"%.2f" % (lv1Veh * 5.00),
                "endPos":"%.2f" % ((lv1Veh + 1)* 5.00)})
            netElem = ET.Element("param", {"key":"network", "value":laneDetails[lane]["network"]})
            connElem = ET.Element("param", {"key":"connections", "value":laneDetails[lane]["connectors"]})
            chargeElem.append(netElem)
            chargeElem.append(connElem)
            root.append(chargeElem)
        
        for lv2Veh in range(laneDetails[lane]["lv2"]):
            chargeElem = ET.Element("chargingStation",{
                "id":"chargingStation_%s_2_%i" % (lane,lv2Veh),
                "lane":lane, "power":"%.2f" % getWattage(level=2), 
                "efficiency":"1.00", "friendlyPos":"1", 
                "startPos":"%.2f" % ((laneDetails[lane]["lv1"] + lv2Veh) * 5.00),
                "endPos":"%.2f" % ((laneDetails[lane]["lv1"] + lv2Veh + 1)* 5.00)})
            netElem = ET.Element("param", {"key":"network", "value":laneDetails[lane]["network"]})
            connElem = ET.Element("param", {"key":"connections", "value":laneDetails[lane]["connectors"]})
            chargeElem.append(netElem)
            chargeElem.append(connElem)
            root.append(chargeElem)

        for lv3Veh in range(laneDetails[lane]["lv3"]):
            chargeElem = ET.Element("chargingStation",{
                "id":"chargingStation_%s_3_%i" % (lane,lv3Veh),
                "lane":lane, "power":"%.2f" % getWattage(level=3), 
                "efficiency":"1.00", "friendlyPos":"1", 
                "startPos":"%.2f" % ((laneDetails[lane]["lv1"] + laneDetails[lane]["lv2"] + lv3Veh) * 5.00),
                "endPos":"%.2f" % ((laneDetails[lane]["lv1"] + laneDetails[lane]["lv2"] + lv3Veh + 1)* 5.00)})
            netElem = ET.Element("param", {"key":"network", "value":laneDetails[lane]["network"]})
            connElem = ET.Element("param", {"key":"connections", "value":laneDetails[lane]["connectors"]})
            chargeElem.append(netElem)
            chargeElem.append(connElem)
            root.append(chargeElem)
    
    tree = ET.ElementTree(root)
    tree.write(output, encoding="UTF-8", xml_declaration=True)

def fillOptions(argParser):
    argParser.add_argument("-n", "--net-file", 
                            metavar="FILE", type=str, required=True,
                            help="SUMO network file (mandatory)")
    argParser.add_argument("-s", "--charging-stations", 
                            metavar="FILE", type=str, required=True,
                            help="the FILE containing the charging stations data. The file type is a CSV by default (mandatory)")
    argParser.add_argument("-o", "--output-file", 
                            metavar="FILE", type=str, default="chargingStations.add.xml",
                            help="the FILE output with the charging stations elements")
    argParser.add_argument("-j", "--json", 
                            action='store_true', default=False,
                            help="parse charging station file as a JSON")
    argParser.add_argument("-x", "--xml",
                            action='store_true', default=False,
                            help="parse charging station file as an XML")

def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Create additional file with charging station provided from a CSV, JSON, or XML file")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser

if __name__ == "__main__":
    options, argParser = parse_args()

    if options.json and options.xml:
        raise Exception("Cannot parse as JSON and XML simultaneously")

    global laneDetails
    laneDetails = {}
    net = sumolib.net.readNet(options.net_file)

    if options.json:
        import json
        
    elif options.xml:

        tree = ET.parse(options.charging_stations)
        root = tree.getroot()

        stations = root.find("fuel-stations")
        for station in stations.findall("fuel-station"):
            lat = station.find("latitude")
            lon = station.find("longitude")

    else:
        import pandas as pd
        df = pd.read_csv(options.charging_stations)

        for i in range(len(df)):
            try:
                lv1 = int(df.loc[i, "EV Level1 EVSE Num"])
            except ValueError:
                lv1 = 0
            try:
                lv2 = int(df.loc[i, "EV Level2 EVSE Num"])
            except ValueError:
                lv2 = 0
            try:
                lv3 = int(df.loc[i, "EV DC Fast Count"])
            except ValueError:
                lv3 = 0
            lat = float(df.loc[i, "Latitude"])
            lon = float(df.loc[i, "Longitude"])
            network = df.loc[i, "EV Network"]
            connector = df.loc[i, "EV Connector Types"]

            lane = netHandler.getClosestLane(net, lon, lat, 100, geoCoords=True)
            if lane is None:
                continue
            lane = lane.getID()
            addChargerToLane(lane, lv1, lv2, lv3, lon, lat, network, connector)
        
    createChargeAddFile(net, options.output_file)



import os, sys
import sumolib
import traci
import numpy as np
import xml.etree.ElementTree as ET

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sumoplustools.stopsigns import addStops 

class RerouteChargingDomain():
    def __init__(self, sumocfgFile, connection : traci.Connection):
        self.sumocfgFile = sumocfgFile
        self.net = self.getNetworkFile()
        self.additionalFiles = self.getAdditionalFiles()
        self.chargingElems = self.getChargingStationElems()
        self.connection = connection
        self._vehiclesRerouted = {}

    def getNetworkFile(self) -> str:
        """
        Returns the network file name\n
        Throws an exception if could not locate it in the SUMO configuration file
        """
        tree = ET.parse(self.sumocfgFile)
        root = tree.getroot()
        inputElem = root.find("input")
        netElem = inputElem.find("sumo-net-file")
        if netElem is None:
            raise Exception('Could not retrieve SUMO network file from SUMO configuration file located at "%s"' % os.path.abspath(self.sumocfgFile))
        return netElem.get("value")

    def getAdditionalFiles(self) -> list:
        """Returns the names of the additional files in the form of a list"""
        tree = ET.parse(self.sumocfgFile)
        root = tree.getroot()
        inputElem = root.find("input")
        addElem = inputElem.find("additional-files")
        if addElem is None:
            return []
        return addElem.get("value").split(",")

    def getChargingStationElems(self) -> list:
        """
        Returns the charging stations from the additional files in the form of a list\n
        Raises an exception if no charging stations are located
        """
        chargingStationElems = []
        for f in self.additionalFiles:
            tree = ET.parse(f)
            root = tree.getroot()
            chargingStationElems += root.findall("chargingStation")
        if len(chargingStationElems) <= 0:
            raise Exception("No charging stations in simulation. Cannot reroute vehicles")
        return chargingStationElems


    def getChargingStationIDs(self):
        return [elem.get("id") for elem in self.chargingElems]

    def getChargingStationLanes(self):
        return [(elem.get("id"), elem.get("lane")) for elem in self.chargingElems]
    
    def addStopsToVehicle(self, vehID):
        startPos, endPos, duration  = addStops.getStopParam()
        routeID = self.connection.vehicle.getRouteID(vehID)

        for edgeID in self.connection.route.getEdges(routeID):
            if addStops.stopAtEdge(self.net, edgeID):
                self.connection.vehicle.setStop(vehID, edgeID, pos=endPos, duration=duration, startPos=startPos)

    def rerouteVehicles(self, startRerouteThreshold=20, finishRerouteThreshold=80, randomThreshold=True):
        """
        Reroutes vehicles low on battery to the closest charging station.
        """
        startRerouteThreshold = 20 / 100
        finishRerouteThreshold = finishRerouteThreshold / 100
        generator = np.random.default_rng()
        for vehicleID in self.connection.vehicle.getIDList():
            hasBattery = (self.connection.vehicle.getParameter(vehicleID, "has.battery.device") == "true")
            if not hasBattery:
                continue

            charging = self.connection.vehicle.getParameter(vehicleID, "device.battery.chargingStationId")
            battery = self.connection.vehicle.getParameter(vehicleID, "device.battery.actualBatteryCapacity")
            batteryTotal = self.connection.vehicle.getParameter(vehicleID, "device.battery.maximumBatteryCapacity")
            if randomThreshold:
                finishRerouteThreshold = finishRerouteThreshold + ((1 - finishRerouteThreshold) * generator.random())

            # Check if vehicle is low on battery, and not at or going to charging station 
            if (float(battery) <= float(batteryTotal) * startRerouteThreshold) and (charging == "NULL") and (vehicleID not in self._vehiclesRerouted):
                shortestTime = np.inf
                closestChargingStation = None
                # Loop for each charging station in the network
                for (chargingStationID, chargingStationLaneID) in self.getChargingStationLanes():
                    # Check if another vehicle is on route to the charging station
                    if chargingStationID in self._vehiclesRerouted[vehicleID].values:
                        continue
                    chargeEdgeID = self.connection.lane.getEdgeID(chargingStationLaneID)
                    travelTime = self.connection.vehicle.getParameter(vehicleID,"device.rerouting.edge:%s" % chargeEdgeID)
                    # Get closest charging station by travel time
                    if float(travelTime) < shortestTime:
                        shortestTime = float(travelTime)
                        closestChargingStation = chargingStationID
                        closestEdge = chargeEdgeID
                # If no charging stations available, do not reroute to charge
                if closestChargingStation is None:
                    continue

                initRouteID = self.connection.vehicle.getRouteID(vehicleID)
                initLastEdgeID = self.connection.route.getEdges(initRouteID)[-1]
                self._vehiclesRerouted[vehicleID] = {"lastEdgeID":initLastEdgeID, "chargingStation":closestChargingStation}

                self.connection.vehicle.changeTarget(vehicleID, closestEdge)
                self.addStopsToVehicle(vehicleID)
                self.connection.vehicle.setChargingStationStop(vehicleID, closestChargingStation, duration=5)

            # check if vehicle is at charging station and is done charging
            elif (float(battery) >= float(batteryTotal) * finishRerouteThreshold) and (charging != "NULL") and (vehicleID in self._vehiclesRerouted):
                self.connection.vehicle.changeTarget(vehicleID, self._vehiclesRerouted[vehicleID]["lastEdgeID"])
                self.addStopsToVehicle(vehicleID)
                self._vehiclesRerouted.pop(vehicleID)
            # Check if vehicle is at charging station and is not done charging
            elif (float(battery) < float(batteryTotal) * finishRerouteThreshold) and (charging != "NULL") and (vehicleID in self._vehiclesRerouted):
                self.connection.vehicle.setChargingStationStop(vehicleID, charging, duration=5)



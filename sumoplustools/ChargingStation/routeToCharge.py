import sumolib
import traci
import numpy as np
import xml.etree.ElementTree as ET

class rerouteChargingDomain():
    def __init__(self, sumocfgFile, connection : traci.Connection):
        self.sumocfgFile = sumocfgFile
        self.additionalFiles = self.getAdditionalFiles()
        self.chargingElems = self.getChargingStationElems()
        self.connection = connection
        self._vehiclesRerouted = {}

    def getAdditionalFiles(self):
        tree = ET.parse(self.sumocfgFile)
        root = tree.getroot()
        inputElem = root.find("input")
        addElem = inputElem.find("additional-files")
        if addElem is None:
            return []
        return addElem.get("value").split(",")

    def getChargingStationElems(self):
        chargingStationElems = []
        for f in self.additionalFiles:
            tree = ET.parse(f)
            root = tree.getroot()
            chargingStationElems += root.findall("chargingStation")
        if len(chargingStationElems) <= 0:
            raise Exception("No charging stations in simulation. Cannot charge vehicles")
        return chargingStationElems


    def getChargingStationIDs(self):
        return [elem.get("id") for elem in self.chargingElems]

    def getChargingStationLanes(self):
        return [(elem.get("id"), elem.get("lane")) for elem in self.chargingElems]


    def rerouteVehicles(self):
        """
        Reroutes vehicles low on battery to the closest charging station.
        """

        for vehicleID in self.connection.vehicle.getIDList():
            hasBattery = (self.connection.vehicle.getParameter(vehicleID, "has.battery.device") == "true")
            if not hasBattery:
                continue

            charging = self.connection.vehicle.getParameter(vehicleID, "device.battery.chargingStationId")
            battery = self.connection.vehicle.getParameter(vehicleID, "device.battery.actualBatteryCapacity")
            batteryTotal = self.connection.vehicle.getParameter(vehicleID, "device.battery.maximumBatteryCapacity")

            if charging != "NULL":
                print(vehicleID, battery)
                
            # Check if vehicle is low on battery, and not at or going to charging station 
            if (float(battery) <= float(batteryTotal) * 0.2) and (charging == "NULL") and (vehicleID not in self._vehiclesRerouted):
                print("low Battery for: ", vehicleID)
                initRouteID = self.connection.vehicle.getRouteID(vehicleID)
                initLastEdgeID = self.connection.route.getEdges(initRouteID)[-1]
                self._vehiclesRerouted[vehicleID] = {"lastEdgeID":initLastEdgeID}
                
                shortestTime = np.inf
                for (chargingStationID, chargingStationLaneID) in self.getChargingStationLanes():
                    chargeEdgeID = self.connection.lane.getEdgeID(chargingStationLaneID)
                    travelTime = self.connection.vehicle.getParameter(vehicleID,"device.rerouting.edge:%s" % chargeEdgeID)
                    print(chargeEdgeID, travelTime)
                    if float(travelTime) < shortestTime:
                        shortestTime = float(travelTime)
                        closestChargingStation = chargingStationID
                        closestEdge = chargeEdgeID
                print(closestChargingStation, closestEdge)
                self.connection.vehicle.changeTarget(vehicleID, closestEdge)
                self.connection.vehicle.setChargingStationStop(vehicleID, closestChargingStation, duration=100)
            # check if vehicle is at charging station and is done charging
            elif (float(battery) >= float(batteryTotal) * 0.8) and (charging != "NULL") and (vehicleID in self._vehiclesRerouted):
                print(vehicleID, "route back")
                self.connection.vehicle.changeTarget(vehicleID, self._vehiclesRerouted[vehicleID]["lastEdgeID"])
                self._vehiclesRerouted.pop(vehicleID)
            # Check if vehicle is at charging station and is not done charging
            elif (float(battery) < float(batteryTotal) * 0.8) and (charging != "NULL") and (vehicleID in self._vehiclesRerouted) and (self.connection.vehicle.getStopState(vehicleID) == 65):
                self.connection.vehicle.setChargingStationStop(vehicleID, charging, duration=50)



import os, sys
import numpy as np
import traci
import xml.etree.ElementTree as ET

class RerouteChargingDomain():
    def __init__(self, sumocfgFile, connection : traci.Connection, netFile=None, addFiles=None):
        self.sumocfgFile = sumocfgFile
        if netFile:
            self.net = netFile
        else:
            self.net = self.getNetworkFile()
        if addFiles:
            self.additionalFiles = addFiles
        else:
            self.additionalFiles = self.getAdditionalFiles()
        self.connection = connection
        self.parkingElems = self.getParkingAreaElems()
        
    
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


    def getParkingAreaElems(self) -> list:
        """
        Returns the charging stations from the additional files in the form of a list\n
        Raises an exception if no charging stations are located
        """
        parkingAreaElems = []
        for f in self.additionalFiles:
            tree = ET.parse(f)
            root = tree.getroot()
            parkingAreaElems += root.findall("parkingArea")
        if len(parkingAreaElems) <= 0:
            raise Exception("No parking areas in simulation. Cannot reroute vehicles")
        return parkingAreaElems


    def getParkingAreaIDs(self) -> list:
        return [elem.get("id") for elem in self.parkingElems]

    def getParkingAreaLanes(self) -> [(str, str)]:
        return [(elem.get("id"), elem.get("lane")) for elem in self.parkingElems]
    
    def getClosestParkingArea(self, edgeID) -> (str,str):
        """
        Returns the closest parking area and its edge from the given edge
        """
        closestdistance = np.inf
        closestParkingArea = closestEdge = None
        # Loop for each charging station in the network
        for parkingAreaID, parkingAreaLaneID in self.getParkingAreaLanes():
            # Check if parking area is full
            if self.connection.simulation.getParameter(parkingAreaID, 'parkingArea.occupancy') == self.connection.simulation.getParameter(parkingAreaID, "parkingArea.capacity"):
                # Go to next parking area
                continue

            parkingEdgeID = self.connection.lane.getEdgeID(parkingAreaLaneID)
            distance = self.connection.simulation.getDistanceRoad(edgeID1=edgeID, pos1=0, edgeID2=parkingEdgeID, pos2=0, isDriving=True)
            # Get closest parking area by disstance
            if float(distance) < closestdistance:
                closestdistance = float(distance)
                closestParkingArea = parkingAreaID
                closestEdge = parkingEdgeID
        return closestParkingArea, closestEdge

    def rerouteVehicles(self):
        # Loop for each vehicle in the simulation
        for vehicleID in self.connection.vehicle.getIDList():
            # Check if vehicle has a stop with the flag of parking area or charging station
            hasStop = False
            for stops in traci.vehicle.getNextStops(vehicleID):
                _, _, _, flag, _, _ = stops
                if np.math.floor(np.math.log2(flag)) in [6,7]:
                    hasStop = True
                    break
            if hasStop:
                continue
            
            closestParkingAreaID, _ = self.getClosestParkingArea(self.connection.vehicle.getRoute(vehicleID)[-1])
            traci.vehicle.rerouteParkingArea(vehicleID, closestParkingAreaID)

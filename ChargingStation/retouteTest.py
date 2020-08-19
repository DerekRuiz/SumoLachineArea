import sumolib
import sys
import traci
import numpy as np
import xml.etree.ElementTree as ET


def getAdditionalFiles():
    global addFiles
    if not "addFiles" in globals():
        tree = ET.parse(sumocfgFile)
        root = tree.getroot()
        inputElem = root.find("input")
        addElem = inputElem.find("additional-files")
        if addElem is None:
            return []
        addFiles = addElem.get("value").split(",")
    return addFiles

def getChargingStationElems():
    global chargingStationElems
    if not "chargingStationElems" in globals():
        chargingStationElems = []
        files = getAdditionalFiles()
        for f in files:
            tree = ET.parse(f)
            root = tree.getroot()
            chargingStationElems += root.findall("chargingStation")
    
    if len(chargingStationElems) <= 0:
        raise Exception("No charging stations in simulation. Cannot charge")
    return chargingStationElems


def getChargingStationIDs():
    return [elem.get("id") for elem in getChargingStationElems()]

def getChargingStationLanes():
    return [(elem.get("id"), elem.get("lane")) for elem in getChargingStationElems()]


def updateAllElecVehicleChargingRoutes():
    for vehicleID in traci.vehicle.getIDList():
        hasBattery = (traci.vehicle.getParameter(vehicleID, "has.battery.device") == "true")
        if not hasBattery:
            continue

        charging = traci.vehicle.getParameter(vehicleID, "device.battery.chargingStationId")
        battery = traci.vehicle.getParameter(vehicleID, "device.battery.actualBatteryCapacity")
        batteryTotal = traci.vehicle.getParameter(vehicleID, "device.battery.maximumBatteryCapacity")

        if charging != "NULL":
            print(vehicleID, battery)
        # Check if vehicle is low on battery, and not at nor going to charging station 
        if (float(battery) <= float(batteryTotal) * 0.2) and (charging == "NULL") and (vehicleID not in vehiclesOnRoute):
            print("low Battery for: ", vehicleID)
            initRouteID = traci.vehicle.getRouteID(vehicleID)
            initLastEdgeID = traci.route.getEdges(initRouteID)[-1]
            vehiclesOnRoute[vehicleID] = {"lastEdgeID":initLastEdgeID}
            
            shortestTime = np.inf
            for (chargingStationID, chargingStationLaneID) in getChargingStationLanes():
                chargeEdgeID = traci.lane.getEdgeID(chargingStationLaneID)
                travelTime = traci.vehicle.getParameter(vehicleID,"device.rerouting.edge:%s" % chargeEdgeID)
                print(chargeEdgeID, travelTime)
                if float(travelTime) < shortestTime:
                    shortestTime = float(travelTime)
                    closestChargingStation = chargingStationID
                    closestEdge = chargeEdgeID
            print(closestChargingStation, closestEdge)
            traci.vehicle.changeTarget(vehicleID, closestEdge)
            traci.vehicle.setChargingStationStop(vehicleID, closestChargingStation, duration=100)
        # check if vehicle is at charging station and is done charging
        elif (float(battery) >= float(batteryTotal) * 0.8) and (charging != "NULL") and (vehicleID in vehiclesOnRoute):
            print(vehicleID, "route back")
            traci.vehicle.changeTarget(vehicleID, vehiclesOnRoute[vehicleID]["lastEdgeID"])
            vehiclesOnRoute.pop(vehicleID)
        # Check if vehicle is at charging station and is not done charging
        elif (float(battery) < float(batteryTotal) * 0.8) and (charging != "NULL") and (vehicleID in vehiclesOnRoute) and (traci.vehicle.getStopState(vehicleID) == 65):
            traci.vehicle.setChargingStationStop(vehicleID, charging, duration=50)

if __name__ == "__main__":
    
    sumoBinary = sumolib.checkBinary('sumo-gui')
    sumocfgFile = "C:\\Users\\epicb\\Documents\\GitHub\\SumoLachineArea\\ChargingStation/test.sumocfg"
    sumoCmd = [sumoBinary, "-c", sumocfgFile] #, "--start", "1"

    try:
        traci.getConnection()
    except traci.TraCIException:
        traci.start(sumoCmd)

    vehiclesOnRoute = {}

    while traci.simulation.getMinExpectedNumber() > 0:
        print("current time: ",traci.simulation.getTime())
        
        updateAllElecVehicleChargingRoutes()
        
        traci.simulationStep()

    try:
        print("done")
        traci.close()
    except:
        pass

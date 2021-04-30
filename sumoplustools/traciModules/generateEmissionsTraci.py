import os, sys
import traci
import sumolib

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from sumoplustools.emissions.generateEmissions import EmissionGenerator
from sumoplustools import netHandler

class TraciEmissions(EmissionGenerator):
    def __init__(self, net : sumolib.net.Net):
        EmissionGenerator.__init__(self, net)
        self._lastSave = None

    def resetLastSave(self):
        self._lastSave = None
    
    def verifyEmissionCollection(self, fromStep, toStep, timeInterval, eTypes, connection: traci.Connection) -> bool:
        '''
        Pre condition to verify if vehicle emissions should be collected for the current time.\n
        Saves the vehicles emissions if appropriate to the current time.\n
        Returns True if the emissions should be collected for the current time, False otherwise.
        
        Parameters
        ----------
        fromStep : float
            Initial step to collect emission data

        toStep : float
            Time step that collecting emission data will stop at

        timeInterval : float
            Amount of time elapsed when the emission data will be combined.
            Can be considered the amount of time resolution when saving the emissions. Measured in seconds

        eTypes : List
            List of strings containing the emission types that will be collected

        connection : traci.Connection
            Socket connection to the TraCI server
        '''
        if connection.simulation.getTime() < fromStep or connection.simulation.getTime() > toStep:
            return False

        if self._lastSave is None or self._lastSave > connection.simulation.getTime():
            self._lastSave = fromStep

        # Save before collecting this time's emissions to get range of [lastTime, thisTime[
        # Save if not the first step since lastTime < first step -> do not want to save lastTime
        # Save if current time is on the interval to save
        if connection.simulation.getTime() != fromStep and (connection.simulation.getTime() - fromStep) % timeInterval == 0:
            self.saveToSQL(self._lastSave)
            self._lastSave = connection.simulation.getTime()

        return True

    def collectVehicleEmissions(self, vehID, connection: traci.Connection):
        '''
        Collects the emission data of the vehicle at the current time.
        '''
        if connection.vehicle.getFuelConsumption(vehID) > 0.00:
            fuel_output = connection.vehicle.getFuelConsumption(vehID) * connection.simulation.getDeltaT()
            CO2_output = connection.vehicle.getCO2Emission(vehID) * connection.simulation.getDeltaT()
            CO_output = connection.vehicle.getCOEmission(vehID) * connection.simulation.getDeltaT()
            HC_output = connection.vehicle.getHCEmission(vehID) * connection.simulation.getDeltaT()
            NOx_output = connection.vehicle.getNOxEmission(vehID) * connection.simulation.getDeltaT()
            PMx_output = connection.vehicle.getPMxEmission(vehID) * connection.simulation.getDeltaT()
            emission_output = {'Fuel':fuel_output, 'CO2':CO2_output, 'CO':CO_output, 'HC':HC_output, 'NOx':NOx_output, 'PMx':PMx_output}

            edgeID = connection.vehicle.getRoadID(vehID)
            if edgeID[0] == ":":
                # Vehicle is on a junction
                x, y = connection.vehicle.getPosition(vehID)
                edgeID = netHandler.getClosestEdge(self.net, x, y, noLimit=True).getID()

            self.addOutputs(vehID, edgeID, emission_output)

    def collectEmissions(self, fromStep, toStep, timeInterval, eTypes, connection: traci.Connection):
        """
        Collects the emission data of the current time step.\n
        Only if the current time step falls within fromStep and toStep (not included) is the emission data collected.

        If the simulation starts at a time after fromStep, then data will only be collected from the initial simulation time.\n
        If the simulation ends at a time before toStep, then the data will only be collected up to the final simulation time, imitating if the toStep = final time
        
        Parameters
        ----------
        fromStep : float
            Initial step to collect emission data

        toStep : float
            Time step that collecting emission data will stop at

        timeInterval : float
            Amount of time elapsed when the emission data will be combined.
            Can be considered the amount of time resolution when saving the emissions. Measured in seconds

        eTypes : List
            List of strings containing the emission types that will be collected

        connection : traci.Connection
            Socket connection to the TraCI server
        """
        if not self.verifyEmissionCollection(fromStep, toStep, timeInterval, eTypes, connection):
            return

        # Loops for each vehicle in the network
        for vehID in connection.vehicle.getIDList():
            self.collectVehicleEmissions(vehID, connection)

    def close(self):
        if not self._sql_buffer.empty:
            self.saveToSQL(self._lastSave, force=True)
        super().close()
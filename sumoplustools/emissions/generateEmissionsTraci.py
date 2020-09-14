import os, sys
import traci
import sumolib
import geopandas as gpd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sumoplustools.emissions.generateEmissions import EmissionGenerator

class TraciEmissions(EmissionGenerator):
    def __init__(self, connection : traci.Connection):
        self.connection = connection
        self.stepLength = connection.simulation.getDeltaT()
        self._lastSave = None

    def collectEmissions(self, fromStep, toStep, timeInterval, eTypes):
        """
        Collects the emission data of the current time step, saving it as numpy arrays to a temporary folder.\n
        Only if the current time step falls within fromStep and toStep (not included) is the emission data collected.

        If the file starts at a time after fromStep, then data will only be collected from the initial file time.\n
        If the file ends at a time before toStep, then the data will only be collected up to the final file time, imitating if the toStep = final time + stepLength
        
        Parameters
        ----------
        fromStep : float
            Initial step to collect emission data

        toStep : float
            Time step that collecting emission data will stop at

        timeInterval : float
            Amount of time elapsed when the emission data will be combined. Measured in seconds

        eTypes : List
            List of strings containing the emission types that will be collected.
        """
        def getSecond(arr):
            return arr[1]
        if self._lastSave is None:
            self._lastSave = fromStep - self.stepLength

        # Check if current time is greater than initial step and less than final step, as well as if vehicles are still in the simulation 
        if self.connection.simulation.getTime() >= fromStep and self.connection.simulation.getTime() < toStep and self.connection.simulation.getMinExpectedNumber() != 0:

            calculated_edges = []

            # Loops for each vehicle in the network
            for vehID in self.connection.vehicle.getIDList():
                if self.connection.vehicle.getFuelConsumption(vehID) > 0.00:
                    edgeID = self.connection.lane.getEdgeID(self.connection.vehicle.getLaneID(vehID))
                    
                    if not edgeID in calculated_edges:
                        fuel_output = self.connection.edge.getFuelConsumption(edgeID) * self.stepLength
                        CO2_output = self.connection.edge.getCO2Emission(edgeID) * self.stepLength
                        CO_output = self.connection.edge.getCOEmission(edgeID) * self.stepLength
                        HC_output = self.connection.edge.getHCEmission(edgeID) * self.stepLength
                        NOx_output = self.connection.edge.getNOxEmission(edgeID) * self.stepLength
                        PMx_output = self.connection.edge.getPMxEmission(edgeID) * self.stepLength
                        emission_output = {'Fuel':fuel_output, 'CO2':CO2_output, 'CO':CO_output, 'HC':HC_output, 'NOx':NOx_output, 'PMx':PMx_output}

                        calculated_edges.append(edgeID)

                        if edgeID[0] == ":":
                            # vehicle is on a junction
                            x, y = self.connection.vehicle.getPosition(vehID)
                            edges = []
                            radius = 10
                            while len(edges) == 0:
                                edges = self.net.getNeighboringEdges(x, y, radius)
                                radius *= 10
                            
                            closestEdge, _ = sorted(edges, key=getSecond)[0]
                            edgeID = closestEdge.getID()

                        self.addOutputs(self.net, edgeID, emission_output)            

        if self.connection.simulation.getTime() - self._lastSave >= timeInterval:
            self.saveEmissionArray(eTypes, float(self._lastSave) + self.stepLength)
            self.resetEmissionArrays(self.net)
            self._lastSave = self.connection.simulation.getTime()
    

    def saveEmissions(self, fromStep, toStep, timeInterval, filename, eTypes, template):
        self.saveDataFrame(fromStep, toStep, timeInterval, filename, eTypes, template)
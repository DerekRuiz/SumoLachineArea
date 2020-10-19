import os, sys
import numpy as np
import traci
import sumolib

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sumoplustools.emissions.generateEmissions import EmissionGenerator

class TraciEmissions(EmissionGenerator):
    def __init__(self, net : sumolib.net.Net):
        EmissionGenerator.__init__(self, net)
        self._lastSave = None

    def resetLastSave(self):
        self._lastSave = None

    def collectEmissions(self, fromStep, toStep, timeInterval, eTypes, connection : traci.Connection, saveRealTime=False):
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
        if connection.simulation.getTime() < fromStep or connection.simulation.getTime() > toStep:
            return 

        def getSecond(arr):
            return arr[1]
        if self._lastSave is None or self._lastSave > connection.simulation.getTime():
            self._lastSave = fromStep

        # Save if current time is on the interval to save, only if time interval is not infinity, otherwise save if no vehicles in simulation
        if connection.simulation.getTime() != fromStep and ((connection.simulation.getTime() - fromStep) % timeInterval == 0 if not timeInterval == np.inf else connection.simulation.getMinExpectedNumber() == 0):
            if saveRealTime:
                self.saveRealTime(float(self._lastSave), toStep, timeInterval, eTypes)
            self.saveEmissionArray(eTypes, float(self._lastSave))
            self.resetEmissionArrays()
            self._lastSave = connection.simulation.getTime()

        # Check if current time is greater than initial step and less than final step, as well as if vehicles are still in the simulation 
        if connection.simulation.getMinExpectedNumber() != 0:

            calculated_edges = []

            # Loops for each vehicle in the network
            for vehID in connection.vehicle.getIDList():
                if connection.vehicle.getFuelConsumption(vehID) > 0.00:
                    edgeID = connection.vehicle.getRoadID(vehID)
                    #edgeID = connection.lane.getEdgeID(connection.vehicle.getLaneID(vehID))
                    
                    if not edgeID in calculated_edges:
                        fuel_output = connection.edge.getFuelConsumption(edgeID) * connection.simulation.getDeltaT()
                        CO2_output = connection.edge.getCO2Emission(edgeID) * connection.simulation.getDeltaT()
                        CO_output = connection.edge.getCOEmission(edgeID) * connection.simulation.getDeltaT()
                        HC_output = connection.edge.getHCEmission(edgeID) * connection.simulation.getDeltaT()
                        NOx_output = connection.edge.getNOxEmission(edgeID) * connection.simulation.getDeltaT()
                        PMx_output = connection.edge.getPMxEmission(edgeID) * connection.simulation.getDeltaT()
                        emission_output = {'Fuel':fuel_output, 'CO2':CO2_output, 'CO':CO_output, 'HC':HC_output, 'NOx':NOx_output, 'PMx':PMx_output}

                        calculated_edges.append(edgeID)

                        if edgeID[0] == ":":
                            # vehicle is on a junction
                            x, y = connection.vehicle.getPosition(vehID)
                            edges = []
                            radius = 10
                            while len(edges) == 0:
                                edges = self.net.getNeighboringEdges(x, y, radius)
                                radius *= 10
                            
                            closestEdge, _ = sorted(edges, key=getSecond)[0]
                            edgeID = closestEdge.getID()

                        self.addOutputs(edgeID, emission_output)

    
    def saveRealTime(self, time, toStep, timeInterval, eTypes):
        for eType in eTypes:
            hr = time // 3600
            mins = (time % 3600) // 60
            sec = (time % 3600) % 60
            fromTime = "%i:%.2i:%.2f" % (hr,mins,sec)
            
            time += timeInterval
            if time > toStep:
                time = toStep
            
            hr = time // 3600
            mins = (time % 3600) // 60
            sec = (time % 3600) % 60
            toTime = "%i:%.2i:%.2f" % (hr,mins,sec)

            # Do not save time steps of length 0
            if fromTime == toTime:
                return
            
            # Adds step to table/dataframe
            stepArr = self.emission_array[self.mapEtypeToIndex(eType)]
            self.sqlConnection.addColumn('%s-%s' % (fromTime, toTime), stepArr, eType)

    def saveDataFrame(self, fromStep, toStep, timeInterval, eTypes, filename=None, toSQL=True):
        super.saveDataFrame(fromStep, toStep, timeInterval, eTypes, filename, toSQL)
        self.resetLastSave()
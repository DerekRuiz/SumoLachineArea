import os, sys
import numpy as np
from datetime import timedelta
import traci
import sumolib
import geopandas as gpd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sumoplustools.postgresql.psqlObjects import VisualConnection
from sumoplustools import netHandler

class TraciVisuals():
    def __init__(self, net: sumolib.net.Net):
        self.sqlConnection = VisualConnection()
        self.net = net
        self.mapNetToDF = self.sqlConnection.getNetToDFMap()

        self._sql_buffer = gpd.pd.DataFrame(columns=self.sqlConnection.columns)
        self._lastSave = None

    def _resetSQLBuffer(self):
        self._sql_buffer = self._sql_buffer.iloc[0:0]

    def resetLastSave(self):
        self._lastSave = None

    def addOutputs(self, time: float, veh_id, visual_output):
        """
        Accumulates the outputs of the visuals per vehicle per time.
        
        Parameters
        ----------
        time : float
            Time stamp of ouputs gathered

        veh_id : str
            Vehicle producing emissions

        visual_output : dict
            Names of outputs associated with their numerical value
        """
        time = self.sqlConnection.initalDate + timedelta(seconds=time)
        self._sql_buffer = self._sql_buffer.append({self.sqlConnection.columns[0]:time, self.sqlConnection.columns[1]:veh_id, **visual_output}, ignore_index=True)
        

    def saveToSQL(self, force=False):
        '''
        Saves the outputs gathered to the SQL server.

        Parameters
        ----------
        force : bool
            Whether to force the save and ignore if full
        '''
        if self._sql_buffer.shape[0] / (10**3) >= 10 or force: # self._sql_buffer.memory_usage(deep=True).sum() / (10**6) >= 5 self._sql_buffer.shape[0] / (10**3) >= 40
            #self.sqlConnection.insertDataFrame(self._sql_buffer, self.sqlConnection.vehTable)
            self._resetSQLBuffer()
    
    def clearSQLVisuals(self):
        self.sqlConnection.clearVehicleTable()

    def saveToDataFrame(self, veh_id, filename, fromTime=None, toTime=None) -> gpd.pd.DataFrame:
        df = self.sqlConnection.getVehDF(veh_id, fromTime, toTime)
        df.to_csv(filename)
        return df
    
    def verifyVisualCollection(self, fromStep, toStep, connection : traci.Connection) -> bool:
        '''
        Pre condition to verify if vehicle visualization should be collected for the current time.\n
        Saves the vehicles visualization if appropriate to the current time.\n
        Returns True if the visualization should be collected for the current time, False otherwise.
        
        Parameters
        ----------
        fromStep : float
            Initial step to collect visual data

        toStep : float
            Time step that collecting visual data will stop at

        connection : traci.Connection
            Socket connection to the TraCI server
        '''
        if connection.simulation.getTime() < fromStep or connection.simulation.getTime() > toStep:
            return False

        if self._lastSave is None or self._lastSave > connection.simulation.getTime():
            self._lastSave = fromStep

        # Save before collecting this time's emissions to get range of [lastTime, thisTime[
        # Save if not the first step since lastTime < first step -> do not want to save lastTime
        if connection.simulation.getTime() != fromStep:
            self.saveToSQL(self._lastSave)
            self._lastSave = connection.simulation.getTime()

        return True

    def collectVehicleVisuals(self, vehID, connection : traci.Connection):
        '''
        Collects the visualization data of the vehicle at the current time.
        '''
        cols = self.sqlConnection.columns

        x, y = connection.vehicle.getPosition(vehID)
        lon, lat = self.net.convertXY2LonLat(x,y)
        speed = connection.vehicle.getSpeed(vehID)
        direction = connection.vehicle.getSlope(vehID)
        vtype = connection.vehicle.getTypeID(vehID)
        vclass = connection.vehicle.getVehicleClass(vehID)
        
        edgeID = connection.vehicle.getRoadID(vehID)
        if edgeID[0] == ":":
            # Vehicle is on a junction
            edgeID = netHandler.getClosestEdge(self.net, x, y, noLimit=True).getID()

        visual_output = {cols[2]:self.mapNetToDF[edgeID], cols[3]:lon, cols[4]:lat, cols[5]:speed, cols[6]:direction, cols[7]:vtype, cols[8]:vclass}
        self.addOutputs(connection.simulation.getTime(), vehID, visual_output)

    def collectVisuals(self, fromStep, toStep, timeInterval, eTypes, connection : traci.Connection):
        """
        Collects the visualization data of the current time step.\n
        Only if the current time step falls within fromStep and toStep (not included) is the visualization data collected.

        If the simulation starts at a time after fromStep, then data will only be collected from the initial simulation time.\n
        If the simulation ends at a time before toStep, then the data will only be collected up to the final simulation time, imitating if the toStep = final time
        
        Parameters
        ----------
        fromStep : float
            Initial step to collect visual data

        toStep : float
            Time step that collecting visual data will stop at

        timeInterval : float
            Amount of time elapsed when the visual data will be combined.
            Can be considered the amount of time resolution when saving the visuals. Measured in seconds

        eTypes : List
            List of strings containing the visual types that will be collected

        connection : traci.Connection
            Socket connection to the TraCI server
        """
        if not self.verifyVisualCollection(fromStep, toStep, connection):
            return

        # Loops for each vehicle in the network
        for vehID in connection.vehicle.getIDList():
            self.collectVehicleVisuals(vehID, connection)

    def close(self):
        if not self._sql_buffer.empty:
            self.saveToSQL(force=True)
        self.sqlConnection.close()

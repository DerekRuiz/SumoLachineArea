import psycopg2, psycopg2.extras
from datetime import datetime, timedelta
import geopandas as gpd

class SQLConnection():
    def __init__(self):
        self.conn = psycopg2.connect(database="SUMO Montreal", user="postgres", password="sumogroup4", host="127.0.0.1", port="5432")
        self.cursor = self.conn.cursor()
        self.initalDate = datetime.fromisoformat("2000-01-01")
        self.referenceTable = "GeoCoordinates"
        self.net2DFTable = "NetToDF"
    
    def execute(self, query):
        try:
            self.cursor.execute(query)
        except Exception:
            self.conn.rollback()
            raise
        self.conn.commit()

    def execute_values(self, query, tuples: tuple):
        try:
            psycopg2.extras.execute_values(self.cursor, query, tuples)
        except Exception:
            self.conn.rollback()
            raise
        self.conn.commit()
    
    def insertDataFrame(self, dataframe, tableName):
        if not dataframe.empty:
            tuples = [tuple(x) for x in dataframe.to_numpy()]
            temp_cols = '","'.join(list(dataframe.columns))
            command  = '''INSERT INTO public."%s"("%s") VALUES %%s''' % (tableName, temp_cols)
            self.execute_values(command, tuples)
    
    def retrieveSelectedQuery(self) -> list:
        return self.cursor.fetchall()

    def getQuery(self, tableName, cols: str=None, cond: str=None) -> list:
        if cols is None:
            cols = "*"
        
        if cond:
            cond = "WHERE %s" % cond
        else:
            cond = ""

        command = 'SELECT %s FROM public."%s" %s' % (cols, tableName, cond)
        self.execute(command)
        return self.retrieveSelectedQuery()

    def getGeoDataFrame(self, query) -> gpd.GeoDataFrame:
        return gpd.read_postgis(sql=query, con=self.conn, geom_col='geometry')
    
    def getDataFrame(self, query) -> gpd.pd.DataFrame:
        return gpd.pd.read_sql_query(sql=query, con=self.conn)

    def getReferenceDF(self) -> gpd.GeoDataFrame:
        return self.getGeoDataFrame('SELECT osm_id, geometry FROM public."%s";' % self.referenceTable).astype({"osm_id":str})

    def dropTable(self, tableName):
        self.execute('''DROP TABLE IF EXISTS public."%s";'''% (tableName))
            
    def createTable(self, tableName, cols=""):
        command = '''CREATE TABLE public."%s"(%s);
        ALTER TABLE public."%s"
            OWNER to postgres;''' % (tableName, cols, tableName)
        self.execute(command)

    def createTableWithReference(self, tableName, cols=""):
        cols = "osm_id TEXT PRIMARY KEY" + ("" if cols == "" else ",%s" % cols) 
        self.createTable(tableName, cols)

        dataframe = gpd.pd.DataFrame(self.getReferenceDF().drop('geometry',axis=1))
        self.insertDataFrame(dataframe, tableName)

    def getNetToDFMap(self):
        net2df = {}
        table = self.net2DFTable
        
        self.execute('SELECT * FROM public."%s"' % table)
        records = self.retrieveSelectedQuery()
        for row in records:
            net2df[str(row[0])] = str(row[1])
        return net2df

    def close(self):
        self.cursor.close()
        self.conn.close()

class EmissionConnection(SQLConnection):
    def __init__(self):
        SQLConnection.__init__(self)
        self.eTable = "Emissions"
        self.keyColumns = ["Time", "osm_id", "veh_id"]
        self.eColumns = ["Fuel","CO2","CO","HC","NOx","PMx"]

    def get_eTypeCol(self, eType: str) -> str:
        name = {"FUEL":"Fuel", "CO":"CO", "CO2":"CO2", "HC":"HC", "NOX":"NOx","PMX":"PMx"}
        return name[eType.upper()]
    
    def clearEmissionsTable(self):
        self.dropTable(self.eTable)
        self.createTable(self.eTable, '"%s" timestamp without time zone, %s text, %s text, "%s" numeric, "%s" numeric, "%s" numeric, "%s" numeric, "%s" numeric, "%s" numeric'
            % (self.keyColumns[0], self.keyColumns[1], self.keyColumns[2], self.eColumns[0], self.eColumns[1], self.eColumns[2], self.eColumns[3], self.eColumns[4], self.eColumns[5]))
    
    def get_eTableDF_osm(self, eTypes: list, osm_ids: list=None, fromTime: float=None, toTime: float=None) -> gpd.GeoDataFrame:
        ecol = ""
        sumCol = ""
        for col in [self.get_eTypeCol(etype) for etype in eTypes]:
            ecol += 'COALESCE(etype."%s",0) "%s", ' % (col, col)
            sumCol += 'SUM(etype."%s") "%s", ' % (col, col)

        cond = ""
        if fromTime:
           fromTime = self.initalDate + timedelta(days=fromTime // (3600 * 24), seconds=fromTime % (3600 * 24))
           cond = '''WHERE etype."Time" >= '%s' ''' % str(fromTime)
        if toTime:
            toTime = self.initalDate + timedelta(days=toTime // (3600 * 24), seconds=toTime % (3600 * 24))
            if fromTime:
                cond = '''WHERE etype."Time" BETWEEN '%s' AND '%s' ''' % (str(fromTime), str(toTime))
            else:
                cond = '''WHERE etype."Time" <= '%s' ''' % str(toTime)
        
        if osm_ids:
            if cond != "":
                cond += " AND etype.osm_id IN ('%s')" % ("','".join(osm_ids))
            else:
                cond = "WHERE etype.osm_id IN ('%s')" % ("','".join(osm_ids))
        
        command = '''SELECT reference."osm_id", %s, reference."geometry"
        FROM public."%s" reference LEFT OUTER JOIN (
            SELECT etype.osm_id, %s from public."%s" etype
            %s
            group by etype.osm_id) etype
        ON reference."osm_id" = etype."osm_id"''' % (ecol.strip(' ,'), self.referenceTable, sumCol.strip(' ,'), self.eTable, cond)
        
        return self.getGeoDataFrame(command)

    def get_eTableDF_veh(self, eTypes: list, veh_ids: list=None, fromTime: float=None, toTime: float=None) -> gpd.pd.DataFrame:
        sumCol = ""
        for col in [self.get_eTypeCol(etype) for etype in eTypes]:
            sumCol += 'SUM(etype."%s") "%s", ' % (col, col)
        
        cond = ""
        if fromTime:
           fromTime = self.initalDate + timedelta(days=fromTime // (3600 * 24), seconds=fromTime % (3600 * 24))
           cond = '''WHERE etype."Time" >= '%s' ''' % str(fromTime)
        if toTime:
            toTime = self.initalDate + timedelta(days=toTime // (3600 * 24), seconds=toTime % (3600 * 24))
            if fromTime:
                cond = '''WHERE etype."Time" BETWEEN '%s' AND '%s' ''' % (str(fromTime), str(toTime))
            else:
                cond = '''WHERE etype."Time" <= '%s' ''' % str(toTime)
        
        if veh_ids:
            if cond != "":
                cond += " AND etype.veh_id IN ('%s')" % ("','".join(veh_ids))
            else:
                cond = "WHERE etype.veh_id IN ('%s')" % ("','".join(veh_ids))
        
        command = '''SELECT etype.veh_id, %s from public."%s" etype
            %s
            group by etype.veh_id''' % (sumCol.strip(' ,'), self.eTable, cond)
        
        return self.getDataFrame(command)
    
    def insertTimeStep(self, time : float, emissions: gpd.pd.DataFrame):
        date = self.initalDate + timedelta(seconds=time)
        emissions.insert(0, "Time", date)
        self.insertDataFrame(emissions, self.eTable)

class VisualConnection(SQLConnection):
    def __init__(self):
        SQLConnection.__init__(self)
        self.vehTable = "VehicleData"
        self.columns = ["Time", "veh_id", "osm_id", "lon", "lat", "speed", "direction", "vtype", "vclass"]

    def clearVehicleTable(self):
        self.dropTable(self.vehTable)
        self.createTable(self.vehTable, '"%s" timestamp without time zone, "%s" text, "%s" text, "%s" numeric, "%s" numeric, "%s" numeric, "%s" numeric, "%s" text, "%s" text'
            % (self.columns[0], self.columns[1], self.columns[2], self.columns[3], self.columns[4], self.columns[5], self.columns[6], self.columns[7], self.columns[8]))
    
    def getVehDF(self, veh_id, fromTime: float=None, toTime: float=None):
        cond = '''WHERE vehicle."%s" = '%s' ''' % (self.columns[1], veh_id)
        if fromTime:
           fromTime = self.initalDate + timedelta(days=fromTime // (3600 * 24), seconds=fromTime % (3600 * 24))
           cond += ''' AND vehicle."%s" >= '%s' ''' % (self.columns[0], str(fromTime))
        if toTime:
            toTime = self.initalDate + timedelta(days=toTime // (3600 * 24), seconds=toTime % (3600 * 24))
            cond += ''' AND vehicle."%s" <= '%s' ''' % (self.columns[0], str(toTime))
        
        command = '''SELECT * from public."%s" vehicle %s''' % (self.vehTable, cond)
        
        return self.getDataFrame(command)


def initializeReferenceTable(dataframe: gpd.GeoDataFrame):
    '''
    Initializes the SQL database with the reference table for the map.
    The dataframe must have a column named 'osm_id' that is a unique id for each street, and a column named 'geometry' that is the shape of the street".
    '''
    sql = SQLConnection()
    referenceTable = sql.referenceTable

    command = '''DROP TABLE IF EXISTS public."%s";''' % (referenceTable)
    sql.execute(command)
    command = '''CREATE TABLE public."%s"(osm_id text, geometry geometry, PRIMARY KEY (osm_id) );
    ALTER TABLE public."%s"
        OWNER to postgres;''' % (referenceTable, referenceTable)
    sql.execute(command)

    dataframe = dataframe['osm_id', 'geometry']
    sql.insertDataFrame(dataframe, referenceTable)
    sql.close()

def initializeNetToDFTable(net, dataframe):
    '''
    Initializes the SQL database with the conversion from a SUMO network edge to a dataframe street.
    The dataframe must have a column named 'osm_id' that is a unique id for each street".
    '''
    from shapely.geometry.polygon import LineString
    sql = SQLConnection()
    table = sql.net2DFTable
    
    sql.dropTable(table)
    command = '''CREATE TABLE public."%s"(edge_id text, osm_id text);
    ALTER TABLE public."%s"
        OWNER to postgres;''' % (table, table)
    sql.execute(command)

    # Instantiate index class
    idx = dataframe.sindex
    edges = net.getEdges()
    
    # Map each edge to a street
    # Very long to process: ~8.5 mins
    for edge in edges:
        edgeLine = LineString([net.convertXY2LonLat(x,y) for x,y in edge.getShape()])
        for closestIndex in idx.nearest(edgeLine.bounds):
            command = '''INSERT INTO public."%s" VALUES('%s', %s)''' % (table, edge.getID(), dataframe.loc[closestIndex, "osm_id"])
            sql.execute(command)
            break


'''
Combine show between times
select te."geometry", COALESCE(ae.fuel, 0) fuel
FROM public."GeoCoordinates" te left outer join (
	Select ab.osm_id, sum("Fuel") fuel from public."Emissions" ab
	where ab."Time" >= '2000-01-01 0:01:41' and ab."Time" <= '2000-01-01 2:00:00'
	group by ab.osm_id
) ae
ON te."osm_id" = ae."osm_id"
where fuel != 0
'''
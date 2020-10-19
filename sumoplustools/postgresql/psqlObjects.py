import psycopg2, psycopg2.extras
from psycopg2 import errors as sqlerror
from psycopg2 import errorcodes
import numpy as np
import geopandas as gpd

class emissionConnection():
    def __init__(self):
        self.conn = psycopg2.connect(database="SUMO Montreal", user="postgres", password="sumogroup4", host="127.0.0.1", port="5432")
        self.cursor = self.conn.cursor()
        self.eTables = ["Fuel Emissions","CO2 Emissions", "CO Emissions", "HC Emissions", "PMx Emissions", "NOx Emissions"]
        self.referenceTable = "GeoCoordinates"
        self.tempTable = "TEMP"
        self.temp2Table = "TEMPTEMP"
        self.net2DFTable = "NetToDF"

    def execute(self, query):
        try:
            self.cursor.execute(query)
        except Exception:
            self.conn.rollback()
            raise
        self.conn.commit()

    def execute_values(self, query, tuples):
        try:
            psycopg2.extras.execute_values(self.cursor, query, tuples)
        except Exception:
            self.conn.rollback()
            raise
        self.conn.commit()
    
    def insertDataFrame(self, dataframe, tableName):
        tuples = [tuple(x) for x in dataframe.to_numpy()]
        temp_cols = '","'.join(list(dataframe.columns))
        command  = '''INSERT INTO public."%s"("%s") VALUES %%s''' % (tableName, temp_cols)
        self.execute_values(command, tuples)
    
    def retrieveQuery(self) -> list:
        return self.cursor.fetchall()
    
    def get_eTable(self, eType) -> str:
        for table in self.eTables:
            if (eType.strip() + " Emissions").upper() in table.upper():
                return table

    def getReferenceDF(self) -> gpd.GeoDataFrame:
        return gpd.read_postgis('SELECT osm_id, geometry FROM public."%s";' % self.referenceTable, self.conn, geom_col='geometry')

    def dropTable(self, tableName):
        self.execute('''DROP TABLE IF EXISTS public."%s";''' % (tableName))
            
    def dropAll_eTables(self):
        for table in self.eTables:
            self.dropTable(table)
            
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

    def createAll_eTables(self, reference=True, cols=""):
        for table in self.eTables:
            if reference:
                self.createTableWithReference(table, cols=cols)
            else:
                self.createTable(table, cols=cols)

    

    def saveDataFrame(self, dataframe, eType, overide=False):
        eTable = self.get_eTable(eType)
        if overide:
            self.dropTable(eTable)
            self.createTable(eTable)
        else:
            try:
                self.createTable(eTable)
            except sqlerror.lookup(errorcodes.DUPLICATE_TABLE):
                pass
        
        cols = '" numeric, ADD "'.join(list(dataframe.columns))
        self.execute('ALTER TABLE public."%s" ADD "%s" numeric;' % (eTable, cols))
        self.insertDataFrame(dataframe, eTable)
        

    def addColumn(self, col, arr, eType):
        eTable = self.get_eTable(eType)
        tempTable = self.tempTable
        tempDF = self.getReferenceDF()
        
        tempDF = gpd.pd.DataFrame(tempDF.drop("geometry", axis=1))
        tempDF = tempDF.join(gpd.pd.DataFrame(arr), how="right")
        tempDF[0] = tempDF[0].astype(float)
        tempDF = tempDF.rename({0:'%s' % col}, axis=1)
        
        # Refresh Temp table to have the new column
        self.dropTable(tempTable)
        command = '''CREATE TABLE public."%s"("osm_id" text, "%s" numeric);
                ALTER TABLE public."%s"
                    OWNER to postgres;''' % (tempTable, col, tempTable)
        self.execute(command)

        # Insert dataframe into temp table
        self.insertDataFrame(tempDF, tempTable)

        # Create new table with updated etype
        command = '''select etype.*, temp."%s" 
	    into public."%s"
        FROM public."%s" etype INNER JOIN public."%s" temp
        ON etype."osm_id" = temp."osm_id";''' % (col, self.temp2Table, eTable, tempTable)
        self.execute(command)

        # Drop old etype table and rename updated table
        self.dropTable(eTable)
        self.execute('''ALTER TABLE public."%s" RENAME TO "%s";''' % (self.temp2Table, eTable))

        self.dropTable(tempTable)

    def getNetToDFMap(self):
        net2df = {}
        table = self.net2DFTable
        
        self.execute('SELECT * FROM public."%s"' % table)
        records = self.retrieveQuery()
        for row in records:
            net2df[str(row[0])] = int(row[1])
        return net2df

    def getQuery(self, tableName, cols=None, cond=None):
        if cols:
            if type(cols) != str:
                hr = cols // 3600
                mins = (cols % 3600) // 60
                sec = (cols % 3600) % 60
                cols = "%i:%.2i:%.2f" % (hr,mins,sec)
        else:
            cols = "*"
        
        if cond:
            cond = "WHERE %s" % cond
        else:
            cond = ""

        command = 'SELECT %s FROM public."%s" %s' % (cols, tableName, cond)
        self.execute(command)


    def close(self):
        self.cursor.close()
        self.conn.close()

def initializeReferenceTable(dataframe):
    sql = emissionConnection()
    referenceTable = sql.referenceTable

    command = '''DROP TABLE IF EXISTS public."%s";''' % (referenceTable)
    sql.execute(command)
    command = '''CREATE TABLE public."%s"(osm_id text, geometry geometry, PRIMARY KEY (osm_id) );
    ALTER TABLE public."%s"
        OWNER to postgres;''' % (referenceTable, referenceTable)
    sql.execute(command)

    for _, row in dataframe.iterrows():
        command  = "INSERT INTO public.\"%s\" VALUES(%s, '%s');" % (referenceTable, row['osm_id'], row['geometry'][0])
        sql.execute(command)
    sql.close()

def initializeNetToDFTable(net, dataframe):
    from shapely.geometry.polygon import LineString
    sql = emissionConnection()
    table = sql.net2DFTable
    
    sql.dropTable(table)
    command = '''CREATE TABLE public."%s"(net text, dfIndex numeric);
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
            command = '''INSERT INTO public."%s" VALUES('%s', %s)''' % (table, edge.getID(), closestIndex)
            sql.execute(command)
            break

'''select * 
from public."GeoCoordinates"
inner join public."Fuel Emissions" 
on public."Fuel Emissions"."osm_id" = public."GeoCoordinates"."osm_id"
inner join public."CO2 Emissions"
on public."CO2 Emissions"."osm_id" = public."GeoCoordinates"."osm_id"
'''
import psycopg2
from psycopg2 import errors as sqlerror
from psycopg2 import errorcodes
import numpy as np
import geopandas as gpd

class emissionConnection():
    def __init__(self):
        self.conn = psycopg2.connect(database="SUMO Montreal", user="postgres", password="sumogroup4", host="127.0.0.1", port="5432")
        self.cursor = self.conn.cursor()
        self.tables = ["Fuel Emissions","CO2 Emissions", "CO Emissions", "HC Emissions", "PMx Emissions", "NOx Emissions"]
        self.referenceTable = "GeoCoordinates"

    def execute(self, query):
        try:
            self.cursor.execute(query)
        except Exception:
            self.conn.rollback()
            raise
        self.conn.commit()

    def getAllTables(self):
        return self.tables
    
    def getTable(self, eType):
        for table in self.tables:
            if (eType.strip() + " Emissions").upper() in table.upper():
                return table

    def getReferenceTable(self) -> gpd.GeoDataFrame:
        return gpd.read_postgis('SELECT osm_id, geometry FROM public."%s";' % self.referenceTable, self.conn, geom_col='geometry')

    def dropTable(self,eType):
        table = self.getTable(eType)
        command = '''DROP TABLE IF EXISTS public."%s";''' % (table)
        self.execute(command)
            
    def dropAllTables(self):
        for table in self.tables:
            command = '''DROP TABLE IF EXISTS public."%s";''' % (table)
            self.execute(command)
            
    def createTable(self,eType):
        table = self.getTable(eType)
        command = '''CREATE TABLE public."%s"(osm_id TEXT PRIMARY KEY);
        ALTER TABLE public."%s"
            OWNER to postgres;''' % (table, table)
        self.execute(command)

    def createTableWithReference(self, eType):
        table = self.getTable(eType)
        self.createTable(eType)

        dataframe = self.getReferenceTable()
        for _, row in dataframe.iterrows():
            self.execute("INSERT INTO public.\"%s\" VALUES(%s);" % (table, row[0]))

    def saveDataFrame(self, dataframe, eType, overide=False):
        table = self.getTable(eType)
        if overide:
            try:
                self.dropTable(eType)
                self.createTable(eType)
            except sqlerror.lookup(errorcodes.DUPLICATE_TABLE):
                raise Exception("Cannot save dataframe if table already exist")

        cols = '" numeric, ADD "'.join(list(dataframe.columns)[1:])
        self.execute('ALTER TABLE public."%s" ADD "%s" numeric;' % (table, cols))
        for _, row in dataframe.iterrows():
            r = ''
            for col in dataframe.columns:
                r += '%s,' % str(row[col]) 
            self.execute("INSERT INTO public.\"%s\" VALUES(%s);" % (table, r[:-1]))

    def addColumn(self, col, arr, eType):
        table = self.getTable(eType)
        dataFrame = self.getReferenceTable()
        ## Imporve Speed ##
        self.execute('ALTER TABLE public."%s" ADD "%s" numeric;' % (table, col))
        for i, num in enumerate(arr):
            self.execute('UPDATE public."%s" SET "%s" = %f WHERE "osm_id" = \'%s\';' % (table, col, num, dataFrame.loc[i,"osm_id"]))

    def close(self):
        self.cursor.close()
        self.conn.close()

def initializeReferenceTable(dataframe):
    sql = emissionConnection()
    referenceTable = sql.referenceTable
    try:
        command = '''CREATE TABLE public."%s"(osm_id text, geometry geometry, PRIMARY KEY (osm_id) );

        ALTER TABLE public."%s"
            OWNER to postgres;''' % (referenceTable, referenceTable)
    
        sql.execute(command)
    except sqlerror.lookup(errorcodes.DUPLICATE_TABLE):
        command = '''DELETE FROM public."%s";''' % referenceTable
        sql.execute(command)

    for _, row in dataframe.iterrows():
        command  = "INSERT INTO public.\"%s\" VALUES(%s, '%s');" % (referenceTable, row['osm_id'], row['geometry'][0])
        sql.execute(command)
    sql.close()

def initializeNetToDFTable(net, dataframe):
    pass
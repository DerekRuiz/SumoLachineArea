from  EmissionTools import sumoEmission as se, emissionIO as eio
#import geopandas


#se.setSumocfgFile("lachine_OD.sumocfg")
se.setEmissionFile("Outputs/traceEmission.xml")
se.createStreetsDF("lachine_bbox.osm.xml")

se.collectEmissions(filepath="Emissions/Lachine_Emission", eTypes=['Fuel'], fromStep=7*3600, useDuration=True, duration=2*3600, timeInterval=60*15, useFile=True)

df = eio.loadDataFrame('Emissions/Lachine_Emission_Fuel')
print(df.head())
print(df.columns)

se.closeTraCI()
from  EmissionTools import sumoEmission as se, emissionIO as eio
import geopandas


se.validateEtype(['Fuel','CO','FD'])

se.setEmissionFile()
se.createStreetsDF()

se.collectEmissions("DaStreets",['Fuel','CO2'],10,20,timeInterval=6)

df = eio.loadDataFrame('DaStreets_Fuel')
print(df.head())

se.closeTraCI()
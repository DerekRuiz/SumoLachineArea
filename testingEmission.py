from  EmissionTools import sumoEmission as se, emissionIO as eio
import geopandas



#se.setEmissionFile()
#se.createStreetsDF()

#se.collectEmissions("Emissions/Lachine_Emission",['Fuel','NOx'],10,80,timeInterval=5)

df = eio.loadDataFrame('Emissions/Lachine_Emission_Fuel')
print(df.head())

se.closeTraCI()
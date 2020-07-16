import sumoEmission as se

se.setEmissionFile()
se.createStreetsDF()

se.setStreetsDFFile(1,toStep=4)

se.createFigure(all=True)
se.showFigure()

se.createFigure(all=False, fuel=True, NOx=True)
se.showFigure()
se.saveFigure("test")

se.saveStepFigures(fromStep=1, useDuration=True, duration=5, useFile=False)

se.closeTraCI()
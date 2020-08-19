import traci
import time
import xml.etree.ElementTree as ET
import os
import subprocess

def createBatchFile(netFile, outputFile, frequency=1, beginning=0, end=3600, seed=None, batch="batch.bat"):
    seedCmd = "" if seed is None else "--seed %s" % (str(seed))

    cmdLine = "%%SUMO_HOME%%tools/randomTrips.py -n %s -o %s -p %s -b %s -e %s %s --vehicle-class passenger --vclass passenger --prefix veh --trip-attributes \"departLane=\\\"best\\\"\" --fringe-start-attributes \"departSpeed=\\\"max\\\"\" --validate" % (netFile, outputFile, str(frequency), str(beginning), str(end), seedCmd)
    with open(batch, "w") as f:
        f.write(cmdLine)

def callBatchFile(file):
    subprocess.call([r"%s" % file])

def loopTest(loop=1, increment=100):
    for i in range(loop + 1):
        if i == 0:
            continue
        p = 300 / (increment * i)
        createBatchFile("C:/Users/epicb/Documents/GitHub/SumoLachineArea/MergeMaps/montreal.net.xml", "C:/Users/epicb/Documents/GitHub/SumoLachineArea/MergeMaps/Trips/montreal.passenger.trips.xml",p,0,300,18, batch="C:/Users/epicb/Documents/GitHub/SumoLachineArea/MergeMaps/batch.bat")
        callBatchFile("C:/Users/epicb/Documents/GitHub/SumoLachineArea/MergeMaps/batch.bat")

        sumocfg = "C:/Users/epicb/Documents/GitHub/SumoLachineArea/MergeMaps/montreal.sumocfg"
        cmd = ["sumo","-c",sumocfg]
        tree = ET.parse(sumocfg)
        root = tree.getroot()
        routeFile = os.path.abspath(root.find(".//route-files").get("value"))
        tree = ET.parse(routeFile)
        root = tree.getroot()
        trips = len(root.findall(".//trip"))

        loadStart = time.time()
        traci.start(cmd)
        loadStop = time.time()

        timeStart = time.time()
        cpuStart = time.process_time()

        while traci.simulation.getMinExpectedNumber() > 0:

            traci.simulationStep()

        cpuStop = time.process_time()
        timeStop = time.time()

        steps = traci.simulation.getTime()
        traci.close()

        with open("C:/Users/epicb/Documents/GitHub/SumoLachineArea/MergeMaps/speedOutput.txt", "a") as f:
            f.write("%i\t\t\t\t%f\t\t\t%f\t\t\t\t%f\t\t\t%f\n" % (trips, (loadStop - loadStart), (timeStop - timeStart), (cpuStop - cpuStart), steps))
    os.remove("C:/Users/epicb/Documents/GitHub/SumoLachineArea/MergeMaps/batch.bat")

if __name__ == "__main__":
    loopTest(10)
    
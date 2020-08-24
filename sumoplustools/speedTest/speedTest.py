import traci
import time
import xml.etree.ElementTree as ET
import os
import subprocess
import argparse

def createBatchFile(netFile, outputFile, frequency=1, beginning=0, end=3600, seed=None, batch="batch.bat"):
    global vClass
    seedCmd = "" if seed is None else "--seed %s" % (str(seed))
    cmdLine = "%%SUMO_HOME%%tools/randomTrips.py -n %s -o %s -p %s -b %s -e %s %s --vehicle-class %s --vclass %s --prefix %.3s --trip-attributes \"departLane=\\\"best\\\"\" --fringe-start-attributes \"departSpeed=\\\"max\\\"\" --validate" % (netFile, outputFile, str(frequency), str(beginning), str(end), seedCmd, vClass, vClass, vClass)
    with open(batch, "w") as f:
        f.write(cmdLine)

def callBatchFile(file):
    subprocess.call([r"%s" % file])

def loopTest(loop=1, initial=0, increment=100, startSpawn=0, stopSpawn=3600, seed=None):
    tempBatchFile = "batch.bat"
    i = 0
    while os.path.exists(tempBatchFile):    
        tempBatchFile = "batch_%i.bat" % i
        i += 1
    
    for i in range(loop):
        try:
            p = stopSpawn / ((increment * i) + initial)
        except ZeroDivisionError:
            continue

        global netFile
        global routeFiles
        createBatchFile(netFile, routeFiles[0], frequency=p, beginning=startSpawn, end=stopSpawn, seed=seed, batch=tempBatchFile)
        callBatchFile(tempBatchFile)

        global cfgFile
        cmd = ["sumo-gui","-c", cfgFile, "--start", "1"]
        
        tree = ET.parse(routeFiles[0])
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

        global outputFile
        with open(outputFile, "a") as f:
            f.write("%i\t\t\t\t%f\t\t\t%f\t\t\t\t%f\t\t\t%f\t\t%f\n" % (trips, (loadStop - loadStart), (timeStop - timeStart), (cpuStop - cpuStart), steps, (steps / (timeStop - timeStart))))
    try:
        os.remove(tempBatchFile)
    except FileNotFoundError:
        pass

def fillOptions(argParser):
    argParser.add_argument("-c", "--sumo-config-file", 
                            metavar="FILE", required=True,
                            help="use FILE to populate data using TraCI (mandatory)")
    argParser.add_argument("-o", "--output-file", 
                            metavar="FILE", default="speedOutput.txt",
                            help="appends testing results to FILE")
    argParser.add_argument("-i", "--initial",
                            type=int, default=0, metavar="INT",
                            help="initial number of vehicles for the first loop")
    argParser.add_argument("-j", "--increment",
                            type=int, default=100, metavar="INT",
                            help="number of vehicles to increment each loop")
    argParser.add_argument("-s", "--start-spawning",
                            type=int, default=0, metavar="INT",
                            help="step time when vehicles start spawning in the simulation")
    argParser.add_argument("-t", "--stop-spawning",
                            type=int, default=3600, metavar="INT",
                            help="step time when vehicles stop spawning in the simulation")
    argParser.add_argument("-d", "--seed",
                            type=int, default=None, metavar="INT",
                            help="the seed for the psuedo-random generator for vehicle spawn location")
    argParser.add_argument("-l", "--loops",
                            type=int, default=1, metavar="INT",
                            help="the number of times to test")
    argParser.add_argument("-v", "--vehicle-class",
                            default="passenger", metavar="STR",
                            help="generate vehicles of STR type")

def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Tests the speed of the SUMO simulation with increasing amount of vehicles")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    global outputFile
    outputFile = options.output_file

    global cfgFile
    cfgFile  = options.sumo_config_file

    tree = ET.parse(options.sumo_config_file)
    root = tree.getroot()

    global netFile
    netFile = root.find(".//net-file").get("value")

    global routeFiles
    routeFiles = root.find(".//route-files").get("value").split(",")

    global vClass
    vClass = options.vehicle_class

    loopTest(loop=options.loops, initial=options.initial, increment=options.increment, startSpawn=options.start_spawning, stopSpawn=options.stop_spawning, seed=options.seed)
    
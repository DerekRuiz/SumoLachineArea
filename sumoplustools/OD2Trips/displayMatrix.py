import os, sys
import argparse
import numpy as np
import geopandas as gpd
from xml.etree import ElementTree as ET
from shapely.geometry import Polygon, Point, MultiLineString
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sumoplustools import verbose


def fillOptions(argParser):
    argParser.add_argument("-m", "--matrix", 
                            metavar="FILE", required=True,
                            help="displays matrix from numpy FILE or all matrices from DIR (mandatory)")
    argParser.add_argument("-r", "--reference", 
                            metavar="FILE",
                            help="references the matrix indeces with a geometry in geoJson format")
    argParser.add_argument("-n", "--sumo-net-file", 
                            metavar="FILE", required=not ('--reference' in sys.argv or '-r' in sys.argv),
                            help="conversion to SUMO coords using FILE. Only required if reference not provided")
    argParser.add_argument("-t", "--taz-add-file", 
                            metavar="FILE", required=not ('--reference' in sys.argv or '-r' in sys.argv),
                            help="gets districts from FILE. Only required if reference not provided")
    argParser.add_argument("-v", "--verbose",
                            action="store_true", default=False,
                            help="gives description of current task")

def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Display OD matrix to display the trips between destricts")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    if options.verbose:
        verbose.addVerboseSteps(["extracting data from SUMO network file", "extracting data from TAZ file", "extracting data from OD matrix"])
        verbose.writeToConsole()


    if options.reference:
        if options.verbose:
            verbose.addVerboseSteps(["extracting data reference file", "extracting data from OD matrix", "displaying matrix"])
            verbose.writeToConsole()
        import json
        with open(options.reference, "r") as f:
            j = json.load(f)
            if isinstance(j, str):
                j = json.loads(j)

        tazShapes = gpd.GeoDataFrame.from_features(j['features'])
        if options.verbose:
            verbose.writeToConsole(done=True)
    else:
        if options.verbose:
            verbose.addVerboseSteps(["extracting data from SUMO network file", "extracting data from TAZ file", "extracting data from OD matrix", "displaying matrices"])
            verbose.writeToConsole()

        import sumolib
        net = sumolib.net.readNet(options.sumo_net_file)

        if options.verbose:
            verbose.writeToConsole(done=True)

        tazXMLIter = ET.iterparse(options.taz_add_file)
        tazShapes = {}
        tazShapes['taz_id'] = []
        tazShapes['geometry'] = []
        for _, elem in tazXMLIter:
            if elem.tag != "taz":
                continue
            
            taz_id = int(elem.get("id").split("_")[1])
            polygon = []
            for position in elem.get("shape").split():
                x, y = position.split(",")
                x, y = float(x.strip()), float(y.strip())

                lon, lat = net.convertXY2LonLat(x, y)
                polygon += [(lon, lat)]
            tazShapes['taz_id'] += [taz_id]
            tazShapes['geometry'] += [Polygon(polygon)]

            elem.clear()
            del elem
        del tazXMLIter
        tazShapes = gpd.GeoDataFrame(tazShapes)

        if options.verbose:
            verbose.writeToConsole(done=True)

        
    if os.path.isdir(options.matrix):
        matrices = []
        for f in [f for f in os.listdir(options.matrix) if '.npy' in f[-4:]]:
            matrices += [(os.path.split(f)[1][:-4], np.load(os.path.join(options.matrix,f)))]
    else:
        matrices = [(os.path.split(options.matrix)[1][:-4], np.load(options.matrix))]
    
    if options.verbose:
        verbose.writeToConsole(done=True)

    for name, tazMatrix in matrices:
        tazShapes["ori_trips"] = np.sum(tazMatrix, axis=1).tolist()
        tazShapes["des_trips"] = np.sum(tazMatrix, axis=0).tolist()

        fig, axs = plt.subplots(2,2)
        fig.suptitle("Trips for file %s" % name)
        axs[0,0].set_title("# of Trips Started")
        axs[0,1].set_title("# of Trips Ended")
        tazShapes.plot(column='ori_trips', legend=True, ax=axs[0,0])
        tazShapes.plot(column='des_trips', legend=True, ax=axs[0,1])
        axs[1,0].set_xlabel("TAZ ID")
        axs[1,0].set_ylabel("# Trips")
        axs[1,1].set_xlabel("TAZ ID")
        axs[1,0].bar(tazShapes['taz_id'], np.sum(tazMatrix, axis=1))
        axs[1,1].bar(tazShapes['taz_id'], np.sum(tazMatrix, axis=0))

    plt.show()

    if options.verbose:
        verbose.writeToConsole(done=True)

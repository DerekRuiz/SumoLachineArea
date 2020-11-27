
import os, sys
import argparse
import sumolib
import geopandas as gpd
from xml.etree import ElementTree as ET

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sumoplustools import verbose



def fillOptions(argParser):
    argParser.add_argument("-n", "--sumo-net-file", 
                            metavar="FILE", required=True,
                            help="conversion to SUMO coords using FILE (mandatory)")
    argParser.add_argument("-c", "--census-file", 
                            metavar="FILE", required=True,
                            help="create districts based from shape-like FILE (mandatory)")
    argParser.add_argument("-b", "--boundary-file", 
                            metavar="FILE",
                            help="boundary shape-like FILE to limit the area of the census")
    argParser.add_argument("-o", "--output-file",
                            metavar="FILE", default="taz.add.xml",
                            help="TAZ data is save to FILE")
    argParser.add_argument("-v", "--verbose",
                            action="store_true", default=False,
                            help="gives description of current task")

    
def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Create additional file containing the traffic analysis zones used for SUMO districts.")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    if options.verbose:
        verbose.addVerboseSteps(["extracting data from SUMO network file", "extracting data from cencus tracts shape file"])
        verbose.writeToConsole()

    net = sumolib.net.readNet(options.sumo_net_file)
    if options.verbose:
        verbose.writeToConsole(done=True)
    tracts = gpd.read_file(options.census_tracts_file)
    tracts.to_crs(epsg=4326, inplace=True)
    if options.verbose:
        verbose.writeToConsole(done=True)

    if options.boundary_file:    
        if options.verbose:
            verbose.addVerboseSteps(["extracting data from boundary shape file"])
            verbose.writeToConsole()
        poly = gpd.read_file(options.boundary_file)
        poly.to_crs(epsg=4326, inplace=True)
        tracts = tracts.loc[tracts.within(poly.loc[0, 'geometry'])]
        if options.verbose:
            verbose.writeToConsole(done=True)

    if options.verbose:
        verbose.addVerboseSteps(["creating TAZ districts", "writing TAZ to file"])
        verbose.writeToConsole()

    root = ET.Element("additional")
    taz_id = 0
    for row_tuple in tracts.itertuples():
        geom = row_tuple.geometry
        sumo_geom = ""
        geomXs, geomYs = geom.exterior.coords.xy
        for lon, lat in zip(geomXs, geomYs):
            x, y = net.convertLonLat2XY(lon, lat)
            sumo_geom += "%s,%s " % (x, y)
        
        taz_elem = ET.Element("taz", {"id":"taz_%i" % taz_id, "shape":sumo_geom.strip(), "color":"blue"})
        root.append(taz_elem)
        taz_id += 1

        if options.verbose:
            verbose.writeToConsole(verboseValue=taz_id)

    if options.verbose:
        verbose.writeToConsole(done=True)

    tree = ET.ElementTree(root)
    tree.write(options.output_file)

    if options.verbose:
        verbose.writeToConsole(done=True)

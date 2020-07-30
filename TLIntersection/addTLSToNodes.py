
import argparse
from os import path


def fillOptions(argParser):
    argParser.add_argument("-n", "--sumo-net-file", metavar="FILE",
                            help="Read SUMO-net from FILE")
    argParser.add_argument("-c", "--csv-file", metavar="FILE",
                            help="Read TLS locations from FILE")
    argParser.add_argument("-o", "--node-output-file", 
                            metavar="FILE", default='tls.nod.xml',
                            help="The generated nodes will be written to FILE")


def parse_args(args=None):
    argParser = argparse.ArgumentParser()
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    # Get net file
    if not options.sumo_net_file:
        argParser.print_help()
        argParser.exit("Error! Providing a net file is mandatory")
    else:
        if not path.exists(options.sumo_net_file):
            argParser.exit("Error! Net file not found")

    # Get csv file
    if not options.csv_file:
        argParser.print_help()
        argParser.exit("Error! Providing a csv file is mandatory")
    else:
        if not path.exists(options.csv_file):
            argParser.exit("Error! CSV file not found")

    import sumolib
    import pandas as pd
    from xml.etree import ElementTree as ET
    from shapely.geometry import polygon

    net = sumolib.net.readNet(options.sumo_net_file)
    nodes = net.getNodes()

    df = pd.read_csv(options.csv_file)
    df = df.loc[df['Arrondissement'] == 'Lachine']

    topElem = ET.Element("nodes")

    for _, row in df.iterrows():
        lon, lat = row['long'], row['lat']
        x, y = net.convertLonLat2XY(lon,lat)

        for node in nodes:
            id = node.getID()
            shape = node.getShape()
            if len(shape) < 3:
                continue
            
            if polygon.Polygon(shape).contains(polygon.Point(x,y)):
                elem = ET.SubElement(topElem,'node')
                elem.attrib = {'id':id, 'type':'traffic_light'}

    tree = ET.ElementTree(topElem)
    tree.write(options.node_output_file)

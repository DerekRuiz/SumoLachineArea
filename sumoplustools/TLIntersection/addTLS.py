
import argparse
from os import path


def fillOptions(argParser):
    argParser.add_argument("-n", "--sumo-net-file", 
                            metavar="FILE", required=True,
                            help="Read SUMO-net from FILE (mandatory)")
    argParser.add_argument("-c", "--csv-file", 
                            metavar="FILE", required=True,
                            help="Read TLS locations from FILE (mandatory)")
    argParser.add_argument("-o", "--node-output-file", 
                            metavar="FILE", default='tls.nod.xml',
                            help="The generated nodes will be written to FILE")

def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Creates a node file containing traffic lights")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    # Set net file
    if not path.exists(options.sumo_net_file):
        argParser.error("net file not found")

    # Set csv file
    if not path.exists(options.csv_file):
        argParser.error("CSV file not found")

    import sumolib
    import pandas as pd
    from xml.etree import ElementTree as ET
    from shapely.geometry import polygon

    net = sumolib.net.readNet(options.sumo_net_file)
    df = pd.read_csv(options.csv_file)

    topElem = ET.Element("nodes")
    
    xmin,ymin,xmax,ymax = net.getBoundary()
    boundary = polygon.Polygon([(xmin,ymin),(xmax,ymin),(xmax,ymax),(xmin,ymax),(xmin,ymin)])
        
    for _, row in df.iterrows():
        lon, lat = row['long'], row['lat']
        x, y = net.convertLonLat2XY(lon,lat)
        # Check each surrounding edge for nodes
        for edge in net.getNeighboringEdge(x, y, radius=100):
            # Check if the from node contains the traffic light
            node = edge.getFromNode()
            if node:
                shape = node.getShape()
                if len(shape) < 3:
                    continue

                node_id = node.getID()
                if polygon.Polygon(shape).contains(polygon.Point(x,y)):
                    elem = ET.SubElement(topElem,'node')
                    elem.attrib = {'id':node_id, 'type':'traffic_light'}
                    break

            # Check if the to node contains the traffic light 
            node = edge.getToNode()
            if node:
                shape = node.getShape()
                if len(shape) < 3:
                    continue

                node_id = node.getID()
                if polygon.Polygon(shape).contains(polygon.Point(x,y)):
                    elem = ET.SubElement(topElem,'node')
                    elem.attrib = {'id':node_id, 'type':'traffic_light'}
                    break

    tree = ET.ElementTree(topElem)
    tree.write(options.node_output_file)

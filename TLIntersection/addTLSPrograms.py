
import argparse
from os import path

def setStatePed(edges):
    state = ''
    for edge in edges:
        
        state += 'r'
    return state


def fillOptions(argParser):
    argParser.add_argument("-n", "--sumo-net-file", 
                            metavar="FILE", required=True,
                            help="Read SUMO-net from FILE")
    argParser.add_argument("-c", "--csv-file", 
                            metavar="FILE", required=True,
                            help="Read TLS schedules from FILE")
    argParser.add_argument("-o", "--programs-output-file", 
                            metavar="FILE", default='tlsPrograms.add.xml',
                            help="The generated TLS programs will be written to FILE")


def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Creates an additional file containing the programs of traffic lights")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    # Set net file
    if not path.exists(options.sumo_net_file):
        argParser.exit("Error! Net file not found")

    # Set csv file
    if not path.exists(options.csv_file):
        argParser.exit("Error! CSV file not found")

    import sumolib
    import pandas as pd
    from xml.etree import ElementTree as ET
    from shapely.geometry import polygon

    net = sumolib.net.readNet(options.sumo_net_file)

    lights = net.getTrafficLights()


    xmls = "<additional>\n"
    for light in lights:
        if light.getID() == 'cluster_609404690_6837771872' or light.getID() == 'cluster_248512340_6837771871':
            continue
        try:
            junction = net.getNode(light.getID())
            if junction.getType() == "rail_crossing":
                continue
        except KeyError:
            pass

        program = sumolib.net.TLSProgram(id='1', offset=1, type='static')
        state = ''
        edges = []
        
        for connections in light.getConnections():
            inLane = connections[0]
            outLane = connections[1]
            linkNum = connections[2]

            edge = inLane.getEdge()
            if edge.allows('pedestrian') and edge not in edges:
                edges += [edge]

            state += 'g'
        
        # Get crosswalks
        state += setStatePed(edges)

        program.addPhase(state, 31)
        light.removePrograms()
        light.addProgram(program)
        xmls += light.toXML()

    xmls += "</additional>"
    with open(options.programs_output_file,'w') as f:
        f.write(xmls)
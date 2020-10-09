import argparse
import sumolib
import xml.etree.ElementTree as ET


def fillOptions(argParser):
    argParser.add_argument("-p", "--parking-file", 
                            metavar="FILE", required=True,
                            help="get parking locations from FILE (mandatory)")
    argParser.add_argument("-n", "--network-file", 
                            metavar="FILE", required=True,
                            help="SUMO network file (mandatory)")
    argParser.add_argument("-o", "--output-file", 
                            metavar="FILE", required=True,
                            help="saves SUMO additional to FILE (mandatory)")
    argParser.add_argument("-d", "--default", 
                            action='store_true', default=False,
                            help="place parking is default zones (residential, tertiary)")
def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Adds Alternative Side Parking to additional file")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()
    
    net = sumolib.net.readNet(options.network_file)
    root = ET.Element('additional')

    sizeOfCar = 5
    if options.default:
        for edge in net.getEdges():
            if edge._type in ['highway.residential','highway.tertiary', 'highway.living_street']:
                # Compensate edge length for a margin of empty space on both ends of the street
                margin = 5.0
                edgeLength = edge.getLength() - (2 * margin)
                if edgeLength < sizeOfCar:
                    continue
                
                laneID = edge.getLane(idx=0).getID()
                capacity = edgeLength // sizeOfCar

                root.append(ET.Element('parkingArea',{'id':'parkingArea_%s' % laneID, 'lane':laneID, 'roadsideCapacity':'%i' % capacity, 'startPos':str(margin), 'endPos':str(-margin), 'friendlyPos':"1"}))
    else:
        def second(elem):
            return elem[1]

        edgesDone = []
        for spot in parkingSpots:
            capacity = getCapacity(spot)
            lat,lon = getLocation(spot)
            x, y = net.convertLonLat2XY(lon, lat)
            radius = 100
            edges = net.getNeighboringEdge(x, y, radius)
            if len(edges) > 0:
                edgeDist = sorted(edges, key=second)
                for edge, _ in edgeDist:
                    if edge not in edgesDone:
                        edgesDone += [edge.getID()]
                        laneID = edge.getLane(idx=0).getID()
                        root.append(ET.Element('parkingArea',{'id':'parkingArea_%s' % laneID, 'lane':laneID, 'roadsideCapacity':str(int(capacity)), 'startPos':str(margin), 'endPos':str(-margin), 'friendlyPos':"1"}))
                
    tree = ET.ElementTree(root)
    tree.write(options.output_file)
    
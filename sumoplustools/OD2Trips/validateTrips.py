import argparse

def fillOptions(argParser):
    argParser.add_argument("-n", "--sumo-network-file", 
                            metavar="FILE", required=True,
                            help="SUMO network FILE (mandatory)")
    argParser.add_argument("-t", "--trips-file",
                            metavar="FILE",  required=True,
                            help="update trips to FILE (mandatory)")
    argParser.add_argument("-v", "--vehicle-class",
                            type=str, default="passenger", metavar="STR",
                            help="validates trips for vehicles of this type")

def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Validate trips (by removing trips that do not allow the vehicle type to travel on)")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    import sumolib
    from xml.etree import ElementTree as ET

    net = sumolib.net.readNet(options.sumo_network_file)

    # Remove trips where vehicle cannot travel on edges
    tree = ET.parse(options.trips_file)
    root = tree.getroot()
    for trip in root.findall("trip"):
        for edge in (trip.get('from'), trip.get('to')):
            if (edge is not None) and (not net.getEdge(edge).allows(options.vehicle_class)):
                root.remove(trip)
                break

    # Write to file
    hasConf = False
    preXML = ""
    with open(options.trips_file, "r") as od_file:
        for line in od_file:
            if 'configuration' in line:
                hasConf = True
            preXML += line
            if "-->" in line:
                break
    if not hasConf:
        preXML = ""

    tree.write(options.trips_file)

    with open(options.trips_file, "r+") as od_file:
        xml_content = od_file.read()
        od_file.seek(0,0)
        od_file.write(preXML + xml_content)
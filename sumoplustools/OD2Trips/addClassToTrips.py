import argparse
import xml.etree.ElementTree as ET

def writeToFile(options):
    od_tree = ET.parse(options.odtrip_file)
    root = od_tree.getroot()
    if root.tag != "routes":
        exit("OD trip file not proper file structure")
    atrributes = {"id":options.vehicle_id, "vClass":options.vehicle_class}
    vtype = ET.Element("vType",attrib=atrributes)
    root.insert(0,vtype)

    preXML = ""
    with open(options.odtrip_file, "r") as od_file:
        for line in od_file:
            if "routes" in line:
                break
            preXML += line

    od_tree.write(options.odtrip_file)

    with open(options.odtrip_file, "r+") as od_file:
        xml_content = od_file.read()
        od_file.seek(0,0)
        od_file.write(preXML + xml_content)


def fillOptions(argParser):
    argParser.add_argument("-od", "--odtrip-file", 
                            metavar="FILE", type=str, required=True,
                            help="write class type to FILE (mandatory)")
    argParser.add_argument("-i", "--vehicle-id", 
                            metavar="STR", type=str, default="veh_passenger",
                            help="assigns a vehicle type this id")
    argParser.add_argument("-v", "--vehicle-class", 
                            metavar="STR", type=str, default="passenger",
                            help="assigns a vehicle type this class")

def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Adds class type from vehicle type to OD trips")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser

if __name__ == "__main__":
    options, argParser = parse_args()

    writeToFile(options)
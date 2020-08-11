"""
Enter following command in Command Prompt:
osmconvert large-osm.osm.pbf -B="poly-file.poly" -o=osm-file.osm
Add </osm> to the end of "osm-file.osm" file
netconvert --osm-files "osm-file.osm" -o net-file.net.xml --output.street-names True
"""
import argparse


def fillOptions(argParser):
    argParser.add_argument("-g", "--montreal-geometry", metavar="FILE",
                            help="montreal geometry using xml or geojson")
    argParser.add_argument("-p", "--polygon-file", metavar="FILE",
                            help="write polygons to FILE")
    argParser.add_argument("-b", "--use-districts",
                            action='store_true', dest='districts', default=False,
                            help="use districts of montreal to create montreal osm")
    


def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Adds class type from vehicle type to OD trips")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    poly_file = open(options.polygon_file, "w")
    poly_file.write("montreal_city\n")

    if options.districts:
        import xml.etree.ElementTree as ET
        tree = ET.parse(options.montreal_geometry)
        root = tree.getroot()
        for place in root.findall(".//fme_LIMADMIN"):

            name = place.find("fme_NOM")
            name_text = name.text
            poly_file.write("%s\n" % name_text)

            geom = place.find("fme_GEOM")
            geom_text = geom.text
            poly = geom_text.replace("MULTIPOLYGON","")
            poly = poly.replace("(","")
            poly = poly.replace(")","")

            for coord in poly.split(","):
                poly_file.write(" %s\n" % coord)
            
            poly_file.write("END\n")
    else:
        import json
        with open(options.montreal_geometry) as f:
            data = json.load(f)

        for lon, lat in data['features'][0]['geometry']['coordinates'][0][0]:
            poly_file.write("\t%f %f\n" % (lon, lat))

        poly_file.write("END")
        poly_file.close()
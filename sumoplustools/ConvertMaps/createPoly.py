import json
import argparse


def fillOptions(argParser):
    argParser.add_argument("-g", "--montreal-geometry", 
                            metavar="FILE", type=str, required=True,
                            help="montreal geometry using geojson (mandatory)")
    argParser.add_argument("-p", "--polygon-file", 
                            metavar="FILE", type=str, default="boundary.poly",
                            help="write polygons to FILE (mandatory)")

def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Create polygon file to get the shape of the map")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser

if __name__ == "__main__":
    options, argParser = parse_args()

    poly_file = open(options.polygon_file, "w")
    poly_file.write("boundary\n")

    with open(options.montreal_geometry) as f:
        data = json.load(f)

    geom = data['features'][0]['geometry']
    geomType = geom['type']

    if len(geom['coordinates']) > 1:
        raise Exception("Geometry cannot have multiple polygon boundaries")
    
    if geomType == "Polygon":
        coords = geom['coordinates'][0]
    elif geomType == "MultiPolygon":
        if len(geom['coordinates'][0]) > 1:
            raise Exception("Geometry cannot have multiple polygon boundaries")
        coords = geom['coordinates'][0][0]
    else:
        raise Exception('Geometry type "%s" is invalid to create a boundary' % geomType)

    for lon, lat in coords:
        poly_file.write("\t%f %f\n" % (lon, lat))

    poly_file.write("END")
    poly_file.close()
import argparse


def fillOptions(argParser):
    argParser.add_argument("-osm", "--osm-file", metavar="FILE",
                            help='add "</osm>" to end of FILE')
    

def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Adds class type from vehicle type to OD trips")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    osm = True
    with open(options.osm_file, "r") as f:
        line = f.readline()
        while line:
            if "</osm>" in line:
                osm = False
                break
            try:
                line = f.readline()
            except UnicodeDecodeError:
                pass
    if osm:    
        with open(options.osm_file, "a") as f:
            f.write("</osm>")
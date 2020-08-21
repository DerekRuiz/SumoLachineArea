from xml.etree import ElementTree as ET
import os
import argparse


def fillOptions(argParser):
    argParser.add_argument("-o", "--od-matrix-dir", 
                            metavar="DIR", required=True,
                            help="DIR where all od-matrices are located")
    argParser.add_argument("-c", "--config-file", 
                            metavar="FILE", required=True,
                            help="update FILE to reference origin destination matrices")
    argParser.add_argument("-t", "-taz-file",
                            metavar="FILE",
                            help="use FILE to indicate boundaries of zones")

def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Updates the matrix configuration file to reference all origin destination matrices")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    if not (os.path.exists(options.od_matrix_dir) and os.path.isdir(options.od_matrix_dir)):
        raise Exception('There is no folder titled OD_Matrices')

    od_matrix_files = os.listdir(options.od_matrix_dir)
    try:
        od_matrix_files.remove("OD_matrix_template.od")
    except ValueError:
        pass

    if len(od_matrix_files) == 0:
        raise Exception("No files in OD_Matrices folder")
    
    value = ""
    for f in od_matrix_files:
        value += "," + options.od_matrix_dir + f
    value = value.replace(",","",1)

    try:
        conf_tree = ET.parse(options.config_file)
        root = conf_tree.getroot()
    except FileNotFoundError:
        root = ET.Element("configuration")
        root.append(ET.Element("input"))
        conf_tree = ET.ElementTree(root)

    try:
        root.find(".//taz-files").set('value', options.taz_file)
    except NameError:
        root.find(".//input").append(ET.Element("od-matrix-files",{"value":options.taz_file}))

    try:
        root.find(".//od-matrix-files").set('value', value)
    except NameError:
        root.find(".//input").append(ET.Element("od-matrix-files",{"value":value}))
    
    conf_tree.write(options.config_file)

import os,sys
import geopandas as gpd
from matplotlib import pyplot as plt

def displayGeoDataFrame(dataframe : gpd.GeoDataFrame):
    dataframe.plot()
    plt.show()


if __name__ == "__main__":
    import argparse
    
    def fillOptions(argParser):
        argParser.add_argument("-e", "--emission-file", 
                                metavar="FILE", required=True,
                                help="read shape-like FILE and displays it (mandatory)")

    def parse_args(args=None):
        argParser = argparse.ArgumentParser(description="Dsiplay emissions")
        fillOptions(argParser)
        return argParser.parse_args(args), argParser
    
    options, argParser = parse_args()
    df = gpd.read_file(options.emission_file)
    displayGeoDataFrame(df)
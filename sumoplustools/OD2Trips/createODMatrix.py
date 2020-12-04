
import os, sys
import argparse
import sumolib
import numpy as np
import geopandas as gpd
import time
from shapely.geometry import Polygon, Point, MultiLineString
from xml.etree import ElementTree as ET

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sumoplustools import verbose

def fillOptions(argParser):
    argParser.add_argument("-n", "--sumo-net-file", 
                            metavar="FILE", required=True,
                            help="conversion to SUMO coords using FILE (mandatory)")
    argParser.add_argument("-t", "--taz-add-file", 
                            metavar="FILE", required=True,
                            help="gets districts from FILE (mandatory)")
    argParser.add_argument("-od", "--origin-dest-file", 
                            metavar="FILE", required=True,
                            help="OD trip data in FILE that uses geometry column by default (mandatory)")
    argParser.add_argument("-o", "--output-file",
                            metavar="FILE", default="tazMatrix",
                            help="OD matrix is save to FILE")
    argParser.add_argument("--ori-lon", 
                            metavar="STR", type=str,
                            help="OD column that contains the origin's longitude. Uses the geometry column if omitted")
    argParser.add_argument("--ori-lat", 
                            metavar="STR", type=str,
                            help="OD column that contains the origin's latitude. Uses the geometry column if omitted")
    argParser.add_argument("--dest-lon", 
                            metavar="STR", type=str,
                            help="OD column that contains the destination's longitude. Uses the geometry column if omitted")
    argParser.add_argument("--dest-lat", 
                            metavar="STR", type=str,
                            help="OD column that contains the destination's latitude. Uses the geometry column if omitted")
    argParser.add_argument("--time-col", 
                            metavar="STR", type=str,
                            help="column that contains time of departure in seconds")
    argParser.add_argument("--time-format", 
                            metavar="STR", type=str, required='--time-col' in sys.argv,
                            help="format of the time structure. Required if time column is provided. For more information on time format use reference time.strftime")
    argParser.add_argument("--time-field", 
                            metavar="STR", type=str, default="H",
                            help="time field to group entries: (M) min, (H) hour, (D) dayOfWeek")
    argParser.add_argument("--filter", 
                            metavar="STR", type=str,
                            help="filter the OD data in the form 'COL:FILTER[,COL:FILTER]' where COL is the column and FILTER is the regular expression to filter for")
    argParser.add_argument("-v", "--verbose",
                            action="store_true", default=False,
                            help="gives description of current task")

    
def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Create OD matrix files based on OD trips data")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    if options.verbose:
        verbose.addVerboseSteps(["extracting data from SUMO network file", "extracting data from TAZ file", "extracting data from OD matrix"])
        verbose.writeToConsole()

    net = sumolib.net.readNet(options.sumo_net_file)

    if options.verbose:
        verbose.writeToConsole(done=True)

    tazXMLIter = ET.iterparse(options.taz_add_file)
    tazShapes = {}
    tazShapes['taz_id'] = []
    tazShapes['geometry'] = []
    for _, elem in tazXMLIter:
        if elem.tag != "taz":
            continue
        
        taz_id = int(elem.get("id").split("_")[1])
        polygon = []
        for position in elem.get("shape").split():
            x, y = position.split(",")
            x, y = float(x.strip()), float(y.strip())

            lon, lat = net.convertXY2LonLat(x, y)
            polygon += [(lon, lat)]
        tazShapes['taz_id'] += [taz_id]
        tazShapes['geometry'] += [Polygon(polygon)]

        elem.clear()
        del elem
    del tazXMLIter
    
    # Add OD matrices based on time
    tazMatrices = [np.zeros((len(tazShapes['taz_id']),len(tazShapes['taz_id'])))]
    if options.time_col:
        field = options.time_field
        if field.upper().startswith("M"):
            r = 59
            time_format = "%M"
        elif field.upper().startswith("H"):
            r = 23
            time_format = "%H"
        elif field.upper().startswith("D"):
            r = 6
            time_format = "%w"
        else:
            argParser.print_help()
            argParser.error("--time-field given is not valid: use given types")
        for _ in range(r):
            tazMatrices += [np.zeros((len(tazShapes['taz_id']),len(tazShapes['taz_id'])))]
    
    if options.verbose:
        verbose.writeToConsole(done=True)
        v_od_collected = 1

    if (options.ori_lon and options.ori_lat and options.dest_lon and options.dest_lat):
        useGeom = False
    else:
        useGeom = True

    columns = None
    chunksize = 10 * 10**3
    chunk_idx = -1
    while True:
        chunk_idx += 1
        od_data = gpd.read_file(options.origin_dest_file, rows=slice(chunk_idx*chunksize, (chunk_idx+1)*chunksize), message=False)
        if od_data.empty:
            break

        # Filter data
        if options.filter:
            filters = options.filter.split(",")
            for fil in filters:
                args = fil.split(":")
                od_data = od_data.loc[od_data.loc[:,args[0]].str.contains(args[1], regex=True)]
            if od_data.empty:
                continue

        # Convert geometry to geocoordinates
        if useGeom:
            od_data.to_crs(epsg=4326, inplace=True)
        
        if columns is None:
            columns = od_data.columns.tolist()
        
        # Iterate for each row in dataframe
        for row_tuple in od_data.itertuples(index=False):
            if options.time_col:
                timeStr = row_tuple[columns.index(options.time_col)]
                try:
                    dTime = time.strptime(timeStr, options.time_format)
                except ValueError as e:
                    descr = e.args[0]
                    if "bad directive" in descr:
                        continue
                    elif "unconverted" in descr:
                        try:
                            if int(timeStr[:2]) > 23:
                                timeStr = timeStr.replace(timeStr[:2], "%i" % (int(timeStr[:2]) % 24), 1)
                                dTime = time.strptime(timeStr, options.time_format)
                            else:
                                continue
                        except:
                            continue

                matrixIdx = int(time.strftime(time_format, dTime)) % len(tazMatrices)
            else:
                matrixIdx = 0

            toAdd = []
            if useGeom:
                geom = row_tuple.geometry
                if geom.geom_type == 'MultiLineString':
                    for line in geom:
                        toAdd += [(Point(line.coords[0]), Point(line.coords[-1]))]
                elif geom.geom_type == 'LineString':
                    toAdd += [(Point(geom.coords[0]), Point(geom.coords[-1]))]
                else:
                    continue
            else:
                oriLon = float(row_tuple[columns.index(options.ori_lon)])
                oriLat = float(row_tuple[columns.index(options.ori_lat)])
                desLon = float(row_tuple[columns.index(options.dest_lon)])
                desLat = float(row_tuple[columns.index(options.dest_lat)])

                toAdd += [(Point(oriLon, oriLat), Point(desLon, desLat))]

            for points in toAdd:
                oriTAZ_id = None
                desTAZ_id = None
                for taz_id, od_poly in zip(tazShapes['taz_id'],tazShapes['geometry']):
                    if oriTAZ_id and desTAZ_id:
                        break
                    if points[0].within(od_poly):
                        oriTAZ_id = taz_id
                    if points[1].within(od_poly):
                        desTAZ_id = taz_id
                if not (oriTAZ_id and desTAZ_id):
                    continue
                
                tazMatrices[matrixIdx][oriTAZ_id, desTAZ_id] += 1
                if options.verbose:
                    verbose.writeToConsole(verboseValue=v_od_collected)
                    v_od_collected += 1

    if options.verbose:
        verbose.writeToConsole(done=True)

    for idx, tazMatrix in enumerate(tazMatrices):
        np.save("%s_" % os.path.splitext(options.output_file)[0] + ("%i" % idx).zfill(2), tazMatrix)



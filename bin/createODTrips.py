import os, sys
import argparse
import subprocess

def fillOptions(argParser):
    argParser.add_argument("-n", "--net-file", 
                            metavar="FILE", required=True, type=str,
                            help="read SUMO network from FILE (mandatory)")
    argParser.add_argument("-t", "--taz-file", 
                            metavar="FILE", required=True, type=str,
                            help="read the SUMO TAZ additionals from FILE (mandatory)")
    argParser.add_argument("-od", "--od-dir",
                            metavar='DIR', required=True, type=str,
                            help="read all origin destination matrices in the DIR (mandatory)")
    argParser.add_argument("-td", "--trip-dir",
                            metavar='DIR', required=True, type=str,
                            help="save the SUMO trips to DIR (mandatory)")
    argParser.add_argument("-rd", "--route-dir",
                            metavar='DIR', required=True, type=str,
                            help="save the SUMO routes to DIR (mandatory)")
    argParser.add_argument("-p", "--prefix",
                            metavar='STR', required=True, type=str,
                            help="save the SUMO routes with prefix (mandatory)")
    
def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Create trips for buses that have specified routes.")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()
    if not 'SUMO_HOME' in os.environ:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    sumoPlusTools = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sumoplustools')
    sumoTools = os.environ['SUMO_HOME']
    
    # Temp files
    odMatrix = os.path.join(sumoPlusTools, 'OD2Trips', 'OD_matrix.conf.xml')
    edgeTaz = os.path.join(sumoPlusTools, 'OD2Trips', 'taz_edges.taz.xml')


    edges = os.path.join(sumoTools, 'tools', 'edgesindistricts.py')
    updateMatrixConf = os.path.join(sumoPlusTools, 'OD2Trips', 'updateMatrixConf.py')

    createEdgeCmd = 'python %s -n %s -t %s -o %s' % (edges, options.net_file, options.taz_file, edgeTaz)    
    updateMatrixCmd = 'python %s -c %s --od-matrix-dir %s -t %s' % (updateMatrixConf, odMatrix, options.od_dir, edgeTaz)

    print('Creating trips from OD Matrices ...')
    proc = subprocess.Popen(createEdgeCmd)
    proc.wait()
    proc = subprocess.Popen(updateMatrixCmd)
    proc.wait()


    od2Trips = os.path.join(sumoTools, 'bin', 'od2trips.exe')
    addClass = os.path.join(sumoPlusTools, 'OD2Trips', 'addClassToTrips.py')
    validate = os.path.join(sumoPlusTools, 'OD2Trips', 'validateTrips.py')
    
    odTripCmdBase = '%s -c %s -o %s.%%s --scale %%f --vtype "%%s" --prefix "%%s"' % (od2Trips, odMatrix, os.path.join(options.trip_dir, options.prefix))
    addClassCmdBase = 'python %s -od %s.%%s -i "%%s" -v "%%s"' % (addClass, os.path.join(options.trip_dir, options.prefix))
    validateCmdBase = 'python %s -n %s -t %s.%%s -v "%%s"' % (validate, options.net_file, os.path.join(options.trip_dir, options.prefix))

    print('Creating trips for passenger vehicles ...')
    proc = subprocess.Popen(odTripCmdBase % ('passenger.odtrips.xml', 3, 'veh_passenger', 'veh'))
    proc.wait()
    proc = subprocess.Popen(addClassCmdBase % ('passenger.odtrips.xml', 'veh_passenger', 'passenger'))
    proc.wait()
    proc = subprocess.Popen(validateCmdBase % ('passenger.odtrips.xml', 'passenger'))
    proc.wait()

    print('Creating trips for motorcyles ...')
    proc = subprocess.Popen(odTripCmdBase % ('motorcycle.odtrips.xml', 1.5, 'moto_motorcycle', 'moto'))
    proc.wait()
    proc = subprocess.Popen(addClassCmdBase % ('motorcycle.odtrips.xml', 'moto_motorcycle', 'motorcycle'))
    proc.wait()
    proc = subprocess.Popen(validateCmdBase % ('motorcycle.odtrips.xml', 'motorcycle'))
    proc.wait()
    
    print('Creating trips for buses ...')
    proc = subprocess.Popen(odTripCmdBase % ('bus.odtrips.xml', 1, 'bus_bus', 'bus'))
    proc.wait()
    proc = subprocess.Popen(addClassCmdBase % ('bus.odtrips.xml', 'bus_bus', 'bus'))
    proc.wait()
    proc = subprocess.Popen(validateCmdBase % ('bus.odtrips.xml', 'bus'))
    proc.wait()

    print('Creating trips for trucks ...')
    proc = subprocess.Popen(odTripCmdBase % ('truck.odtrips.xml', 0.5, 'truck_truck', 'truck'))
    proc.wait()
    proc = subprocess.Popen(addClassCmdBase % ('truck.odtrips.xml', 'truck_truck', 'truck'))
    proc.wait()
    proc = subprocess.Popen(validateCmdBase % ('truck.odtrips.xml', 'truck'))
    proc.wait()


    duarouter = os.path.join(sumoTools, 'bin', 'duarouter.exe')
    duarouterCmd = '%s -n %s -r %s.%%s.odtrips.xml -o %s.%%s.rou.xml' % (duarouter, options.netFile, os.path.join(options.trip_dir, options.prefix), os.path.join(options.route_dir, options.prefix))

    print('Converting trips to Routes ...')
    proc = subprocess.Popen(duarouterCmd % ('passenger', 'passenger'))
    proc.wait()
    proc = subprocess.Popen(duarouterCmd % ('motorcycle', 'motorcycle'))
    proc.wait()
    proc = subprocess.Popen(duarouterCmd % ('bus', 'bus'))
    proc.wait()
    proc = subprocess.Popen(duarouterCmd % ('truck', 'truck'))
    proc.wait()

    stops = os.path.join(sumoPlusTools, 'StopSigns', 'createStops.py')
    stopCmd = 'python %s -n %s -r %s.%%s.rou.xml -v "%%s"' % (stops, options.net_file, os.path.join(options.route_dir, options.prefix))

    print('Adding stops to Routes ...')
    proc = subprocess.Popen(stopCmd % ('passenger', 'passenger'))
    proc.wait()
    proc = subprocess.Popen(stopCmd % ('motorcycle', 'motorcycle'))
    proc.wait()
    proc = subprocess.Popen(stopCmd % ('bus', 'bus'))
    proc.wait()
    proc = subprocess.Popen(stopCmd % ('truck', 'truck'))
    proc.wait()

    os.remove(odMatrix)
    os.remove(edgeTaz)
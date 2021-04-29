import os, sys
import argparse
import subprocess

def fillOptions(argParser):
    argParser.add_argument("-n", "--net-file", 
                            metavar="FILE", required=True, type=str,
                            help="read SUMO network from FILE (mandatory)")
    argParser.add_argument("-s", "--stop-file", 
                            metavar="FILE", required=True, type=str,
                            help="the bus stop location shape-like file (mandatory)")
    argParser.add_argument("-l", "--line-file",
                            metavar='FILE', required=True, type=str,
                            help="the bus routes shape-like file (mandatory)")
    argParser.add_argument("-so", "--stop-output",
                            metavar='FILE', required=True, type=str,
                            help="save the SUMO bus stop locations to FILE (mandatory)")
    argParser.add_argument("-lo", "--line-output",
                            metavar='FILE', required=True, type=str,
                            help="save the SUMO bus routes to FILE (mandatory)")
    argParser.add_argument("-to", "--trip-output",
                            metavar='FILE', required=True, type=str,
                            help="save the SUMO bus trips to FILE (mandatory)")
    argParser.add_argument("-b", "--num-buses",
                            metavar='INT', required=True, type=int,
                            help="the the number of buses on each bus route (mandatory)")
    argParser.add_argument("-i", "--interval",
                            metavar='INT', required=True, type=int,
                            help="the simulation time difference between two buses on a single line")
    
def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Create trips for buses that have specified routes.")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    sumoPlusTools = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sumoplustools')

    stopCmd = 'python %s -n %s -s %s -o %s -v' % (os.path.join(sumoPlusTools, 'busnetwork', 'createBusStops.py'), options.net_file, options.stop_file, options.stop_output)
    lineCmd = 'python %s -n %s -l %s -s %s -o %s -v' % (os.path.join(sumoPlusTools, 'busnetwork', 'createBusLines.py'), options.net_file, options.line_file, options.stop_output, options.line_output)
    tripCmd = 'python %s -l %s -o %s -n %i -i %i -v' % (os.path.join(sumoPlusTools, 'busnetwork', 'createBusTrips.py'), options.line_output, options.trip_output, options.num_buses, options.interval)

    proc = subprocess.Popen(stopCmd)
    proc.wait()
    
    proc = subprocess.Popen(lineCmd)
    proc.wait()
    
    proc = subprocess.Popen(tripCmd)
    proc.wait()
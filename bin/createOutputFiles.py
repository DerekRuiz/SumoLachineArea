import os, sys
import argparse
import subprocess

def fillOptions(argParser):
    argParser.add_argument("-c", "--cfg-file", 
                            metavar="FILE", required=True,
                            help="read SUMO configuration from FILE (mandatory)")
    argParser.add_argument("-o", "--output-dir", 
                            metavar="DIR", required=True,
                            help="save output files to DIR (mandatory)")
    argParser.add_argument("-e", "--emission",
                            action='store_true', default=True,
                            help="generate emissions output report")
    argParser.add_argument("-f", "--fcd",
                            action='store_true', default=False,
                            help="generate fcd output report")
    argParser.add_argument("-l", "--lanechange",
                            action='store_true', default=False,
                            help="generate lane change output report")
    argParser.add_argument("-v", "--vtk",
                            action='store_true', default=False,
                            help="generate vtk output report")
    
def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Create random trips for all class types in a network. More information at: https://sumo.dlr.de/docs/Tools/Trip.html")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()
    if not 'SUMO_HOME' in os.environ:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    sumo = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo.exe')
    
    if options.emission:
        proc = subprocess.Popen('%s -c %s --emission-output %s' % (sumo, options.cfg_file, os.path.join(options.output_dir, 'traceEmission.xml')))
        proc.wait()

    if options.fcd:
        proc = subprocess.Popen('%s -c %s --fcd-output %s' % (sumo, options.cfg_file, os.path.join(options.output_dir, 'traceVehiclePosition.xml')))
        proc.wait()

    if options.fcd:
        proc = subprocess.Popen('%s -c %s --lanechange-output %s' % (sumo, options.cfg_file, os.path.join(options.output_dir, 'traceLaneChange.xml')))
        proc.wait()

    if options.fcd:
        proc = subprocess.Popen('%s -c %s --vtk-output %s' % (sumo, options.cfg_file, os.path.join(options.output_dir, 'VTK', 'trace_vkt.xml')))
        proc.wait()
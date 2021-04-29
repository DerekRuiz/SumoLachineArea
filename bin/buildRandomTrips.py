import os, sys
import argparse
import subprocess

def fillOptions(argParser):
    argParser.add_argument("-n", "--net-file", 
                            metavar="FILE", required=True,
                            help="read SUMO network from FILE (mandatory)")
    argParser.add_argument("-o", "--output-prefix", 
                            metavar="FILE", required=True,
                            help="save trip files with prefix to FILE (mandatory)")
    argParser.add_argument("-p", "--probablility",
                            metavar='INT', type=int,
                            help="the frequency of trips added. ex: `-p 0.5` a trip is added every 0.5 seconds")
    argParser.add_argument("-b", "--begin",
                            metavar='INT', type=int,
                            help="the simulation time to start inserting trips")
    argParser.add_argument("-e", "--end",
                            metavar='INT', type=int,
                            help="the simulation time to stop inserting trips")
    argParser.add_argument("-s", "--seed",
                            metavar='INT', type=int,
                            help="the seed for psuedo randomess")
    argParser.add_argument("-f", "--fringe-factor",
                            metavar='INT', type=int,
                            help="the probability that a trip starts at an edge with no successor or predecessor (near the edges of the map)")
    
def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Create random trips for all class types in a network. More information at: https://sumo.dlr.de/docs/Tools/Trip.html")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()
    if not 'SUMO_HOME' in os.environ:
        sys.exit("please declare environment variable 'SUMO_HOME'")
    
    sumoTool = os.path.join(os.environ['SUMO_HOME'], 'tools', 'randomTrips.py')
    otherCmds = ''
    if options.probablility:
        otherCmds +='-p %i' % options.probablility
    if options.begin:
        otherCmds += '-b %i ' % options.begin
    if options.end:
        otherCmds +='-e %i' % options.end
    if options.seed:
        otherCmds += '--seed %i ' % options.seed
    if options.fringe_factor:
        otherCmds +='--fringe-factor %i' % options.fringe_factor

    baseCmd = 'python %s -n %s -o %s.%%s.trips.xml %s %%s' % (sumoTool, options.net_file, options.output_prefix, otherCmds)
    
    passengerCmds = ('truck', '--vehicle-class passenger --vclass passenger --prefix veh')
    truckCmds = ('passenger', '--vehicle-class truck --vclass truck --prefix truck')
    motorCmds = ('motorcycle', '--vehicle-class motorcycle --vclass motorcycle --prefix moto')
    busCmds = ('bus', '--vehicle-class bus --vclass bus --prefix bus')
    railCmds = ('rail', '--vehicle-class rail --vclass rail --prefix rail')
    pedestrianCmds = ('pedestrian', '--vehicle-class pedestrian --pedestrian --prefix ped')
    bicycleCmds = ('bicycle', '--vehicle-class bicycle --vclass bicycle --prefix bike')


    sys.stdout.write('Verbose: Creating trips for passenger vehicles ... ')
    sys.stdout.flush()
    proc = subprocess.Popen(baseCmd % passengerCmds)
    proc.wait()
    sys.stdout.write('DONE\n')

    sys.stdout.write('Verbose: Creating trips for truck vehicles ... ')
    sys.stdout.flush()
    proc = subprocess.Popen(baseCmd % truckCmds)
    proc.wait()
    sys.stdout.write('DONE\n')

    sys.stdout.write('Verbose: Creating trips for motorcycle vehicles ... ')
    sys.stdout.flush()
    proc = subprocess.Popen(baseCmd % motorCmds)
    proc.wait()
    sys.stdout.write('DONE\n')

    sys.stdout.write('Verbose: Creating trips for bus vehicles ... ')
    sys.stdout.flush()
    proc = subprocess.Popen(baseCmd % busCmds)
    proc.wait()
    sys.stdout.write('DONE\n')

    sys.stdout.write('Verbose: Creating trips for rail vehicles ... ')
    sys.stdout.flush()
    proc = subprocess.Popen(baseCmd % railCmds)
    proc.wait()
    sys.stdout.write('DONE\n')

    sys.stdout.write('Verbose: Creating trips for pedestrians ... ')
    sys.stdout.flush()
    proc = subprocess.Popen(baseCmd % pedestrianCmds)
    proc.wait()
    sys.stdout.write('DONE\n')

    sys.stdout.write('Verbose: Creating trips for bicycles ... ')
    sys.stdout.flush()
    proc = subprocess.Popen(baseCmd % bicycleCmds)
    proc.wait()
    sys.stdout.write('DONE\n')
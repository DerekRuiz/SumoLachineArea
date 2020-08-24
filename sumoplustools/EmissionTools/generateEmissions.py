import argparse
from EmissionTools import sumoEmission as se


def fillOptions(argParser):
    argParser.add_argument("-osm", "--osm-file", 
                            metavar="FILE", required=True,
                            help="use FILE to create GeoDataFrame to be saved (mandatory)")
    argParser.add_argument("-e", "--emission-file",
                            metavar="FILE",
                            help="use FILE to populate data using XML")
    argParser.add_argument("-c", "--sumo-config-file", 
                            metavar="FILE",
                            help="use FILE to populate data using TraCI")
    argParser.add_argument("-o", "--output-file", 
                            metavar="FILE", required=True,
                            help="write emission dataframes with prefix of FILE (mandatory)")
    argParser.add_argument("-t", "--emission-types", 
                            type=str, metavar='STR[,STR]*', required=True,
                            help="the emission types that will be collected and saved. Seperate types with a comma (mandatory)")
    argParser.add_argument("-s", "--start-time",
                            metavar='INT[-INT-INT]',
                            help="initial time that data is collected from. Can be in seconds or with format of 'hr-min-sec'. Starts at begining if omitted")
    argParser.add_argument("-f", "--finish-time",
                            metavar='INT[-INT-INT]',
                            help="last time that data is collected from. Can be in seconds or with format of 'hr-min-sec'. Terminates 1 second after start if omitted")
    argParser.add_argument("-d", "--duration",
                            metavar='INT[-INT-INT]',
                            help="amount of time that data is collected from. Can be in seconds or with format of 'hr-min-sec'. Terminates after 1 second has elapsed if omitted. Has priority over --finish-time")
    argParser.add_argument("-g", "--go-to-end",
                            action='store_true', dest='toEnd', default=False,
                            help="collect data until the end of file or simulation. Has priority over --duration")
    argParser.add_argument("-i", "--time-interval",
                            metavar='INT[-INT-INT]',
                            help="the number of step in an interval. Can be in seconds or with format of 'hr-min-sec'. Interval of total runtime if omitted")


def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Generate emissions and save them to a Geo Package file")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    # Set OSM file
    se.createStreetsDF(options.osm_file)

    # Set emission types
    eTypes = options.emission_types.split(",")

    # Set data file to populate dataframe
    if options.emission_file:
        try:
            se.checkEmissionFile()
        except Exception:
            se.setEmissionFile(options.emission_file)
        useFile = True
    elif options.sumo_config_file:
        se.setSumocfgFile(options.sumo_config_file)
        useFile = False
    else:
        raise Exception("No --emission-file or --sumo-config-file was provided. One or the other must be set to populate data.")

    # Defaults
    fromTime = -1
    toTime = -1
    duration = 1
    useDuration = False
    timeInterval = 0


    # Set start time
    if options.start_time:
        try:
            fromTime = int(options.start_time)
        except ValueError:
            try:
                split = options.start_time.split('-')
                fromTime = (int(split[0]) * 3600) + (int(split[1]) * 60) + int(split[2])
            except IndexError:
                raise Exception("--start-time is not in the correct format")

    # Set end time
    # Using to end
    if options.toEnd:
        pass
    # Using duration
    elif options.duration:
        try:
            duration = int(options.duration)
        except ValueError:
            try:
                split = options.duration.split('-')
                duration = (int(split[0]) * 3600) + (int(split[1]) * 60) + int(split[2])
            except IndexError:
                raise Exception("--duration is not in the correct format")
        useDuration = True
    # Using finish time
    elif options.finish_time:
        try:
            toTime = int(options.finish_time)
        except ValueError:
            try:
                split = options.finish_time.split('-')
                toTime = (int(split[0]) * 3600) + (int(split[1]) * 60) + int(split[2])
            except IndexError:
                raise Exception("--finish-time is not in the correct format")

        
    # Set time interval
    if options.time_interval:
        try:
            timeInterval = int(options.time_interval)
        except ValueError:
            try:
                split = options.time_interval.split('-')
                timeInterval = (int(split[0]) * 3600) + (int(split[1]) * 60) + int(split[2])
            except IndexError:
                raise Exception("--time-interval is not in the correct format")


    se.collectEmissions(filepath=options.output_file, eTypes=eTypes, fromStep=fromTime, toStep=toTime, timeInterval=timeInterval, useDuration=useDuration, duration=duration, toEnd=options.toEnd, useFile=useFile)
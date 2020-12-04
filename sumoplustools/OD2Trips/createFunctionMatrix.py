import os,sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
from statistics import mean
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import math
import warnings

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sumoplustools import verbose


# createFunctionMatrix.py --matrices Montreal/ODdata --prefix "mtl_hour,qc_18_hour" --extension ".npy" --output-file Montreal/ODFunctions/hour_function --verbose
# createFunctionMatrix.py --matrices Montreal/ODdata --prefix "mtl_wday" --extension ".npy" --output-file Montreal/ODFunctions/wday_function --verbose

def getNumberOfTrips(functionMatrix, origin: int, destination: int, time: float) -> float:
    model = functionMatrix[origin, destination]
    values = np.array([time]).reshape((-1,1))
    pred = PolynomialFeatures(degree=len(model.coef_) - 1).fit_transform(values)
    return np.round(np.array(model.predict(pred)),decimals=2)[0]
    
def displayTrips(functionMatrix, origin: int, destination: int, timeRange: np.ndarray):
    model = functionMatrix[origin, destination]
    x = timeRange
    y = model.predict(PolynomialFeatures(degree=len(model.coef_) - 1).fit_transform(timeRange.reshape((-1,1))))
    plt.plot(x, y, color='blue')
    plt.show()


def fillOptions(argParser):
    argParser.add_argument("-m", "--matrices", 
                            metavar="DIR", required=True,
                            help="all OD matrices are located within DIR (mandatory)")
    argParser.add_argument("-p", "--prefix", 
                            metavar="STR[,STR]", default="",
                            help="processes only matrices with the prefix. If multiple prefixes provided, then the files are group by prefix then combined appropriately. Any prefix must filter the exact same number of files as all other prefixes")
    argParser.add_argument("-e", "--extension", 
                            metavar="FILE", default=".npy",
                            help="processes only matrices with the extension")
    argParser.add_argument("-o", "--output-file",
                            metavar="FILE",
                            help="function matrix is save to FILE. If not provided it is saved to the matrices directory under function.npy")
    argParser.add_argument("-v", "--verbose",
                            action="store_true", default=False,
                            help="gives description of current task")

    
def parse_args(args=None):
    argParser = argparse.ArgumentParser(description="Create function matrix based on OD matrices data. Each entry in the matrix is the coefficient of the ")
    fillOptions(argParser)
    return argParser.parse_args(args), argParser


if __name__ == "__main__":
    options, argParser = parse_args()

    if options.verbose:
        verbose.addVerboseSteps(["extracting files from directory", "combining matrices of different prefixes", "computing function for matrix", "writing to file"])
        verbose.writeToConsole()

    folder = options.matrices
    prefixes = options.prefix.split(",")
    
    combinedMatricesPerTime = None
    matricesPerPrefix = []
    for prefix in prefixes:
        files = [folder + os.sep + f for f in os.listdir(folder) if prefix in f[0:len(prefix)] and options.extension in f[-len(options.extension):]]
        if len(files) == 0:
            warnings.warn('No files loaded from folder "%s", with prefix "%s" and extension "%s"\n Skipping this prefix' % (folder, prefix, options.extension))
            continue
        matricesPerTime = [np.load(f) for f in files]
        matricesPerPrefix += [matricesPerTime]
        if combinedMatricesPerTime is None:
            combinedMatricesPerTime = [np.zeros(odMatrix.shape) for odMatrix in matricesPerTime]
    
    if len(matricesPerPrefix) == 0:
        warnings.warn('No matrices loaded from folder "%s"\n Terminating process' % (folder))
        exit()
    
    if options.verbose:
        verbose.writeToConsole(done=True)
    
    for matricesPerTime in matricesPerPrefix:
        for t in range(len(matricesPerTime)):
            combinedMatricesPerTime[t] += matricesPerTime[t]
    #for matrix in combinedMatricesPerTime:
    #    matrix = matrix / float(len(matricesPerPrefix))
    
    if options.verbose:
        verbose.writeToConsole(done=True)

    xs = np.array(list(range(len(combinedMatricesPerTime)))).reshape((-1,1))
    xs = PolynomialFeatures(degree=len(xs) - 1).fit_transform(xs)

    function = np.zeros((combinedMatricesPerTime[0].shape[0], combinedMatricesPerTime[0].shape[1]), dtype='O')
    for i in range(combinedMatricesPerTime[0].shape[0]):
        for j in range(combinedMatricesPerTime[0].shape[1]):
            data = []
            for time in range(len(combinedMatricesPerTime)):
                data += [combinedMatricesPerTime[time][i,j]]
            if (i == 13 and j == 13):
                print(data)
            data = np.array(data) + 1
            model = LinearRegression().fit(xs, data)
            function[i,j] = model

            if options.verbose:
                completedCoords = (i,j)
                verbose.writeToConsole(verboseValue=completedCoords)

    if options.verbose:
        verbose.writeToConsole(done=True)

    if options.output_file:
        output = options.output_file
    else:
        output = folder + os.sep + "function"

    np.save(output, function)
    
    if options.verbose:
        verbose.writeToConsole(done=True)
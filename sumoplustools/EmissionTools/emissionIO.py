import geopandas as gpd
import os
import numpy as np
import shutil

_TEMP_FOLDER = "temp"
_EMISION_FOLDER = "splitEmission"

def saveDataFrame(dataFrame, filepath):
    """
    Saves the dataFrame to a GeoPackage file.
    Some data may be altered to properly save to GeoPackage format
    Use function loadDataFrame() to reverse the format change
    """
    gdf = dataFrame.copy()
    for col in gdf.columns:
        if col == 'geometry':
            break
        gdf[col] = gdf[col].astype(str)
        if gdf[col].str.contains(",").any():
            gdf[col] = gdf[col].apply(lambda x: str(x).replace("[","").replace("]","").replace(", "," ;-; ") if "," in str(x) else x)
    
    if not '.gpkg' in filepath:
        filepath += '.gpkg'
    gdf.to_file(filepath, driver="GPKG")

def loadDataFrame(filepath):
    """
    loadDataFrame() -> GeoDataFrame
    Return a GeoDataFrame from a GeoPackage file
    """
    if not '.gpkg' in filepath:
        filepath += '.gpkg'
    gdf = gpd.read_file(filepath)
    
    for col in gdf.columns:
        if col == 'geometry':
            break
        gdf[col] = gdf[col].apply(lambda x: x.split(" ;-; ") if ";-;" in str(x) else x)

    return gdf

def createProjectTempFolder():
    if not os.path.exists(_TEMP_FOLDER):
        os.makedirs(_TEMP_FOLDER)

def removeProjectTempFolder():
    if os.path.exists(_TEMP_FOLDER):
        shutil.rmtree(_TEMP_FOLDER)

def getFilesInTemp(prefix=None):
    if not os.path.exists(_TEMP_FOLDER):
        return []
    if prefix is None:
        return os.listdir(_TEMP_FOLDER)
    else:
        return [f for f in os.listdir(_TEMP_FOLDER) if prefix in f]

def saveNumpyArray(npArray, filename):
    createProjectTempFolder()
    
    np.save(os.path.join(_TEMP_FOLDER, filename), npArray)

def loadNumpyArray(filename):
    if not os.path.exists(_TEMP_FOLDER):
        raise OSError("No numpy arrays created yet")
    elif not os.path.exists(os.path.join(_TEMP_FOLDER, filename)):
        filename += ".npy"
    if not os.path.exists(os.path.join(_TEMP_FOLDER, filename)):
        raise OSError('Numpy file "' + os.path.abspath(os.path.join(_TEMP_FOLDER, filename)) + '" does not exists')
    
    return np.load(os.path.join(_TEMP_FOLDER, filename))

def createEmissionFolder():
    if not os.path.exists(_EMISION_FOLDER):
        os.makedirs(_EMISION_FOLDER)

def splitEmissionFile(filepath):
    createEmissionFolder()
    filename = os.path.splitext(os.path.basename(filepath))[0]
    index = 0
    try:
        f = open(filepath, "r")
        nf = open(os.path.join(_EMISION_FOLDER, filename + "_" + str(index) + ".xml"), "w")
        nf_path = os.path.abspath(nf.name)
        line = f.readline()
        while line:
            nf.write(line)
            if os.path.getsize(os.path.abspath(nf.name)) > (2**27) and "</timestep>" in line:
                nf.write("</emission-export>")
                index += 1
                nf.close()
                nf = open(os.path.join(_EMISION_FOLDER, filename + "_" + str(index) + ".xml"), "w")
                nf.write("<emission-export>\n")
            line = f.readline()
    finally:
        f.close()
        nf.close()
    return nf_path

def getNextEmissionFile(filepath, index):
    filename = os.path.splitext(os.path.basename(filepath))[0]
    if not os.path.exists(os.path.join(_EMISION_FOLDER, filename + "_" + str(index) + ".xml")):
        raise OSError("No next emission file at: %s" %  os.path.join(_EMISION_FOLDER, filename + "_" + str(index) + ".xml"))
    
    return os.path.join(_EMISION_FOLDER, filename + "_" + str(index) + ".xml")

def validateEmissionFileSize(filepath):
    """
    Determines if the emission file can be parsed in with Element tree based on its size.
    Returns True if size is within the threshold of the limit, False otherwise
    """
    return os.path.getsize(os.path.abspath(filepath)) < (2**28)

def getLastEmissionFile(filepath):
    filename = os.path.splitext(os.path.basename(filepath))[0]
    for index in range(len(os.listdir(_EMISION_FOLDER)) + 1):
        f = os.path.join(_EMISION_FOLDER, filename + "_" + str(index) + ".xml")
        if not os.path.exists(f):
            return os.path.join(_EMISION_FOLDER, filename + "_" + str(index) + ".xml")

def getFirstEmissionFile(filepath):
    filename = os.path.splitext(os.path.basename(filepath))[0]
    return os.path.join(_EMISION_FOLDER, filename + "_" + str(0) + ".xml")
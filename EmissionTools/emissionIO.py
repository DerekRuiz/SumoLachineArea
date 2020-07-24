import geopandas as gpd
import os
import numpy as np
import shutil

_TEMP_FOLDER = "temp/"

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
    
    np.save(_TEMP_FOLDER + filename, npArray)

def loadNumpyArray(filename):
    if not os.path.exists(_TEMP_FOLDER):
        raise OSError("No numpy arrays created yet")
    elif not os.path.exists(_TEMP_FOLDER + filename):
        filename += ".npy"
    if not os.path.exists(_TEMP_FOLDER + filename):
        raise OSError('Numpy file "' + os.path.abspath(_TEMP_FOLDER + filename) + '" does not exists')
    
    return np.load(_TEMP_FOLDER + filename)

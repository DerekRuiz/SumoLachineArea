import math
import matplotlib.pyplot as plt
from shapely.geometry import polygon
import gc
import sumoEmission as se
import rasterio

def createFigure(all=True, fuel=False, CO2=False, CO=False, HC=False, NOx=False, PMx=False):
    """
    Uses the streets GeoDataFrame to create a pyplot figure containing the emissions.
    To display or save the image, use showFigure() or saveFigure() methods.
    """
    streets_gdf = se.getStreetDF()

    emissions = []
    if all:
        emissions = ['fuel','CO2','CO','HC','NOx','PMx']
    else:
        if fuel:
            emissions += ['fuel']
        if CO2:
            emissions += ['CO2']
        if CO:
            emissions += ['CO']
        if HC:
            emissions += ['HC']
        if NOx:
            emissions += ['NOx']
        if PMx:
            emissions += ['PMx']
    
    if len(emissions) == 0:
        raise Warning("Cannot create a figure with no categories.")
        
    l = math.floor(math.sqrt(len(emissions)))
    w = math.ceil(len(emissions) / l)

    coords = [(x, y) for x in range(l) for y in range(w)]
    plt.cla()
    plt.clf()
    plt.close("all")
    gc.collect()

    topLat, topLon = 45.448347, -73.655078
    bottomLat, bottomLon = 45.432745, -73.709244
    zoom_area = polygon.Polygon([[topLon, topLat], [topLon, bottomLat], [bottomLon, bottomLat], [bottomLon, topLat], [topLon, topLat]])
    streets_gdf_zoom = streets_gdf[streets_gdf['geometry'].within(zoom_area)]
    
    _, axs = plt.subplots(l, w)
    for ax, col in zip(coords, emissions):
        if l == 1 and w == 1:
            streets_gdf_zoom.plot(column=col, ax=axs, legend=True, linewidth=(2 * streets_gdf_zoom[col] / streets_gdf_zoom[col].max()) + 0.02)
            axs.set_title('%s Emissions' % (col[0].upper() + col[1:]))
        elif l == 1:
            streets_gdf_zoom.plot(column=col, ax=axs[ax[1]], legend=True, linewidth=(2 * streets_gdf_zoom[col] / streets_gdf_zoom[col].max()) + 0.02)
            axs[ax[1]].set_title('%s Emissions' % (col[0].upper() + col[1:]))
        else :
            streets_gdf_zoom.plot(column=col, ax=axs[ax[0],ax[1]], legend=True, linewidth=(2 * streets_gdf_zoom[col] / streets_gdf_zoom[col].max()) + 0.02)
            axs[ax[0],ax[1]].set_title('%s Emissions' % (col[0].upper() + col[1:]))



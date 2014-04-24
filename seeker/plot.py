import matplotlib.pyplot as plt
import numpy as np
from descartes import PolygonPatch

def show(fig):
    plt.axis('off')
    fig.canvas.draw()

def setLims(ax):
    ax.set_xlim((-122.40800, -122.40349))
    ax.set_ylim((37.7970, 37.8000))

def plotBackgroundMap(ax, filename = "data/beatnik_map.png"):
    setLims(ax)
    left, right = ax.get_xlim()
    bottom, top = ax.get_ylim()
    img = plt.imread(filename)
    ax.imshow(img, extent = [left, right, bottom, top], zorder = 0, alpha=0.8)
    
def plotGeofences(ax, geofences):
    for gf in geofences:
        circ = plt.Circle((gf.location.lon, gf.location.lat), radius=gf.radius,
                          color='red', fill=True, alpha=0.3, lw=3, zorder=2)
        ax.add_patch(circ)

def plotPathLines(ax, paths):
    for path in paths:
        plotLocations(ax, path, color='red', marker='s', mfc='yellow', ms=3,
                      ls='-')

def plotPathPoly(ax, pathPoly):
    patch = PolygonPatch(pathPoly, fc='blue', ec='blue', alpha=0.1, zorder=1)
    ax.add_patch(patch)

def plotUserLocations(ax, locations, status=None):
    if status is None:
        return plotLocations(ax, locations, color="black", marker='o', ms=5, ls='')
    else:
        pass # TODO if status is array, color pts by status
#        colorDict = {None:"black", "stopped":"red"}

def plotLocations(ax, locations, **kwargs):
    xTup, yTup = zip(*[(loc.lon, loc.lat) for loc in locations])
    return ax.plot(xTup, yTup, **kwargs)

def setupRunPlot(sim, figsize=None):
    plt.ion()
    if figsize is not None:
        fig = plt.figure(figsize=figsize)
    else:
        fig = plt.figure()
    ax = fig.add_subplot(111)
    plotBackgroundMap(ax, filename="seeker/data/beatnik_map.png")
    plotGeofences(ax, sim.gfList)
    plotPathLines(ax, sim.pathDict.values())
    plotPathPoly(ax, sim.pathMLSPoly)

    return (fig, ax)

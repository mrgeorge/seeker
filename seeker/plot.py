import matplotlib.pyplot as plt
import numpy as np

def show():
    setLims()
    plt.show()

def setLims():
    plt.xlim((-122.40800, -122.40349))
    plt.ylim((37.7970, 37.8000))

def plotBackgroundMap(filename = "data/beatnik_map.png"):
    setLims()
    left, right = plt.xlim()
    bottom, top = plt.ylim()
    img = plt.imread(filename)
    plt.imshow(img, extent = [left, right, bottom, top], zorder = 0, alpha=0.8)
    
def plotGeofences(geofences):
    for gf in geofences:
        circ = plt.Circle((gf.location.lon, gf.location.lat), radius=gf.radius,
                          color='red', fill=True, alpha=0.1, lw=3)
        ax = plt.gca()
        ax.add_patch(circ)

def plotPaths(paths):
    for path in paths:
        plotLocations(path, color='red', ls='-')

def plotLocations(locations, **kwargs):
    xTup, yTup = zip(*[(loc.lon, loc.lat) for loc in locations])
    plt.plot(xTup, yTup, **kwargs)

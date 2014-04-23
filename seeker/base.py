from shapely.geometry import asMultiLineString, asPoint
import random
import time

accuracyFactor = 1.e-5

class Location(object):
    def __init__(self, t, lat, lon, accuracy, bearing):
        self.t = t
        self.lat = lat
        self.lon = lon
        self.accuracy = accuracy
        self.bearing = bearing

class User(object):
    def __init__(self, location, trueLocation):
        self.locations = [location]
        self._trueLocations = [trueLocation]
        self.waypoints = []
        self.status = "start"

    def _getLatestTrueLocation(self):
        return self._trueLocations[-1]

    def _updateLocation(self, location):
        self.locations.append(location)

    def _updateTrueLocation(self, trueLocation):
        self._trueLocations.append(trueLocation)

    def sampleLocation(self, t, accuracy):
        pass

class Geofence(object):
    def __init__(self, location, description, radius = 1.e-4):
        self.location = location
        self.description = description
        self.radius = radius

    def isLocationInFence(self, location):
        pass

class Simulator(object):
    def __init__(self, numUsers = 20):
        self.gfDict = {}
        self.pathDict = {}
        self.numUsers = numUsers
        self.userDict = {}
        self.tStart = time.localtime()

    @property
    def lastLocations(self):
        return [user.locations[-1] for user in self.userDict.values()]

    @property
    def lastTrueLocations(self):
        return [user._trueLocations[-1] for user in self.userDict.values()]

    def createUserDict(self):
        userIDs = range(self.numUsers)
        locations, trueLocations = self.getInitialUserLocations(self.tStart)
        for uid, loc, trueLoc in zip(userIDs, locations, trueLocations):
            self.userDict[uid] = User(loc, trueLoc)

    def getInitialUserLocations(self, tStart, accuracy=10):
        """Place users uniformly within self.pathMLSPoly with Monte Carlo"""

        try:
            minLon, minLat, maxLon, maxLat = self.pathMLSPoly.bounds
        except AttributeError:
            self.setupPathGeom()

        numAssigned = 0
        locations = []
        trueLocations = []
        while numAssigned < self.numUsers:
            lat = random.random() * (maxLat-minLat) + minLat
            lon = random.random() * (maxLon-minLon) + minLon
            pt = asPoint((lon, lat))
            if self.pathMLSPoly.contains(pt):
                bearing = random.random() * 360.
                trueLocations.append(Location(tStart, lat, lon, accuracy,
                                              bearing))

                latOffset = random.random() * accuracy * accuracyFactor
                lonOffset = random.random() * accuracy * accuracyFactor
                locations.append(Location(tStart, lat+latOffset, lon+lonOffset,
                                          accuracy, bearing))
                numAssigned += 1
        return (locations, trueLocations)

    def updateUsers(self):
        pass

    def createGFDict(self, filename = "data/beatnik_geofences.dat"):
        with open(filename, 'r') as f:
            for line in f.readlines():
                if line[0] in ('\n', '#', '%'): # skip commented or empty lines
                    continue

                ID, latitude, longitude, description = line.split(', ')
                ID = int(ID)
                latitude = float(latitude)
                longitude = float(longitude)
                location = Location(None, latitude, longitude, None, None)
                self.gfDict[ID] = (Geofence(location, description))

    def createPathDict(self, filename = "data/beatnik_paths.dat"):
        with open(filename, 'r') as f:
            for line in f.readlines():
                if line[0] in ('\n', '#', '%'): # skip commented or empty lines
                    continue

                IDStart, IDEnd, pathSequence, latitude, longitude = \
                  line.split(', ')
                IDStart = int(IDStart)
                IDEnd = int(IDEnd)
                latitude = float(latitude)
                longitude = float(longitude)
                key = (IDStart, IDEnd)
                location = Location(None, latitude, longitude, None, None)
                if key not in self.pathDict:
                    self.pathDict[key] = [location]
                else:
                    self.pathDict[key].append(location)

    def setupPathGeom(self, pathBuffer = 1.e-4):
        try:
            paths = self.pathDict.values()
        except AttributeError:
            self.createPathDict()
        nPaths = len(paths)
        self.pathMLS = asMultiLineString([[(loc.lon, loc.lat) for loc in path] \
                                     for path in paths])
        self.pathMLSPoly = self.pathMLS.buffer(pathBuffer)

    def run(self, tStart, tEnd):
        pass

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

    def createUsers(self):
        pass

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

    def run(self, tStart, tEnd):
        pass

import random
import math
import matplotlib.pyplot as plt
from operator import itemgetter
from datetime import datetime, timedelta

from shapely.geometry import asMultiLineString, asLineString, asPoint

import plot

accuracyFactor = 1.e-5
speedFactor = 1.e-5

class Location(object):
    def __init__(self, t, lat, lon, accuracy, bearing):
        self.t = t
        self.lat = lat
        self.lon = lon
        self.accuracy = accuracy
        self.bearing = bearing

    def distance(self, loc):
        """Return Euclidean distance to other Location loc"""
        return pow((self.lon - loc.lon)**2 + (self.lat - loc.lat)**2, 0.5)

class User(object):
    def __init__(self, location, trueLocation):
        self.locations = [location]
        self._trueLocations = [trueLocation]
        self.status = "start"
        self.speed = 0.3
        self.accuracy = 10.

    def _getLatestTrueLocation(self):
        return self._trueLocations[-1]

    def _updateLocation(self, location):
        self.locations.append(location)

    def _updateTrueLocation(self, trueLocation):
        self._trueLocations.append(trueLocation)

class Geofence(object):
    def __init__(self, ID, location, description, radius = 1.e-4):
        self.ID = ID
        self.location = location
        self.description = description
        self.radius = radius

    def isLocationInFence(self, location):
        pass

class Simulator(object):
    """Simulator class keeps track of waypoints, paths, and users"""

    def __init__(self, numUsers, gfFilename, pathFilename, dtStart, dtEnd,
                 dtDelta):

        self.numUsers = numUsers
        self.gfFilename = gfFilename
        self.pathFilename = pathFilename
        self.gfList = []
        self.pathDict = {}
        self.userDict = {}
        self.dtStart = dtStart
        self.dtEnd = dtEnd
        self.dtDelta = dtDelta

        self.createGFList()
        self.createPathDict()
        self.setupPathGeom()
        self.createUserDict()

    @property
    def lastLocations(self):
        return [user.locations[-1] for user in self.userDict.values()]

    @property
    def lastTrueLocations(self):
        return [user._trueLocations[-1] for user in self.userDict.values()]

    def createUserDict(self):
        """Create dict with {uid: User} pairs and initialize User locations"""

        userIDs = range(self.numUsers)
        locations, trueLocations = self.getInitialUserLocations(self.dtStart)
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

    def createGFList(self):
        """Create dict with {ID: Geofence} pairs read from self.gfFilename"""

        with open(self.gfFilename, 'r') as f:
            for line in f.readlines():
                if line[0] in ('\n', '#', '%'): # skip commented or empty lines
                    continue

                ID, latitude, longitude, description = line.split(', ')
                ID = int(ID)
                latitude = float(latitude)
                longitude = float(longitude)
                location = Location(None, latitude, longitude, None, None)
                self.gfList.append(Geofence(ID, location, description))

    def createPathDict(self):
        """Create dict with {(a, b): [Location]} pairs from self.pathFilename"""

        with open(self.pathFilename, 'r') as f:
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
        """Generate shapely MultiLineString and Polyon from list of paths

        Inputs:
            pathBuffer - float, radius around path lines polygon area (degrees)
        """

        try:
            paths = self.pathDict.values()
        except AttributeError:
            self.createPathDict()
        nPaths = len(paths)
        self.pathMLS = asMultiLineString([[(loc.lon, loc.lat) for loc in path] \
                                     for path in paths])
        self.pathMLSPoly = self.pathMLS.buffer(pathBuffer)

    def getNearestGeofence(self, userID, trueLoc=False):
        """Return index in self.gfList for nearest geofence"""
        distList = self.getDistancesToGeofences(userID, trueLoc=trueLoc)
        return min(enumerate(distList), key=itemgetter(1))[0]

    def getDistancesToGeofences(self, userID, trueLoc=False):
        if trueLoc:
            distList = [self.userDict[userID]._trueLocations[-1].distance(gf.location)\
                        for gf in self.gfList]
        else:
            distList = [self.userDict[userID].locations[-1].distance(gf.location)\
                        for gf in self.gfList]

        return distList

    def getCurrentPathID(self, userID, trueLoc=False):
        """Get ID of user's current path

        Input:
            userID
        Returns:
            pathID - tuple (lastGF, nextGF) used to index self.pathDict
        """

        try:
            lastGFIndex = self.userDict[userID].lastGeofenceIndex
            if lastGFIndex == (len(self.gfList) - 1): # user has finished
                return None
        except AttributeError: # lastGeofence hasn't been assigned, try nearest
            lastGFIndex = self.getNearestGeofence(userID, trueLoc=trueLoc)
            self.userDict[userID].lastGeofenceIndex = lastGFIndex
            if lastGFIndex == (len(self.gfList) - 1): # on initialization,
                                                      # assume user hasn't
                                                      # finished
                lastGFIndex -= 1


        nextGFIndex = lastGFIndex + 1
        lastGFID = self.gfList[lastGFIndex].ID
        nextGFID = self.gfList[nextGFIndex].ID
        pathID = (lastGFID, nextGFID)

        return pathID

    def getNextPathID(self, userID):
        currPathID = self.getCurrentPathID(userID)
        if (currPathID is None) or (currPathID[1] == self.gfList[-1].ID):
            return None

        nextPathStartGFIndex = self.gfList.index(currPathID[1])
        nextPathEndGFIndex = nextPathStartGFIndex + 1
        nextPathID = (currPathID[1], self.gfList[nextPathEndGFIndex].ID)

        return nextPathID

    def getDistancesToWaypoints(self, userID, pathID, trueLoc=False):
        if trueLoc:
            distList = [self.userDict[userID]._trueLocations[-1].distance(wp) \
                        for wp in self.pathDict[pathID]]
        else:
            distList = [self.userDict[userID].locations[-1].distance(wp) \
                        for wp in self.pathDict[pathID]]

        return distList

    def getNearestWaypoint(self, userID, pathID, trueLoc=False):
        distList = self.getDistancesToWaypoints(userID, pathID, trueLoc=trueLoc)
        return min(enumerate(distList), key=itemgetter(1))[0]

    def getLastWaypoint(self, userID, pathID, trueLoc=False):
        try:
            return self.userDict[userID].lastWaypoint
        except:
            lastWP = self.getNearestWaypoint(userID, pathID, trueLoc=trueLoc)
            path = self.pathDict[pathID]
            if lastWP == (len(path) - 1): # on initialization, assume user
                                          # hasn't finished
                lastWP -= 1
            self.lastWaypoint = lastWP
            return lastWP

    def getNextWaypointLocation(self, userID, pathID, trueLoc=False):
        lastWP = self.getLastWaypoint(userID, pathID, trueLoc=trueLoc)
        path = self.pathDict[pathID]
        if lastWP == (len(path) - 1): # start next path
            nextPathID = self.getNextPathID(userID)
            if nextPathID is None:
                return None
            nextWPLoc = self.pathDict[nextPathID][0]
        else:
            nextWPLoc = self.pathDict[pathID][lastWP+1]

        return nextWPLoc

    def getUserMovements(self, userID):
        pathID = self.getCurrentPathID(userID, trueLoc=True)
        if pathID is None: # user has finished
            return None

        nextWPLoc = self.getNextWaypointLocation(userID, pathID, trueLoc=True)
        if nextWPLoc is None: # user has finished
            return None

        user = self.userDict[userID]
        currTrueLoc = user._trueLocations[-1]
        movementPath = asLineString(((currTrueLoc.lon, currTrueLoc.lat),
                                     (nextWPLoc.lon, nextWPLoc.lat)))

        stepDistance = user.speed * speedFactor * self.dtDelta.total_seconds()
        nextPt = movementPath.interpolate(stepDistance)
        nextTrueLon, nextTrueLat = (nextPt.x, nextPt.y)
        nextBearing = math.atan2(nextTrueLat - currTrueLoc.lat,
                                 nextTrueLon - currTrueLoc.lon)

        return (nextTrueLat, nextTrueLon, nextBearing)

    def updateUserLocations(self, userID, dt):

        nextCoords = self.getUserMovements(userID)
        if nextCoords is None:
            return False # error code for user to be removed

        lat, lon, bearing = nextCoords
        user = self.userDict[userID]
        user._trueLocations.append(Location(dt, lat, lon, user.accuracy,
                                            bearing))

        latOffset = random.random() * user.accuracy * accuracyFactor
        lonOffset = random.random() * user.accuracy * accuracyFactor
        user.locations.append(Location(dt, lat+latOffset, lon+lonOffset,
                                       user.accuracy, bearing))
        return True

    def assignUserStatuses(self, locUpdate):
        pass

    def run(self, showPlot=True, showTrueLoc=False):
        """Run Simulator by iterating through time steps

        Inputs:
        run calls several other methods to get each user's behavior, update
        their positions, and assign their statuses.
        """

        nSteps = int((self.dtEnd - self.dtStart).total_seconds() /
                     self.dtDelta.total_seconds())
        for ii in xrange(nSteps):
            dt = self.dtStart + ii*self.dtDelta
            for userID in self.userDict.keys():
                self.getUserMovements(userID)
                locUpdate = self.updateUserLocations(userID, dt)
                self.assignUserStatuses(locUpdate)

            if showPlot:
                if ii==0:
                    fig, ax = plot.setupRunPlot(self)
                    if showTrueLoc:
                        locs, = plot.plotUserLocations(ax,
                                                       self.lastTrueLocations)
                    else:
                        locs, = plot.plotUserLocations(ax, self.lastLocations)
                else:
                    if showTrueLoc:
                        locs.set_xdata([loc.lon for loc in \
                                        self.lastTrueLocations])
                        locs.set_ydata([loc.lat for loc in \
                                        self.lastTrueLocations])
                    else:
                        locs.set_xdata([loc.lon for loc in \
                                        self.lastLocations])
                        locs.set_ydata([loc.lat for loc in \
                                        self.lastLocations])
                ax.set_title(dt)
                plot.show(fig)

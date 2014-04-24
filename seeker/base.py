import random
import math
import matplotlib.pyplot as plt
from operator import itemgetter
from datetime import datetime, timedelta

from shapely.geometry import asLineString, asPoint

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

    def __str__(self):
        return "Location({}, {}, {}, {}, {})".format(self.t, self.lat, self.lon,
                                                    self.accuracy, self.bearing)

    def distance(self, loc):
        """Return Euclidean distance to other Location loc"""
        return pow((self.lon - loc.lon)**2 + (self.lat - loc.lat)**2, 0.5)

    @property
    def asPoint(self):
        return asPoint((self.lon, self.lat))

class User(object):
    def __init__(self, location, trueLocation):
        self.locations = [location]
        self._trueLocations = [trueLocation]
        self.status = "start"
        self.speed = 1.
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
        self.pathList = []
        self.userDict = {}
        self.dtStart = dtStart
        self.dtEnd = dtEnd
        self.dtDelta = dtDelta

        self.createGFList()
        self.createPathList()
        self.setupPathGeom()
        self.setGFDistances()
        self.createUserDict()

    @property
    def prevLocations(self):
        return [user.locations[-1] for user in self.userDict.values()]

    @property
    def prevTrueLocations(self):
        return [user._trueLocations[-1] for user in self.userDict.values()]

    def createUserDict(self):
        """Create dict with {uid: User} pairs and initialize User locations"""

        userIDs = range(self.numUsers)
        locations, trueLocations = self.createInitialUserLocations(self.dtStart)
        for uid, loc, trueLoc in zip(userIDs, locations, trueLocations):
            self.userDict[uid] = User(loc, trueLoc)

    def createInitialUserLocations(self, tStart, accuracy=10):
        """Place users uniformly within self.fulPathPoly with Monte Carlo"""

        try:
            minLon, minLat, maxLon, maxLat = self.fullPathPoly.bounds
        except AttributeError:
            self.setupPathGeom()

        numAssigned = 0
        locations = []
        trueLocations = []
        while numAssigned < self.numUsers:
            lat = random.random() * (maxLat-minLat) + minLat
            lon = random.random() * (maxLon-minLon) + minLon
            pt = asPoint((lon, lat))
            if self.fullPathPoly.contains(pt):
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
        """Create list of Geofences read from self.gfFilename"""

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

    def createPathList(self):
        """Create list of Location lists from self.pathFilename

        List is ordered like gfList: pathList[n] connects gfList[n]-gfList[n+1]
        """

        pathList = [[] for ii in self.gfList[:-1]]
        gfIDList = [gf.ID for gf in self.gfList]

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
                location = Location(None, latitude, longitude, None, None)
                pathList[gfIDList.index(IDStart)].append(location)

        self.pathList = pathList

    def setupPathGeom(self, pathBuffer = 1.e-4):
        """Generate shapely LineString and Polyon from list of paths

        Inputs:
            pathBuffer - float, radius around path lines polygon area (degrees)
        """

        try:
            nPaths = len(self.pathList)
        except:
            self.createPathList()
            nPaths = len(self.pathList)

        self.fullPathLS = asLineString([(loc.lon, loc.lat) \
                                        for path in self.pathList \
                                        for loc in path])
        self.fullPathPoly = self.fullPathLS.buffer(pathBuffer)

    def getNearestGeofence(self, userID, trueLoc=False):
        """Return index in self.gfList for nearest geofence"""
        distList = self.getDistancesToGeofences(userID, trueLoc=trueLoc)
        return min(enumerate(distList), key=itemgetter(1))[0]

    def setGFDistances(self):
        for gf in self.gfList:
            gf.projDist = self.fullPathLS.project(gf.location.asPoint)

    def getInitialGeofence(self, userID, trueLoc=False):
        """Return index of gf with next smallest projected location"""
        try:
            gfDistances = [gf.projDist for gf in self.gfList]
        except AttributeError:
            self.setGFDistances()
            gfDistances = [gf.projDist for gf in self.gfList]

        if trueLoc:
            loc = self.userDict[userID]._trueLocations[-1]
        else:
            loc = self.userDict[userID]._locations[-1]

        projDist = self.fullPathLS.project(loc.asPoint)
        prevGFDist = max(gfd for gfd in gfDistances if gfd <= projDist)
        prevGFIndex = gfDistances.index(prevGFDist)

        # Handle case where user starts beyond last geofence
        if prevGFIndex == (len(gfDistances) - 1):
            prevGFIndex -= 1

        return prevGFIndex

    def getDistancesToGeofences(self, userID, trueLoc=False):
        if trueLoc:
            distList = [self.userDict[userID]._trueLocations[-1].distance(gf.location)\
                        for gf in self.gfList]
        else:
            distList = [self.userDict[userID].locations[-1].distance(gf.location)\
                        for gf in self.gfList]

        return distList

    def getCurrentPathIndex(self, userID, trueLoc=False):
        """Get ID of user's current path

        Input:
            userID
        Returns:
            pathIndex - index of self.pathList user is on
        """

        try:
            prevGFIndex = self.userDict[userID].prevGeofenceIndex
            if prevGFIndex == (len(self.gfList) - 1): # user has finished
                return None
        except AttributeError: # prevGeofence hasn't been assigned, try nearest
            prevGFIndex = self.getInitialGeofence(userID, trueLoc=trueLoc)
            self.userDict[userID].prevGeofenceIndex = prevGFIndex

        pathIndex = prevGFIndex

        return pathIndex

    def getNextPathIndex(self, userID):
        currPathIndex = self.getCurrentPathIndex(userID)
        if (currPathIndex is None) or (currPathIndex == len(self.pathList)):
            return None

        return currPathIndex + 1

    def getDistancesToWaypoints(self, userID, pathIndex, trueLoc=False):
        if trueLoc:
            distList = [self.userDict[userID]._trueLocations[-1].distance(wp) \
                        for wp in self.pathList[pathIndex]]
        else:
            distList = [self.userDict[userID].locations[-1].distance(wp) \
                        for wp in self.pathList[pathIndex]]

        return distList

    def getNearestWaypoint(self, userID, pathIndex, trueLoc=False):
        distList = self.getDistancesToWaypoints(userID, pathIndex,
                                                trueLoc=trueLoc)
        return min(enumerate(distList), key=itemgetter(1))[0]

    def getInitialWaypoint(self, userID, pathIndex, trueLoc=False):

        path = self.pathList[pathIndex]
        pathLS = asLineString([(loc.lon, loc.lat) for loc in path])
        wpDistances = [pathLS.project(loc.asPoint) for loc in path]

        if trueLoc:
            loc = self.userDict[userID]._trueLocations[-1]
        else:
            loc = self.userDict[userID]._locations[-1]

        projDist = pathLS.project(loc.asPoint)
        prevWPDist = max(wpd for wpd in wpDistances if wpd <= projDist)
        prevWPIndex = wpDistances.index(prevWPDist)

        # Handle case where user starts beyond last waypoint
        if prevWPIndex == (len(path) - 1):
            prevWPIndex -= 1

        return prevWPIndex

    def getPrevWaypoint(self, userID, pathIndex, trueLoc=False):
        try:
            return self.userDict[userID].prevWaypoint
        except:
            prevWP = self.getInitialWaypoint(userID, pathIndex, trueLoc=trueLoc)
            path = self.pathList[pathIndex]
            if prevWP == (len(path) - 1): # on initialization, assume user
                                          # hasn't finished
                prevWP -= 1
            self.userDict[userID].prevWaypoint = prevWP
            return prevWP

    def getNextWaypointLocation(self, userID, pathIndex, trueLoc=False):
        prevWP = self.getPrevWaypoint(userID, pathIndex, trueLoc=trueLoc)
        path = self.pathList[pathIndex]
        if prevWP == (len(path) - 1): # start next path
            nextPathIndex = self.getNextPathIndex(userID)
            if nextPathIndex is None:
                return None
            nextWPLoc = self.pathList[nextPathIndex][0]
        else:
            nextWPLoc = self.pathList[pathIndex][prevWP+1]

        return nextWPLoc

    def getUserMovements(self, userID):
        pathIndex = self.getCurrentPathIndex(userID, trueLoc=True)
        if pathIndex is None: # user has finished
            return None

        nextWPLoc = self.getNextWaypointLocation(userID, pathIndex,
                                                 trueLoc=True)
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

    def updateUserWaypoints(self, userID, trueLoc=False):
        user = self.userDict[userID]
        path = self.pathList[user.prevGeofenceIndex]
        if trueLoc:
            loc = user._trueLocations[-1]
        else:
            loc = user._locations[-1]

        if (loc.distance(path[user.prevWaypoint+1]) <
            loc.accuracy * accuracyFactor):
            user.prevWaypoint += 1
            if user.prevWaypoint >= (len(path) - 1):
                user.prevWaypoint = 0
                user.prevGeofenceIndex += 1


    def removeFinishedUsers(self, userID):
        if self.userDict[userID].prevGeofenceIndex == (len(self.gfList) - 1):
            self.userDict.pop(userID)
            return True
        else:
            return False

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
                self.updateUserWaypoints(userID, trueLoc=True)
                if self.removeFinishedUsers(userID):
                    continue
                self.assignUserStatuses(locUpdate)

            if showPlot:
                if ii==0:
                    fig, ax = plot.setupRunPlot(self)
                    if showTrueLoc:
                        locs, = plot.plotUserLocations(ax,
                                                       self.prevTrueLocations)
                    else:
                        locs, = plot.plotUserLocations(ax, self.prevLocations)
                else:
                    if showTrueLoc:
                        locs.set_xdata([loc.lon for loc in \
                                        self.prevTrueLocations])
                        locs.set_ydata([loc.lat for loc in \
                                        self.prevTrueLocations])
                    else:
                        locs.set_xdata([loc.lon for loc in \
                                        self.prevLocations])
                        locs.set_ydata([loc.lat for loc in \
                                        self.prevLocations])
                ax.set_title(dt)
                plot.show(fig)

import seeker

sim = seeker.Simulator()
sim.createGFDict(filename = "seeker/data/beatnik_geofences.dat")
sim.createPathDict(filename = "seeker/data/beatnik_paths.dat")
sim.setupPathGeom()
sim.createUserDict()

seeker.plot.plotBackgroundMap(filename = "seeker/data/beatnik_map.png")
seeker.plot.plotGeofences(sim.gfDict.values())
seeker.plot.plotPathLines(sim.pathDict.values())
seeker.plot.plotPathPoly(sim.pathMLSPoly)
seeker.plot.plotUserLocations(sim.lastLocations)
seeker.plot.show()

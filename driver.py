import seeker

sim = seeker.Simulator()
sim.createGFDict(filename = "seeker/data/beatnik_geofences.dat")
sim.createPathDict(filename = "seeker/data/beatnik_paths.dat")

seeker.plot.plotGeofences(sim.gfDict.values())
seeker.plot.plotPaths(sim.pathDict.values())
seeker.plot.plotBackgroundMap(filename = "seeker/data/beatnik_map.png")
seeker.plot.show()

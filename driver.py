import seeker
from datetime import datetime, timedelta

# Simulator parameters and data files
numUsers=20
gfFilename = "seeker/data/beatnik_geofences.dat"
pathFilename = "seeker/data/beatnik_paths.dat"

# Time range for simulator
dtStart = datetime.now()
dtEnd = dtStart + timedelta(minutes=10)
dtDelta = timedelta(seconds=1)

# Initialize sim
sim = seeker.Simulator(20, gfFilename, pathFilename, dtStart, dtEnd, dtDelta)

# Run simulator
sim.run()

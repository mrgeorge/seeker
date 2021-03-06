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
sim = seeker.Simulator(numUsers, gfFilename, pathFilename,
                       dtStart, dtEnd, dtDelta)

seeker.plot.setupRunPlot(sim, figsize=(12,10))

raw_input("")

# Run simulator
sim.run(showPlot=True, showTrueLoc=True)

raw_input("")
# Re-initialize sim
sim = seeker.Simulator(numUsers, gfFilename, pathFilename,
                       dtStart, dtEnd, dtDelta)

sim.run(showPlot=True, showTrueLoc=False)

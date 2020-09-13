class colours:
    neutral = [255,255,255]
    failedLevel = [255,0,0]
    leftColour = [255,0,0]
    rightColour = [0,0,255]

    neutralBrightness = 50
    spikeBrightness = 100

class lightingMode:
    mode = "Notes" #Options: [Score, SongLights,Notes]
    spikeBrightnessOnNoteCut = True
    lightTransitions = "smooth" #[smooth, sudden]

class beatsaberServer:
    host = "localhost"
    port = 6557
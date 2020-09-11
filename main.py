import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import time
import yeelight
import json
import config

lights_available = []
lastRGB = (0,0,0)

def changeLightColour(colour):
    for lightIP in lights_available:
        print("Updating brightness: ",lightIP)
        yeelight.Bulb(lightIP).set_rgb(colour[0],colour[1],colour[2])

def changeLightBrightness(brightness):
    for lightIP in lights_available:
        print("Updating brightness: ",lightIP)
        yeelight.Bulb(lightIP).set_brightness(config.colours.neutralBrightness)

def startLightFlow(Flow):
    for lightIP in lights_available:
        print("Starting flow: ",lightIP)
        yeelight.Bulb(lightIP).start_flow(Flow)

def startMusicMode():
    for lightIP in lights_available:
        print("Starting music mode: ",lightIP)
        yeelight.Bulb(lightIP).start_music()

def getScoreRGB(event):
    global lastRGB
    print("Received event:",event["event"])
    try:
        if event["status"]["performance"]["currentMaxScore"] != 0:
            score = round(event["status"]["performance"]["score"]/event["status"]["performance"]["currentMaxScore"],2)
        else:
            score = 1
        print("Score:",score)
        colourScale = int((score * 255))
        print("New percentage: ",colourScale)
        rgb = (abs(colourScale-255),colourScale,0)
        return rgb
    except Exception as e:
        print("Error:",e)
        return lastRGB

def getSongLights(event):
    global lastRGB
    print("Received event:",event["event"])
    print("lightChange", event["beatmapEvent"]["value"], event["beatmapEvent"]["type"])
    try:
        if event["beatmapEvent"]["type"] == 1:
            lightChange = event["beatmapEvent"]["value"]
            print("lightChange", lightChange)
            if lightChange in [1,2,3]:
                rgb = config.colours.rightColour
            elif lightChange in [5,6,7]:
                rgb = config.colours.leftColour
            else:
                rgb = lastRGB
            return rgb
        else: return lastRGB
    except Exception as e:
        print("Exception:",e)
        return lastRGB


def on_message(ws, message):
    global lastRGB
    event = json.loads(message)
    if event["event"] == "noteCut":
        if config.lightingMode.mode == "Score":
            print("Received event:",event["event"])
            rgb = getScoreRGB(event)
            print("RGB:",rgb)
            if rgb != lastRGB:
                lastRGB = rgb
                changeLightColour(rgb)
        if config.lightingMode.spikeBrightnessOnNoteCut:
            print("Note cut received, spiking brightness")
            brightnessSpikeFlow = yeelight.Flow(
                count = 1,
                action = yeelight.Flow.actions.recover,
                transitions = [
                    yeelight.RGBTransition(lastRGB[0],lastRGB[1],lastRGB[2],brightness=config.colours.spikeBrightness),
                    yeelight.SleepTransition(duration=50),
                    yeelight.RGBTransition(lastRGB[0],lastRGB[1],lastRGB[2],brightness=config.colours.neutralBrightness),
                    ]
            )
            startLightFlow(brightnessSpikeFlow)


    elif event["event"] == "beatmapEvent":
        if config.lightingMode.mode == "SongLights":
            rgb = getSongLights(event)
            print("RGB:",rgb)
            if rgb != lastRGB:
                changeLightColour(rgb)
                lastRGB = rgb
    elif event["event"] == "finished":
        changeLightBrightness(config.colours.neutralBrightness)
        changeLightColour(config.colours.neutral)
    elif event["event"] == "failed":
        changeLightBrightness(config.colours.neutralBrightness)
        changeLightColour(config.colours.failedLevel)
        time.sleep(3)
        changeLightColour(config.colours.neutral)
            

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")
    print("Trying to reconnect in 3s")
    time.sleep(5)
    start_socket()

def on_open(ws):
    print("Connected to beatsaber")

def start_socket():
    ws = websocket.WebSocketApp("ws://"+config.beatsaberServer.host+":"+str(config.beatsaberServer.port)+"/socket",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()

if __name__ == "__main__":
    while len(lights_available) == 0:
        print("Finding lights available")
        lights_available = [x["ip"] for x in yeelight.discover_bulbs()]
        print("Found",len(lights_available),"light(s)")
    changeLightColour(config.colours.neutral)
    changeLightBrightness(config.colours.neutralBrightness)
    startMusicMode()

    print("Done, opening web socket")
    start_socket()
    
import websocket
try:
	import thread
except ImportError:
	import _thread as thread
import time
import yeelight
import json
import config
import numpy as np

lights_available = dict()
lights_enabled = set()
lastRGB = (0,0,0)

#Global variables for note flow combonation effect
noteHitRgbToSpike = np.array([0,0,0])
noteHitTimeSinceLastSpike = time.time()

# disable allEnabled if you wish for lights to be whitelisted. Set enabled property on bulb to enable
allEnabled = True

def changeLightColour(colour,):
	for bulb in get_selected():
		print("Updating brightness: ",bulb)
		bulb.set_rgb(colour[0],colour[1],colour[2])

def setUpLights(mode=config.lightingMode):
    config.lightingMode = mode
    for bulb in get_selected():
        print("Initiating light: ",bulb)
        bulb.set_rgb(config.colours.neutral[0],config.colours.neutral[1],config.colours.neutral[2])
        bulb.set_brightness(config.colours.neutralBrightness)
        bulb.start_music()
        bulb.turn_on()

def disconnectLights():
	for bulb in get_selected():
		print("Disconnecting light: ",bulb)
		bulb.set_rgb(config.colours.neutral[0],config.colours.neutral[1],config.colours.neutral[2])
		bulb.set_brightness(config.colours.neutralBrightness)
		try: bulb.stop_music()
		except: print("Failed to turn off music mode...")

def changeLightBrightness(brightness):
	for bulb in get_selected():
		print("Updating brightness: ",bulb)
		bulb.set_brightness(brightness)

def startLightFlow(Flow):
	for bulb in get_selected():
		print("Starting flow: ",bulb)
		bulb.start_flow(Flow)

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
	global noteHitRgbToSpike
	global noteHitTimeSinceLastSpike

	event = json.loads(message)
	if event["event"] == "noteCut":
		if config.lightingMode.mode == "Score":
			print("Received event:",event["event"])
			rgb = getScoreRGB(event)
			print("RGB:",rgb)
			if rgb != lastRGB:
				lastRGB = rgb
				changeLightColour(rgb)
		elif config.lightingMode.mode == "Notes":
			print("Note cut, updating lights to:",event["noteCut"]["noteType"][-1:])
			try:
				if (time.time() - noteHitTimeSinceLastSpike) > 0.1:
					noteHitRgbToSpike = np.array([0,0,0])
					noteHitTimeSinceLastSpike = time.time()
				if event["noteCut"]["noteType"][-1:] == "A":
					noteHitRgbToSpike = np.add(noteHitRgbToSpike, np.array(config.colours.leftColour))
				elif event["noteCut"]["noteType"][-1:] == "B":
					noteHitRgbToSpike = np.add(noteHitRgbToSpike, np.array(config.colours.rightColour))
				else:
					return
				np.clip(noteHitRgbToSpike,0,255)
			except Exception as e:
				print(e)
			print("Combined RGB to:",noteHitRgbToSpike)
			#Only flow if 50 mills has passed since last flow
			noteHitFlow = yeelight.Flow(
				count = 1,
				action = yeelight.Flow.actions.recover,
				transitions = [
					yeelight.RGBTransition(noteHitRgbToSpike[0],noteHitRgbToSpike[1],noteHitRgbToSpike[2],brightness=config.colours.spikeBrightness),
					]
			)
			startLightFlow(noteHitFlow)

		if config.lightingMode.spikeBrightnessOnNoteCut and config.lightingMode.mode != "Notes":
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
	print("### error ###")
	print(error)
	print("Trying to reconnect in 3s")
	time.sleep(3)
	print("Retrying...")
	start_socket()

def on_close(ws):
	print("### closed ###")

def on_open(ws):
	print("Connected to beatsaber")

wsApp = False
def start_socket():
	global wsApp
	wsApp = websocket.WebSocketApp("ws://"+config.beatsaberServer.host+":"+str(config.beatsaberServer.port)+"/socket",
							  on_message = on_message,
							  on_error = on_error,
							  on_close = on_close)
	wsApp.on_open = on_open
	wsApp.run_forever()

def discover_lights():
	global lights_available
	while len(lights_available) == 0:
		lights_available = dict()
		for light in yeelight.discover_bulbs():
			prefix = light["capabilities"]["name"] + '-'
			name = (prefix if prefix != '-' else '') + light["ip"]
			lights_available[name] = yeelight.Bulb(light["ip"],effect=config.lightingMode.lightTransitions)
		return lights_available

def get_selected():
	if(allEnabled): return lights_available.values()
	return [l for (n,l) in lights_available.items() if n in lights_enabled]

if __name__ == "__main__":
	print("Finding lights available")
	discover_lights()
	print("Found",len(lights_available),"light(s)")
	setUpLights()

	print("Done, opening web socket")
	start_socket()
	
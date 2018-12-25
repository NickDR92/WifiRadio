'''
	Author:		Nick De Raeve (Belgium)
	Date:		24/06/2018
	Title:		WiFi radio
	Description:
		This file contains the code necessary in order to program any raspberry pi to function
			as a internet radio (streaming radio). This project requires a rotary encoder
			to select a volume level, 2 push buttons to select a channel an 1 pushbutton to 
			shut down the pi. All these buttons are connected via GPIO pins to the raspberry pi.
			
		The design and code were based on this project from Marcel (https://www.instructables.com/id/Raspberry-Pi-Radio/) 
			but we added our functionalities and the I²C communication protocol. This ensured an efficient communication
			with the amplifier, which was bought on adafruit 
			(https://learn.adafruit.com/adafruit-20w-stereo-audio-amplifier-class-d-max9744/digital-control).
			
		The code used in order to set the volume via a rotary encoder is from paulV 
			(https://www.raspberrypi.org/forums/viewtopic.php?t=126753) 			
			
		An additional script will be required when using the raspberry pi zero W in order to send the audio stream to 
			the PWM GPIO pins instead of to the HDMI connector. This script can be found on 
			adafruit (https://learn.adafruit.com/adding-basic-audio-ouput-to-raspberry-pi-zero/pi-zero-pwm-audio).

		Workflow of the program:
		When the pi boots up it will read two files. The first file contains the last selected 
		volume level and the other file contains the last selected channel. 
		The pi will use the standard programmed values, in case those previously mentionned file don't exist. 
		After selecting these two parameters, the name of the 
		radio station will be announced through the speakers and eventually the stream is started 
		via omxplayer. 
		
		When the "next" or "previous" button is pushed than the function 'ChangeRadioChannel' is 
			called and the next or previous channel is played. Just like in the boot up routine, 
			the name of de radio is called. Afterwards, this channel is saved in a txt file. 

		When pushing the rotary encoder the pi will mute the steam by sending a 0 to the amplifier.
		When you turn the rotary encoder, the function 'Rotation_decoder' is called. This will determine
		which way the encoder was turned. Afterwards the 'increase_volume' of 'decrease_volume' function
		is called and the volume of the amplifier is changed. The last selected volume is also saved in 
		a txt file. 

		To terminate the pi, push the shutdown button. This calls the 'ShutdownRadio' function. 
			This function cleans up the GPIO settings and eventually shuts the pi down.
''' 
#----------------------------------------------------------------------
#							Includes
#----------------------------------------------------------------------
import RPi.GPIO as GPIO
import os
from time import sleep
import subprocess
from MAX9744 import MAX9744

#----------------------------------------------------------------------
#							Variables
#----------------------------------------------------------------------

# Channels
CurrentChannel = 0	# Variable used to save the current channel that is playing
# All channels that this radio can play
Channels = [
	'Radio P.R.O.S.', 'http://audiostreamen.nl:8012',
	'Star Radio', 'http://internetradio.radiostar.be:8000/;stream.nsv&type=mp3',
	'Radio 1','http://icecast.vrtcdn.be/radio1-high.mp3 ',
	'Radio 2 oost-vlaanderen', 'http://icecast.vrtcdn.be/ra2ovl-high.mp3',
	'MNM', 'http://icecast.vrtcdn.be/mnm-high.mp3',
	'Studio Brussel', 'http://icecast.vrtcdn.be/stubru-high.mp3',
	'Joe FM', 'http://icecast-qmusic.cdp.triple-it.nl/JOEfm_be_live_128.mp3',
	'Nostalgie', 'http://nostalgiewhatafeeling.ice.infomaniak.ch/nostalgiewhatafeeling-128.mp3',
	'Q music', 'http://icecast-qmusic.cdp.triple-it.nl/Qmusic_be_live_128.mp3',
]
isPlaying = False	# Flag used to be sure whether the radio is playing or not
# Declaration of the process used to start the audiostream
MyProcess = subprocess.Popen(['echo', 'Hello'], stdout=subprocess.PIPE)
print(MyProcess.communicate())

# Declaration of the amplifier
Amplifier = MAX9744()

# GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
''' Variables holding the physical pins of the pi '''
Pin_VolUp = 29		#Kanaal A Rotary encoder 	(GPIO 5)
Pin_VolDown = 31	#Kanaal B Rotary encoder 	(GPIO 6)
Pin_Mute = 35		#Switch Rotary encoder 		(GPIO 19)
Pin_Next = 7		#Push button				(GPIO 4)
Pin_Prev = 11		#Push button				(GPIO 17)
Pin_OnOff = 13		#Push button				(GPIO 27)

# Volume settings
CurrentVolume = 32			# 
MAX_VOLUME = 63		# Maximum reachable volume
MIN_VOLUME = 0		# Volume at mute level
SPEECH_VOLUME = 55	# Volume used when radio says the name of the channel
isMuted = False		# Flag stating radio is muted

#----------------------------------------------------------------------
#					Initialization of GPIO
#----------------------------------------------------------------------
# Initialzing pins for I/O
GPIO.setup(Pin_VolUp, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)	# Pull-Down
GPIO.setup(Pin_VolDown, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)	# Pull-Down
GPIO.setup(Pin_Mute, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)		# Pull-Down
GPIO.setup(Pin_OnOff, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)		# Pull-Up
GPIO.setup(Pin_Next, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)		# Pull-Up
GPIO.setup(Pin_Prev, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)		# Pull-Up

#----------------------------------------------------------------------
#							Functions
#----------------------------------------------------------------------
'''
	Function used to safely shut down the radio
'''
def ShutdownRadio(dummy):
	print('Shut down radio')
	GPIO.cleanup()
	os.system("sudo shutdown -h now")

'''
	Function used to change the radio channel. When changed the new 
	channel is saved in a txt file
'''
def ChangeRadioChannel(choice):
	print('Change radio channel')
	global CurrentChannel 
	global Channels
	global MyProcess
	global Amplifier
	
	# Get next channel
	CurrentChannel = CurrentChannel + choice*2
	
	# Adjust CurrentChannel when needed
	if CurrentChannel < 0:
		CurrentChannel = len(Channels)-2
	if CurrentChannel > len(Channels)-1:
		CurrentChannel = 0

	if isPlaying == True:
		MyProcess.stdin.write('q')	# kill running stream
		sleep(0.5)	# Wait 500 ms to quit the previous channel
	# Use text to speech to hear the name of the radio channel
	Amplifier.set_volume(SPEECH_VOLUME)	# Adjust volume
	os.system('echo "' + Channels[CurrentChannel] + '" | festival --tts')	# text to speech convertion of the radio name
	# Start the channel
	Amplifier.set_volume(CurrentVolume)	# Adjust volume
	MyProcess = subprocess.Popen(['omxplayer', '-o', 'local', Channels[CurrentChannel+1]], stdin=subprocess.PIPE)	# Start new stream
	
	#Store latest chosen channel in txt file
	file = open("LastChannel.txt","w")
	file.write(str(CurrentChannel)+"\n")
	file.close()
 
'''
	Function used to increase the volume by 1 via a I2C command
'''
def VolumeUp(dummy):
	print('Volume up')
	global Amplifier
	global CurrentVolume
	CurrentVolume = CurrentVolume + 1
	if CurrentVolume >= MAX_VOLUME:
		CurrentVolume = MAX_VOLUME
	else:
		Amplifier.increase_volume()
	
	#Store latest volume in txt file
	file = open("LastVolume.txt", "w")
	file.write(str(CurrentVolume) + "\n")	
	file.close()

'''
	Function used to decrease the volume by 1 via a I2C command
'''
def VolumeDown(dummy):
	print('Volume down')
	global Amplifier
	global CurrentVolume
	CurrentVolume = CurrentVolume - 1
	if CurrentVolume <= MIN_VOLUME:
		CurrentVolume = 0
	else:
		Amplifier.decrease_volume()
		
	#Store latest volume in txt file
	file = open("LastVolume.txt", "w")
	file.write(str(CurrentVolume) + "\n")	
	file.close()

'''
	Function used to mute the amplifier
'''
def Mute(dummy):
	global Amplifier
	global isMuted
	if isMuted == False:
		print('Volume muted')
		Amplifier.set_volume(0)
		isMuted = True
	else:
		print('Volume unmuted')
		Amplifier.set_volume(CurrentVolume)
		isMuted = False

'''
	Function used to decode in which way the rotary encoder is turned
'''
def Rotation_decoder(dummy):
	print('Decode rotary encoder')
	global counter
	VolUp = GPIO.input(Pin_VolUp)
	VolDown = GPIO.input(Pin_VolDown)
	
	sleep(0.002) # extra 2 mSec de-bounce time
	if (VolUp == 1) and (VolDown == 0) : # A then B ->
		VolumeUp(dummy)

	elif (VolUp == 1) and (VolDown == 1): # B then A <-
		VolumeDown(dummy)

	else: # discard all other combinations
		return

'''
	Function used to get the next channel
'''
def Next(dummy):
	print('Next radio channel')
	ChangeRadioChannel(1)

'''
	Function used get the previous channel
'''
def Previous(dummy):
	print('Previous radio channel')
	ChangeRadioChannel(-1)

#----------------------------------------------------------------------
#						Initialization of events
#----------------------------------------------------------------------
GPIO.add_event_detect(Pin_VolUp, GPIO.RISING, callback = Rotation_decoder, bouncetime=2)
GPIO.add_event_detect(Pin_Mute, GPIO.RISING, callback = Mute, bouncetime = 2000)
GPIO.add_event_detect(Pin_OnOff, GPIO.RISING, callback = ShutdownRadio, bouncetime = 2000)
GPIO.add_event_detect(Pin_Next, GPIO.RISING, callback = Next, bouncetime = 2000)
GPIO.add_event_detect(Pin_Prev, GPIO.RISING, callback = Previous, bouncetime = 2000)

#----------------------------------------------------------------------
#							Main
#----------------------------------------------------------------------
try:
	try:
		# At boot
		# 1) restore volume
		try: 
			file = open("LastVolume.txt", "r")
			CurrentVolume = int(file.read())
			Amplifier.set_volume(CurrentVolume)
			file.close()
			print('Volume is set')
		except: pass
		
		# 2) restore channel
		# Read latest channel from txt file
		file = open("LastChannel.txt","r")
		CurrentChannel = int(file.read())
		file.close()
		
		Amplifier.set_volume(SPEECH_VOLUME) # Adjust volume
		os.system('echo "' + Channels[CurrentChannel] + '" | festival --tts')	# text-to-speech conversion of the radio name
		Amplifier.set_volume(CurrentVolume)	# Adjust volule
		MyProcess = subprocess.Popen(['omxplayer', '-o', 'local', Channels[CurrentChannel+1]], stdin=subprocess.PIPE)	# Start audio stream
		isPlaying = True
	except:
		CurrentChannel=0
		ChangeRadioChannel(0)

	while True:	#Infinite loop
		sleep(0.5)
		
except KeyboardInterrupt:
	GPIO.cleanup()

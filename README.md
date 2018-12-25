# WifiRadio
This project contains all the python files to make a ethernet radio with a Raspberry Pi and a 20W amplifier from adafruit.

I bought the amplifier from adafruit and used there python code to install all the necessary libraries and some example code. 
Amplifier: https://www.adafruit.com/product/1752
Github amplifier: https://github.com/adafruit/Adafruit_Python_MAX9744

Based on some example code from instructables I created this code. All the necessary code is found in main python file 

In my project I used a Raspberry Pi Zero. So I had to reroute the audio to 2 PWM gpio pins (https://learn.adafruit.com/adding-basic-audio-ouput-to-raspberry-pi-zero). Afterwards I installed a media player and a program that makes the pi read the name from the radio station.

```
sudo apt-get install festival
sudo apt-get install mplayer2
```

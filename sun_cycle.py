from phue import Bridge
import os
import time
import colorsys
import math
import opc
import Dynamo
import datetime
from astral import Astral

bridge = Dynamo.bridge
FCpixels = Dynamo.FCpixels
FCclient = Dynamo.FCclient

a = Astral()
city = a['Chicago']

def getTemp():
    now = datetime.datetime.now()
    elevation = city.solar_elevation(now)
    print('The time is: %s' % str(now))
    print('Solar elevation: %s degrees' % elevation)
    kelvin = (1228.7 * math.log(elevation)) + 253.03
    print('Estimated color temperature: %sK' % kelvin)
    return kelvin

def clamp(value):
    if value < 0:
        return 0
    if value > 255:
        return 255

def kelvin2rgb(kelvin):
    temp = kelvin / 100
    if temp <= 66:
        red = 255
        green = 99.4708025861 * math.log(temp) - 161.1195681661

        if temp <= 19:
            blue = 0
        else:
            blue = 138.5177312231 * math.log(temp - 10) - 305.0447927307
    else:
        red = 329.698727446 * ((temp - 60) ** -0.1332047592)
        green = 288.1221695283 * ((temp - 60) ** -0.0755148492)
        blue = 255
    return [red, green, blue]

def rgb2hsv_p(RGB):                                                               #Takes RGB value and delivers the flavor of HSV that the hue api uses
    R = RGB[0] / 255                                                            #colorsys takes values between 0 and 1, PIL delivers between 0 and 255
    G = RGB[1] / 255
    B = RGB[2] / 255
    hsv = colorsys.rgb_to_hsv(R, G, B)                                          #Makes standard HSV
    hsv_p = [int(hsv[0] * 360 * 181.33), int(hsv[1] * 255), int(hsv[2] * 255)]  #Converts to Hue api HSV
    return hsv_p

def lights_from_kelvin(kelvin, room):                                             #Function takes color list and applies to lights with 10s fade
    rgb = kelvin2rgb(kelvin)
    print('Setting lights as %s' % rgb)
    print('')
    hsv_p = rgb2hsv_p(rgb)
    for l in range(len(room)):
        if type(room[l]) == range:                                               #See if this is a neopixel strip
            for p in room[l]:
                FCpixels[p] = rgb

        else:
            command = {'hue': hsv_p[0], 'sat': hsv_p[1], 'bri': hsv_p[2], 'transitiontime': 300, 'on': True}
            bridge.set_light(room[l], command)
    FCclient.put_pixels(FCpixels)

room = Dynamo.living_room

while True:
    kelvin = getTemp()
    lights_from_kelvin(kelvin, room)
    time.sleep(60)

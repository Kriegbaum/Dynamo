from phue import Bridge
import os
import time
from PIL import Image
from PIL import ImageFile
import colorsys
import math
import numpy as np
import random

#REMINDER FOR FUTURE ME, PHUE.PY NEEDS TO BE IN SCRIPT'S DIRECTORY WHEN PUSHED TO GITHUB


bridge = Bridge('10.0.0.10')
bedroom = [7,8,10,11,12,14]
living_room = [1,2,3,4,5,6,13]
everything = [1,2,3,4,5,6,7,8,10,11,12,13,14]

ImageFile.LOAD_TRUNCATED_IMAGES = True

def setup():
    print('Input bridge IP address')
    bridgeip = input()
    bridge = Bridge(bridgeip)
    settings_body = 'Bridge IP:\n' + bridgeip + '\n'
    settings = open(settings_path, 'w')
    print('Within the next 30 seconds, press the bridge connect button')
    time.sleep(30)
    bridge.connect()

    api = bridge.get_api()
    lights = bridge.get_light_objects('id')


    print('##########  I found these groups in your bridge  ##########')

    for i in api['groups']:
        group = api['groups'][i]
        print(group['name'])
        for i in group['lights']:
            print(i, lights[int(i)])
        print('###########################################################')

    print('Writing these groups to settings...')

    group_dict = {}

    for i in api['groups']:
        tmplist = []
        group = api['groups'][i]
        for n in group['lights']:
            tmplist.append(int(n))
        group_dict[group['name']] = tmplist
    settings_body += str(group_dict) + '\n'
    settings.write(settings_body)
    settings.close()

def getsettings():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    settings_path = script_dir + '/hue_settings.txt'
    if os.path.exists(settings_path):
        settings = open(settings_path, 'r')
        settings.readline()
        bridge = Bridge(readline())
        settings.readline()
        rooms = eval(settings.readline())
    else:
        setup()

def sample_image(image):
    im = Image.open(image)
    colors = im.getcolors(100000)
    color_count = [x[0] for x in colors]
    color_values = [x[1] for x in colors]
    min_color_values = []
    min_color_count = []
    for i in range(len(colors)):
        total = sum(color_values[i])
        if total > 25:
            min_color_values.append(color_values[i])
            min_color_count.append(color_count[i])
    top_color = []
    for i in range(25):
        tmp = max(min_color_count)
        tmp_index = min_color_count.index(tmp)
        top_color.append(min_color_values[tmp_index])
        del min_color_values[tmp_index]
        del min_color_count[tmp_index]
    return top_color

def convert(RGB):
    R = RGB[0] / 255
    G = RGB[1] / 255
    B = RGB[2] / 255
    hsv = colorsys.rgb_to_hsv(R, G, B)
    hsv_p = [int(hsv[0] * 360 * 181.33), int(hsv[1] * 255), int(hsv[2] * 255)]
    return hsv_p

def randomcolor(image, n):
    top_color = sample_image(image)
    colorlist = []
    for i in range(n):
        num = random.randrange(0, 24)
        color = convert(top_color[num])
        colorlist.append(color)
    return colorlist

def rekt(n):
    factors = []
    for i in range(1, n + 1):
        if n % i == 0:
            factors.append(i)
    if len(factors) % 2 == 0:
        larger = factors[int((len(factors) / 2))]
    else:
        larger = factors[int((len(factors) / 2) - .5)]
    return [larger, int(n / larger)]

def sample_sectors(image, room):
    im = Image.open(image)
    size = im.size
    if size[0] > size[1]:
        hdiv = max(rekt(len(room)))
        vdiv = min(rekt(len(room)))
    else:
        hdiv = min(rekt(len(room)))
        vdiv = max(rekt(len(room)))
    varray = np.full((vdiv + 1, vdiv + 1), 0, int)
    harray = np.full((hdiv + 1, hdiv + 1), 0, int)
    for col in range(len(harray)):
        for row in range(len(harray)):
            harray[col][row] = (size[0] / hdiv) * row
    for col in range(len(varray)):
        for row in range(len(varray)):
            varray[col][row] = (size[1] / vdiv) * row
    pixels = []
    px = im.load()
    if hdiv >= vdiv:
        for row in range(1, hdiv + 1):
            for vrow in range(1, vdiv + 1):
                hrand = random.randrange(harray[0][row - 1], harray[0][row])
                vrand = random.randrange(varray[0][vrow - 1], varray[0][vrow])
                tmpix = px[hrand, vrand]
                if type(tmpix) == int:
                    tmpix = [tmpix, tmpix, tmpix]
                pixels.append([tmpix[0], tmpix[1], tmpix[2]])
    else:
        for row in range(1, vdiv + 1):
            for vrow in range(1, hdiv + 1):
                vrand = random.randrange(varray[0][row - 1], varray[0][row])
                hrand = random.randrange(harray[0][vrow - 1], harray[0][vrow])
                tmpix = px[hrand, vrand]
                if type(tmpix) == int:
                    tmpix = [tmpix, tmpix, tmpix]
                pixels.append([tmpix[0], tmpix[1], tmpix[2]])
    for i in range(len(pixels)):
        pixels[i] = convert(pixels[i])
    return pixels

def lights_from_image(image, room):
    it = 0
    colorlist = sample_sectors(image, room)
    for l in room:
        command = {'hue': colorlist[it][0], 'sat': colorlist[it][1], 'bri': colorlist[it][2], 'transitiontime': 100}
        bridge.set_light(l, command)
        it += 1
def dynamic_image(image, room):
    ex = 0
    while 1 == 1:
        lights_from_image(image, room)
        time.sleep(15)
        ex += 1
        if ex % 3 == 0:
            random.shuffle(room)
            print('Shuffle on iteration', ex)

print('Input image filepath')
print()
filepath = input()
print('Which room?')
group = eval(input())
bridge.set_light(group, 'on', True)

dynamic_image(filepath, group)

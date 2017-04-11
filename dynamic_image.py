from phue import Bridge
import os
import time
from PIL import Image
from PIL import ImageFile
import colorsys
import math
import numpy as np
import random
import opc
import Dynamo

Dynamo.serverstart()
bridge = Dynamo.bridge
FCpixels = Dynamo.FCpixels
FCclient = Dynamo.FCclient

FCclient = opc.Client('localhost:7890')

ImageFile.LOAD_TRUNCATED_IMAGES = True

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
    return pixels

def lights_from_image(image, room):
    it = 0
    colorlist = sample_sectors(image, room)
    for l in range(len(room)):
        if type(room[l]) == range:                                              #See if this is a neopixel strip
            templist = [colorlist[it][0], colorlist[it][1], colorlist[it][2]]   #Useful for swapping RGB to GBR
            colorlist[it] = templist
            if sum(templist) < 15:
                templist = [0,0,0]
            for p in room[l]:
                FCpixels[p] = colorlist[it]
            it += 1

        else:
            colorlist[it] = convert(colorlist[it])                              #Get color values into something hue API can understand
            com_on = True
            com_sat = colorlist[it][1]
            com_bri = colorlist[it][2]
            com_trans = 70
            command = {'hue': colorlist[it][0], 'sat': com_sat , 'bri': com_bri , 'transitiontime': com_trans, 'on' : com_on}
            bridge.set_light(room[l], command)
            it += 1

def dynamic_image(image, room):
    ex = 0
    while 1 == 1:
        lights_from_image(image, room)
        FCclient.put_pixels(FCpixels)
        time.sleep(17)
        ex += 1
        if ex % 3 == 0:
            random.shuffle(room)
            print('Shuffle on iteration', ex)

print('Input image name')
print()
filedir = os.path.join('E:\\', 'Spidergod', 'Images', 'Color Pallettes')
pallettes = os.listdir(filedir)
for f in pallettes:
    print(f)
filepath = input()
filepath = os.path.join('E:\\', 'Spidergod', 'Images', 'Color Pallettes', filepath)
print('Which room?')
group = Dynamo.room_dict[input().lower()]
for i in range(len(group)):
    if type(group[i]) != range:
        bridge.set_light(group[i], 'on', True)

for i in range(256, 321):
    FCpixels[i] = [255,255,220]

dynamic_image(filepath, group)

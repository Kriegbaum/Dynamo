import librosa
from scipy.ndimage import gaussian_filter1d
from strandEffects import *
import random
import os
import csv
import numpy as np
from playsound import playsound
import threading
from musicbeeipc import *


mb = MusicBeeIPC()

path = 'C:\\users\\akauf\\desktop\\song.mp3'
print('Loading Song')
sampleRate = 44100
songArray, sampleRate = librosa.load(path, sr=sampleRate)
print('Harmonic percussive seperation...')
harmonicArray, percussiveArray = librosa.effects.hpss(songArray)
print('Beat analysis...')
BPM, beatTrack = librosa.beat.beat_track(y=songArray, sr=sampleRate, units='time')
print('%s beats in song' % len(beatTrack))

def normalize(array, sigma=False, shift=False):
    if shift:
        low = min(array)
        array += abs(low)
    else:
        array = np.absolute(array)
    if sigma:
        array = gaussian_filter1d(array, sigma)
    array *= (255.0 / array.max())
    return array

percussiveArray = normalize(percussiveArray, sigma=(0.0224 * sampleRate))
print('New min : %s' % min(percussiveArray))


def sumGraph(array, sigma=15):
    '''This is essentially an integral graph in spirit, for every frame, if its
    harmonic power is over the track's average, the slope is positive, if below
    the average harmonic power, the slope is negative, Sigma is additional smoothing'''
    print('    Performing integral array...')
    #First we establish the average for the whole array
    #TODO: There is probably a baked-in system function for this either in python or numpy
    avg = 0
    for i in array:
        avg += i
    avg = avg / len(array)
    #Run is the running value of the graph, to be tooled up or down with every frame
    run = avg
    newArray = []
    for i in range(1, len(array)):
        tmp = array[i]
        #TODO: What the fuck is this about? WHy?
        if array[i] < 0.1:
            tmp = abs(avg - 2)
        #How far off the average are we? Adjust run up or down depending
        run += tmp - avg
        newArray.append([i, run])
    #Now we adjust the array so that it falls between 0 and 255
    arrayMin = abs(min([x[1] for x in newArray]))
    arrayMax = max([x[1] for x in newArray])
    factor = 255 / (arrayMax + arrayMin)

    for i in newArray:
        i[1] = (i[1] + arrayMin) * factor
    #Lets, uhhhhh, lets uh smoooth this out
    smoothArray = gaussian_filter1d([x[1] for x in newArray], sigma)

    for i in range(len(newArray)):
        newArray[i][1] = smoothArray[i]

    return newArray

def derivGraph(graph, shift=True):
    '''Takes a super cool graph, and makes another graph thats a derivative of
    the first graph, shift determines whether the graph goes 0-255 or -255 to 255'''
    print('    Creating derivative graph...')
    derivGraph = []
    #Basic derivative action, determine the slope between this point and the next
    for i in range(len(graph) - 1):
        slope = (graph[i + 1][1] - graph[i][1]) / (graph[i + 1][0] - graph[i][0])
        derivGraph.append([i, slope])
    #Perform our scaling work here
    #TODO: it seems like every graph does this, make a function that scales a two dimensional array?
    derivMax = max([x[1] for x in derivGraph])
    derivMin = min([x[1] for x in derivGraph])
    if shift:
        factor = 255 / (derivMax + derivMin)
    else:
        factor = 255 / (derivMax)
    #Perform our shift work here
    #TODO: Seems like this is done a few times, make a function that shifts a two dimensional array?
    for i in derivGraph:
        if shift:
            i[1] += derivMin
        i[1] *= factor
    return derivGraph

def smoothArray(graph):
    '''TBH dont quite know what's happening here
    TODO: Figure out what the fuck is happening here'''
    print('    Smoothing sample array...')
    newGraph = []
    hop = 5100
    for i in range(hop, len(graph), hop):
        run = gaussian_filter1d([x[1] for x in graph[i - hop]], 25)
        tmp = 0
        for s in range(i - hop, i + hop - 1):
            if tmp == len(run):
                break
            else:
                newGraph.append([graph[s][0], run[tmp]])
            tmp += 1
    lrg = gaussian_filter1d([x[1] for x in newGraph], .6 * sampleRate)
    for i in range(len(graph)):
        newGraph[i][1] = lrg[i]
    return newGraph

'''I seem to have spent a lot of time figuring out what the values below should be,
but the code indicates that they are dependent on the sample rate, the original
project seems to have done an analysis twice at two different sample rates, presumably
one for fidelity and one for speed. Not quite sure how nessecary the double analysis is,
seems to me now that a speed analysis should be sufficient'''
#arcGraph = normalize(songArray, sigma=(1.85 * sampleRate), shift=False)
#harmGraph = normalize(harmonicArray, sigma=(0.9571 * sampleRate))
#largeArc = sumGraph(songArray, simga=(5.442 * sampleRate))

#harmGraph = smoothArray(harmGraph)

def zeroSlopes(graph):
    '''Finds points in the graph where the slope is zero, determines if its high or low
    Typical moment returned: [sample, bool], boolean is true if this is a high point, false if low'''
    print('Finding arc pivot points...')
    #This will be a list of moments where the derivative is zero
    zeroList = []
    deriv = derivGraph(graph, False)
    for i in range(len(deriv) - 1):
        #deriv rarely lands at exactly zero, this finds if the derivative has passed zero between frames
        if deriv[i][1] > 0 and deriv[i + 1][1] <= 0:
            zeroList.append([graph[i][0], True])
        elif deriv[i][1] < 0 and deriv[i + 1][1] >= 0:
            zeroList.append([graph[i][0], False])
    return zeroList

def percussiveParse(graph, beatTrack, threshold=87):
    '''Takes librosa's beat detection, and our own track analysis, and figures out
    whether this is a beat worth emphasizing. This will toss out most beat moments
    from the librosa beat track'''
    print('Culling beat moments...')
    beatList = []
    #For every one of librosa's beats, see if there is enough percussive power to qualify it
    #TODO: Deterimine beat strength through a derivative of derivative
    #TODO: See how a derivative graph of percussive events compares to this
    for i in beatTrack:
        graphPower = graph[int(i * sampleRate)]
        if graphPower > threshold:
            beatList.append(i)
    return beatList

def writeData(path, graph):
    print('Writing graph')
    with open(path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for i in range(len(graph)):
            writer.writerow([i, graph[i]])

pixels = PixelArray(allMap, locationMap, intersections, room, controller)

def beat():
    flyLocation = random.choice(pixels.allMap)
    pixels.fireflyRigid(flyLocation, [85, 117, 0], [10,26,0], [0, 12, 22], 1.3)

#writeData('C:\\users\\akauf\\desktop\\percgraph.csv', percussiveArray)
beatTrack = percussiveParse(percussiveArray, beatTrack)
for i in beatTrack:
    i -= .05
print(beatTrack)
mb.clear_now_playing_list()
mb.stop()
mb.queue_next(path)
for dumb in beatTrack:
    t = threading.Timer(dumb, beat)
    t.start()
mb.play()

import librosa
from scipy.ndimage import gaussian_filter1d
from Tantallion import *
import random
import os
import csv

path = input()
songArray, sampleRate = librosa.load(path)
harmonicArray, percussiveArray = librosa.effects.hpss(songArray)
BPM, beatTrack = librosa.beat.beat_track(y=songArray, sr=sampleRate, units='time')

def normalize(array, sigma=0, shift=True):
    '''Makes the highest value of the graph 255, and the lowest value 0
    this should exaggerate the peaks and valleys, and create the highest possible
    dynamic range, allowing the following functions access to finer detail in the track
    If shift is true, the graph will go 0-255, if False, the graph will go -255 - 255
    Sigma will determine the amount of smoothing in the graph'''
    print('    Normalzing...')
    #New list to append modified values to, to avoid altering the original array
    values = []
    for i in array:
        #TODO: Test this, is there are reason for typecasting to floats?
        if shift:
            values.append(float(i))
        else:
            values.append(float(abs(i)))
    #Smooth out jagged lines in the array
    values = gaussian_filter1d(values, sigma)
    low = min(values)
    high = max(values)
    '''Determine the factor each array value needs to be mutliplied by in order
    to achieve the new desired range of values, keeping things proportional'''
    if low >= 0:
        factor = 255 / (high - low)
    else:
        factor = 255 / (high + abs(low))
    #Do this to ensure that the bottom of the graph is 0
    for i in values:
        if low < 0:
            i += abs(low)
        else:
            i -= low
        i *= factor
    #Turn this into a two dimensional array to be used as a graph
    for i in range(len(values)):
        values[i] = [i, values[i]]
    #Returns a two dimensional array
    return values

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

    for i in range(len(newArray):
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
arcGraph = normalize(songArray, sigma=(1.85 * sampleRate), shift=False)
percGraph = normalize(percussiveArray, sigma=(0.0224 * sampleRate), shift=False)
harmGraph = normalize(harmonicArray, sigma=(0.9571 * sampleRate))
largeArc = sumGraph(songArray, simga=(5.442 * sampleRate))

harmGraph = smoothArray(harmGraph)

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
            zeroList.append([graph[i][0], True)
        elif deriv[][1] < 0 and deriv[i + 1][1] >= 0:
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
        graphPower = graph[i * sampleRate][1]
        if graphPower > threshold:
            beatList.append(i)
    return beatList

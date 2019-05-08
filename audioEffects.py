import librosa
from scipy.ndimage import gaussian_filter1d
from Tantallion import *
import random
import os
import csv

path = input()
songArray, sampleRate = librosa.load(path)
BPM, beatArray = librosa.beat.beat_track(songArray, sampleRate, units='time')

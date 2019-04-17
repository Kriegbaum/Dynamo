from DYNAcore import *
from datetime import datetime

def circadianLookup(city):
    '''retuns a color temperature value given an astral city object'''
    '''Data points:
    (-36, 2700)
    (-18, 15000)
    (0, 7000)
    (18, 10000)
    (90, 7000)
    (0, 2000)
    (-18, 10000)
    (-36, 2700)
    '''
    sun = city.sun()
    timezone = sun['sunrise'].tzinfo
    now = datetime.now(tz=timezone)
    elevation = city.solar_elevation()
    print('Sun elevation: ' + str(elevation))
    #Are we after sunset or before sunrise?
    if elevation < 0:
        #In the darkest part of the night, lights go to natural tungsten lamp, but a little warmer
        if elevation <= -36:
            return 2700
        #Just before sunrise, lights get very cool to help wake you up
        if now <= sun['sunrise']:
            if elevation <= -18:
                return ((2050 * elevation) / 3.0) + 27300
            else:
                return 7000 - ((4000 * elevation) / 9.0)
        elif now >= sun['sunset']:
            if elevation <= -18:
                return ((3650 * elevation) / 9.0) + 17300
            else:
                return 2000 - ((4000 * elevation) / 9.0)
        #There should be no cases outside of the above tests
        else:
            print('Sun elevation is negative, but it is after sunrise and before sunset, something is not right here')
            return False
    #The sun will pass each elevation point twice, but the light should continue to get warmer
    #So we must seperate before and after noon
    else:
        if now <= sun['noon']:
            #There is a second spike in color temperature after sunrise
            if elevation < 18:
                return ((500 * elevation) / 3.0) + 7000
            else:
                return 10750 - ((125 * elevation) / 3.0)
        else:
            return ((500 * elevation) / 9.0) + 2000


def circadian(room):
    print('Circadian cycle selected, loading Astral module...')
    from astral import Astral
    print('Astral module loaded!')
    cityName = 'Chicago'
    a = Astral()
    city = a[cityName]
    controllerList = gatherControllers(room)
    while True:
        if gatherArbitration(controllerList):
            kelvin = circadianLookup(city)
            print('Based on sun elevation, setting lights to: %s Kelvin' % kelvin)
            rgb = cctRGB(kelvin)
            print('Kelvin parsed to ' + str(rgb))
            rgbRoom(room, rgb, 40)
            print('...')
            print('')
            time.sleep(120)
        else:
            print('Circadian routine interrupted by manual override')

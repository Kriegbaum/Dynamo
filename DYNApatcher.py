import os
import yaml
import sys

###########################RIG PROPERTIES#####################################
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')) as f:
    configFile = f.read()
configs = yaml.load(configFile)

hasFadecandy = configs['hasFadecandy']
hasHue = configs['hasHue']
hasMusicbee = configs['hasMusicbee']

if sys.platform == 'linux':
    pallettesDir = configs['pallettesDirLinux']
else:
    pallettesDir = configs['pallettesDirWin']

hueIP = configs['hueIP']
fadecandyIPs = configs['fadecandyIPs']

allFixtures = []
fixtureDict = {}

def testDict(dictionary, key, default):
    '''See if the patch dictionary has specified a value. If it hasn't, return
    a specificed default'''
    try:
        result = dictionary[key]
        return result
    except KeyError:
        return default

class Fixture:
    def __init__(self, patchDict, name):
        self.system = patchDict['system']
        self.name = name
        self.colorCorrection = testDict(patchDict, 'colorCorrection', [1,1,1])
        if self.system == 'Hue':
            self.dimming = testDict(patchDict, 'dimming', True)
            self.color = testDict(patchDict, 'color', True)
            self.id = testDict(patchDict, 'id', 0)
        if self.system == 'Fadecandy':
            self.indexrange = testDict(patchDict, 'indexrange', [0,0])
            self.grb = testDict(patchDict, 'grb', True)
            self.controller = patchDict['controller']
        self.room = testDict(patchDict, 'room', 'UNUSED')
        allFixtures.append(self)
        fixtureDict[self.name] = self
    def __repr__(self):
        return('%s: %s' % (self.name, self.system))

#####################FIXTURE GENERATION#########################################
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'patch.yml')) as f:
    patchFile = f.read()
patch = yaml.load(patchFile)

for f in patch:
    new = Fixture(patch[f], f)

#######################GROUPS###################################################

rooms = {'all': [], 'nonDim': []}
for i in allFixtures:
    if i.system == 'Hue' and not (i.dimming or i.color):
        rooms['nonDim'].append(i)
    elif i.room in rooms:
        rooms[i.room].append(i)
    else:
        rooms[i.room] = [i]
    if i not in rooms['nonDim']:
        rooms['all'].append(i)

groups = {}

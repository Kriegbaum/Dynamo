import os
import yaml

###########################RIG PROPERTIES#####################################
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')) as f:
    configFile = f.read()
configs = yaml.load(configFile)

hasFadecandy = configs['hasFadecandy']
hasHue = configs['hasHue']
hasMusicbee = configs['hasMusicbee']

pallettesDir = configs['pallettesDir']

hueIP = configs['hueIP']
fadecandyIP = configs['fadecandyIP']

allFixtures = []

def testDict(dictionary, key, default):
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
        self.room = testDict(patchDict, 'room', 'UNUSED')
        allFixtures.append(self)
    def __repr__(self):
        return('%s: %s' % (self.name, self.system))

#####################FIXTURE GENERATION#########################################
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'patch.yml')) as f:
    patchFile = f.read()
patch = yaml.load(patchFile)

for f in patch:
    new = Fixture(patch[f], f)

#######################GROUPS###################################################

rooms = {'all': []}
for i in allFixtures:
    if hasattr(i, 'dimming') or hasattr(i, 'color'):
        if not i.dimming or not i.color:
            break
    if i.room in rooms:
        rooms[i.room].append(i)
    else:
        rooms[i.room] = [i]
    rooms['all'].append(i)
groups = {}

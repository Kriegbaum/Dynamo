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
class Fixture:
    def __init__(self, system, name):
        self.system = system
        self.name = name
        self.colorCorrection = [1, 1, 1]
        if system == 'Hue':
            self.dimming = True
            self.color = True
            self.id = 0
        if system == 'Fadecandy':
            self.indexrange = [0,0]
            self.grb = True
        self.room = 'UNUSED'
        allFixtures.append(self)
    def __repr__(self):
        return('%s: %s' % (self.name, self.system))

#############################################################################
#                       FIXTURE DEFINITIONS

#Fadecandy Fixtures
s1 = Fixture('Fadecandy', 'Windows')
s1.indexrange = [0,128]
s1.colorCorrection = [1,.8627,.6705]
s1.room = 'bedroom'

s3 = Fixture('Fadecandy', 'Fan')
s3.indexrange = [448,494]
s3.colorCorrection = [1, .8627, 0.6705]
s3.room = 'bedroom'

s4 = Fixture('Fadecandy', 'Worklight')
s4.indexrange = [384,385]
s4.colorCorrection = [1, .97777, 0.63137]
s4.room = 'bedroom'

#Hue Fixtures
h1 = Fixture('Hue', 'Coffee Station')
h1.id = 1
h1.room = 'kitchen'

h2 = Fixture('Hue', 'Desk Lamp')
h2.id = 2
h2.room = 'bedroom'

h3 = Fixture('Hue', 'Entry 2')
h3.id = 3
h3.room = 'living room'

h4 = Fixture('Hue', 'Reaper')
h4.id = 4
h4.room = 'living room'

h5 = Fixture('Hue', 'Table Lamp')
h5.id = 5
h5.room = 'living room'

h6 = Fixture('Hue', 'Flag Left')
h6.id = 6
h6.room = 'living room'

h7 = Fixture('Hue', 'Flag Right')
h7.id = 7
h7.room = 'living room'

h8 = Fixture('Hue', 'TV')
h8.id = 8
h8.room = 'living room'

h10 = Fixture('Hue', 'Duct')
h10.id = 10
h10.room = 'bedroom'

h11 = Fixture('Hue', 'Skull')
h11.id = 11
h11.colorCorrection= [.92,.95,1]
h11.room = 'bedroom'

h12 = Fixture('Hue', 'Bedroom Hall')
h12.id = 12
h12.room = 'living room'

h13 = Fixture('Hue', 'Sink')
h13.id = 13
h13.room = 'kitchen'

h14 = Fixture('Hue', 'Pantry')
h14.id = 14
h14.room = 'kitchen'

h15 = Fixture('Hue', 'Cabinet Top')
h15.id = 15
h15.room = 'kitchen'

h17 = Fixture('Hue', 'Floor Lamp')
h17.id = 17
h17.room = 'bedroom'

h18 = Fixture('Hue', 'Corner')
h18.id = 18
h18.room = 'bedroom'

h19 = Fixture('Hue', 'Kitchen Door Right')
h19.id = 19
h19.room = 'living room'

h20 = Fixture('Hue', 'Kitchen Door Left')
h20.id = 20
h20.room = 'living room'

h21 = Fixture('Hue', 'Morty')
h21.id = 21

h24 = Fixture('Hue', 'Studio Monitors')
h24.id = 24
h24.room = 'bedroom'
h24.dimming = False
h24.color = False

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

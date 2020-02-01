import phue
import os
import yaml

#Prints all lights attached to hue bridge along with their IDs

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'user', 'config.yml')) as f:
    configFile = f.read()
configs = yaml.safe_load(configFile)
bridge = phue.Bridge(configs['hueIP'])


lights = bridge.get_light_objects('id')

for l in lights:
    print(l)
    print(lights[l].name)
    print('')

import phue
bridge = phue.Bridge('192.168.0.12')


lights = bridge.get_light_objects('id')

for l in lights:
    print(l)
    print(lights[l].name)
    print('')

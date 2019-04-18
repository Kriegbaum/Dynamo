import phue
bridge = phue.Bridge('10.0.0.20')


lights = bridge.get_light_objects('id')

for l in lights:
    print(l)
    print(lights[l].name)
    print('')

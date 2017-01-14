from phue import Bridge





bridge = Bridge('10.0.0.10')
bedroom = [7,8,10,11,17,14,15,16]
living_room = [1,2,3,4,5,6,13]
everything = [1,2,3,4,5,6,7,8,10,11,12,13,14]

print('Which Room?')
room = eval(input())

bridge.set_light(room, 'on', False)

from phue import Bridge
import opc


FCclient = opc.Client('localhost:7890')
pixels = [[0, 0, 0]] * 512
bridge = Bridge('10.0.0.10')
bedroom = [7,8,10,11,17,18,15,16]
living_room = [1,2,3,4,5,6,13]
everything = [1,2,3,4,5,6,7,8,10,11,12,13,14,15,16,17,18]


print('Which Room?')
room = eval(input())
if room == bedroom:
    FCclient.put_pixels(pixels)
    FCclient.put_pixels(pixels)
bridge.set_light(room, 'on', False)

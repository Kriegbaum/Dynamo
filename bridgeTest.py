from DYNAcore import *
fixture = False
for i in rooms['office']:
    if i.name == 'Whiteboard':
        fixture = i
print(fixture)
sendCommand(fixture, [0,255,0], 6)
time.sleep(5)
sendCommand(fixture, [255,0,255], 2)

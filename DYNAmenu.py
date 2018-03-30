from DYNAcore import *
################################################################################
#                       BEGIN MENU

def imageLoop():
    print('Input image name')
    print()
    pallettes = os.listdir(pallettesDir)
    for f in pallettes:
        print(f)
    filepath = input()
    filepath = os.path.join(pallettesDir, filepath)
    print('Which room?')
    group = rooms[input().lower()]
    print(group)
    for i in range(len(group)):
        if group[i].system == 'Hue':
            bridge.set_light(group[i].id, 'on', True)

    dynamic_image(filepath, group)

def albumLoop():
    print('Which room?')
    group = rooms[input().lower()]
    dynamic_album(group)

print('What will it be today?')
subroutine = input().lower()

if subroutine == 'image':
    imageLoop()

if subroutine == 'album':
    albumLoop()

if subroutine == 'off':
    print('Which room?')
    group = rooms[input().lower()]
    off(group)

else:
    print('Yeah right!')

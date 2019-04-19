from Tantallion import *
import gpiozero as GPIO
from signal import pause

button1 = GPIO.Button(19)
button2 = GPIO.Button(16)
button3 = GPIO.Button(26)
button4 = GPIO.Button(20)

saturatedIteration = 0
naturalIteration = 0
contrastIteration = 0

naturalLooks = ['Copper', 'Burma', 'Snowy', 'Japanese', 'Sacred', 'Eternity']
saturatedLooks = ['Jelly', 'Vaporwave', 'Intersection', 'Eiffel', 'Valtari', 'Umbrella', 'Void']
contrastLooks = ['Toplight', 'Night', 'Cabinet']

natualLooks = [scenes[x] for x in naturalLooks]
saturatedLooks = [scenes[x] for x in saturatedLooks]
contrastLooks = [scenes[x] for x in contrastLooks]

def run1():
    controllerDict['officeFC'].setArbitration('ButtonPress')
    roomDict['office'].scene(naturalLooks[naturalIteration])
    if naturalIteration > len(naturalLooks) - 1:
        naturalIteration = 0
def run2():
    controllerDict['officeFC'].setArbitration('ButtonPress')
    roomDict['office'].scene(saturatedLooks[saturatedIteration])
    if saturatedIteration > len(saturatedLooks) - 1:
        saturatedIteration = 0
def run3():
    controllerDict['officeFC'].setArbitration('ButtonPress')
    roomDict['office'].scene(contrastLooks[contrastIteration])
    if contrastIteration > len(contrastLooks) - 1:
        contrastIteration = 0
def run4():
    controllerDict['officeFC'].setArbitration('ButtonPress')
    roomDict['office'].off()

print('Initalizing...')
sendCommand([0,128], [255,255,255], 1, controllerDict['officeFC'])
time.sleep(1)
sendCommand([0,128], [0,0,0], 1, controllerDict['officeFC'])
time.sleep(1)
sendCommand([0,128], [255,255,255], 1, controllerDict['officeFC'])
time.sleep(1)
sendCommand([0,128], [0,0,0], 2, controllerDict['officeFC'])

button1.when_pressed = run1
button2.when_pressed = run2
button3.when_pressed = run3
button4.when_pressed = run4

pause()

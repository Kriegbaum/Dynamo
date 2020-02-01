# SeaCastle
SeaCastle is a control system for interfacing with various intelligent lighting platforms as well as relay power controllers. This is still very much under construction, and may be subject to major restructuring in the near future.

## Getting Started
Running any SeaCastle routine first involves invoking a Patch. An example patch yaml file is provided in SeaCastle/user/examplePatch.yml. At least one fixture must be declared to get SeaCastle up and running. A typical patch entry looks like this:

    Desk:
	    name: Desk Lamp
	    system: Hue
	    id: 1
	    room: office
More information on patch attributes can be found in the 'Patch' section.

Additionally, there is a config file located at SeaCastle/user/config.yml. This will contain platform-specific information (i.e. the IP address of a Philips Hue hub). See platform-specific documentation for more information.

Once a patch and config files are created, a patch object can be created.

    patch = Patch()
By default, the patch will read the patch file at SeaCastle/user/patch.yml, and a config file at SeaCastle/user/config.yml. Patch can be called to read files from a different location

    patch = Patch('/home/user1/patch.yml', '/home/user1/config.yml')
The Patch() constructor will build a structure for controlling all the fixtures declared in patch. These can be addressed by their name, and all implement a common set of commands. For instance

    desk_lamp = patch.fixture('Desk Lamp')

    #Sets a fixture to full white
    desk_lamp.setColor([255,255,255])

    #Returns color of fixture
    desk_lamp.getColor()
    >[255,255,255]

    office = patch.room('office')

    #Sets all fixtures in the office to red
    office.setColor([255,0,0])
   Some hardware may have additional capabilities, check the documentation for available features per fixture type.

# Generic Fixture Methods
These methods are also applicable to groups of fixtures by calling them on a room.
### Fixture.setColor(rgb, fadeTime=0.5)
Fades fixture to specified rgb value over specified time

 - rgb: 3 value array, 0-255
 - fadeTime: Time in seconds it take to complete fade
### Fixture.getColor()
Returns a 3 value array (0-255) showing the current value of fixture
### Fixture.on(fadeTime=0)
Turns fixture on to a warm white color
### Fixture.off(fadeTime=0)
Turns fixture off
### Fixture.fadeUp(amount=25)
Increases fixture brightness. Amount is 8-bit (0-255)
### Fixture.fadeDown(amount=25)
Decreases Fixture brightness

# Fixture Types
### WS281x - Simple
SeCastle can control addressable pixel fixtures (sold by Adafruit as NeoPixels, but also known as WS2811, WS2812, WS2812b, and WS2813). This implementation depends on the Fadecandy project created by scanlime. Check out her repo for more information on the hardware setup. opcBridge (located at SeaCastle/opcBridge) See opcBridge ReadMe for setup instructions.

##### Patch Declaration
These fixtures can be declared in one of two different types depending on the complexity of control desired. The simpler type is declared as 'Fadecandy'. A patch entry looks like this:

    endTable:
	    name: end table
	    system: Fadecandy
	    indexes: [1-28]
	    colorCorrection: [1, .85098, .57647]
	    proportion: .75
	    room: living room
	    grb: False
	    controller: livingroomFC
A little more detail on these patch attributes:

 - system: tells Patch() what sort of object this is
 - indexes: Which pixels make up this fixture. Will accept a combination of ranges. For instance [0-3, 12] will result in [0, 1, 2, 3, 12]
 - colorCorrection: Allows for a custom whitepoint setting. Red, green, and blue values get multiplied by [0], [2], and [3] respectively
 - proportion: describes maximum brightness for fixture. In this case, proporiton: .75 will cap this fixture's brightness at 75%
 - room: Where this fixture is placed
 - grb: many of these indexable fixture come with their color structure stacked in a grb order instead of an rgb order, flip this true if this is the case
 - Controller: References a controller defined in config.yml. This is a server running opcBridge.py. See opcBridge documentation for more information

##### Unique Methods
This fixture type does not implement any unique methods

### PixelArray
This type is another way of declaring a WS281x fixture, this time creating a 2D map of the pixels, allowing for more complex lighting effects.
##### Patch Declaration
Patch declaration for a PixelArray is identical to a Fadecandy fixture, except for the following

	system: PixelArray
    map:
    - [142-146, 147-157, 158-171, 172-181, 182-191]
    - [128-141]
    - [448-461]
    - [384-397]
    - [462-477, 478-485, 486-489, 490-496, 497-501, 502-511]
    - [398-409, 410-418, 419-427, 428-439, 440-447]
    - [320-325, 326-332, 333-339, 340-348, 349-354, 355-359, 360-365, 366-369]
    - [256-269, 270-278, 279-287, 288-296, 297-305]
    - [192-197, 198-208, 209-216, 217-222, 223-230, 231-241]
Each line in the map declaration will be made into a row in the array.

##### Unique Methods
In addition to the generic Fixture methods, a Pixel Array can do the following:

 - PixelArray.imageSample(): Will sample colors off of a digital image, and then crawl up and down the array, randomly assigning pixels new colors
 - PixelArray.fireflies(): Randomly highlights pixels to a selected color, and then fades them into the background
 - PixelArray.rollFade(): Fades the array to a new color, executing the fade one row at a time

## Hardware

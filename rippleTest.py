from DYNAcore import *

command1 = [fixtureDict['Whiteboard'], [255,255,255], 5]
command2 = [fixtureDict['Fan'], [255,0,0], 10]
command3 = [fixtureDict['Worklight'], [0,255,0], 2]

commands = [command1, command2, command3]

sendMultiCommand(commands, 'officeFC')

import sys
sys.path.append('..')

from Tantallion import Patch
import snapcast.control
import time
import asyncio
import yaml
import os

#Bring in seaCastle functions
patch = Patch()

#Load configs
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'muteMinder.yml')) as f:
    configs = f.read()
configs = yaml.safe_load(configs)

stereos = {}

class Stereo:
    def __init__(self, snapClient, room):
        self.snapClient = snapClient
        self.room = room
        self.muteCache = None
    def switch(self, state):
        if state:
            patch.room(self.room).relaysOn()
            time.sleep(1)
            patch.room(self.room).relaysOn()
        else:
            patch.room(self.room).relaysOff()
            time.sleep(1)
            patch.room(self.room).relaysOff()

for snapClient in configs['snapClients'].keys():
    stereos[snapClient] = Stereo(snapClient, configs['snapClients'][snapClient])



#########################SNAPSERVER GARBAGE#####################################
loop = asyncio.get_event_loop()
class MuteMinder(snapcast.control.Snapserver):
    def _on_client_volume_changed(self, data):
        self._clients.get(data.get('id')).update_volume(data)
        try:
            stereo = stereos[data['id']]
            muteState = data['volume']['muted']
            if muteState != stereo.muteCache:
                stereo.muteCache = muteState
                stereo.switch(not muteState)
        except:
            print('FAILURE')

@asyncio.coroutine
def create_muteminder(loop, host, port=1705, reconnect=False):
    server = MuteMinder(loop, host, port, reconnect)
    yield from server.start()
    return server
snapserver = loop.run_until_complete(create_muteminder(loop, '192.168.2.65'))

#Lets print out all the client IDs so its easy to nab them if the system changes
for client in snapserver.clients:
    print(client.identifier + ': ' + client.friendly_name)




loop.run_forever()

from phue import Bridge
bridge = Bridge('192.168.1.31')
bridge.set_light(24, 'on', False)

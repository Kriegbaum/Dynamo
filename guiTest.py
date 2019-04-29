from __future__ import absolute_import

from Tantallion import *
import sys

import time
from threading import Timer

import pygame
import OpenGL.GL as gl

from imgui.integrations.pygame import PygameRenderer
import imgui
import time

class UIframe:
    def __init__(self, tick):
        self.tick = tick
        self.timer = Timer(tick, self.unCache)
        self.lastUpdate = time.clock()
        self.commandCache = False
        self.argsCache = []

    def cache(self, command, args):
        self.commandCache = command
        self.argsCache = args

    def unCache(self):
        if self.commandCache == False:
            self.lastUpdate = time.clock()
        else:
            self.commandCache(*self.argsCache)
            self.commandCache = False
            self.lastUpdate = time.clock()

    def update(self):
        if time.clock() - self.lastUpdate < self.tick:
            if not self.timer.is_alive():
                self.timer = Timer(self.tick, self.unCache)
                self.timer.start()
        else:
            self.unCache()


patch = Patch()

rgb = patch.fixture('Worklight').getColor()
for r in rgb:
    r = int(r)
ui = UIframe(0.2)

def interface():
    imgui.new_frame()
    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("File", True):
            clicked_quit, selected_quit = imgui.menu_item("Quit", 'Cmd+Q', False, True)
            if clicked_quit:
                exit(1)
            imgui.end_menu()
        imgui.end_main_menu_bar()

    imgui.begin("Fixture Control: Worklight", True)
    changed, value = imgui.v_slider_int('red', 20, 100, rgb[0], 0, 255)
    if changed:
        rgb[0] = value
        ui.cache(patch.fixture('Worklight').setColor, [rgb, 0.2])
        ui.update()
    imgui.same_line(spacing=50)
    changed, value = imgui.v_slider_int('green', 20, 100, rgb[1], 0, 255)
    if changed:
        rgb[1] = value
        ui.cache(patch.fixture('Worklight').setColor, [rgb, 0.2])
        ui.update()
    imgui.same_line(spacing=50)
    changed, value = imgui.v_slider_int('blue', 20, 100, rgb[2], 0, 255)
    if changed:
        rgb[2] = value
        ui.cache(patch.fixture('Worklight').setColor, [rgb, 0.2])
        ui.update()

    imgui.same_line(spacing=50)
    imgui.end()

def main():
    pygame.init()
    size = 1024, 768

    pygame.display.set_mode(size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE)

    #imgui.create_context()
    impl = PygameRenderer()

    io = imgui.get_io()
    io.display_size = size
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            impl.process_event(event)
        interface()
        imgui.show_metrics_window()
        # note: cannot use screen.fill((1, 1, 1)) because pygame's screen
        #       does not support fill() on OpenGL sufraces
        gl.glClearColor(.1, .1, .1, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())

        pygame.display.flip()



if __name__ == "__main__":
    main()

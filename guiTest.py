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

class UIValues:
    def __init__(self, patch):
        self.values = {}
        self.showFixtureControl = True
        for f in patch.fixtures.values():
            self.values[f.name] = f.getColor()
            if not self.values[f.name]:
                self.values[f.name] = [0,0,0]


class UIframe:
    def __init__(self, tick):
        self.tick = tick
        self.timer = Timer(tick, self.unCache)
        self.lastUpdate = time.perf_counter()
        self.commandCache = False
        self.argsCache = []

    def cache(self, command, args):
        self.commandCache = command
        self.argsCache = args

    def unCache(self):
        if self.commandCache == False:
            self.lastUpdate = time.perf_counter()
        else:
            self.commandCache(*self.argsCache)
            self.commandCache = False
            self.lastUpdate = time.perf_counter()

    def update(self):
        if time.perf_counter() - self.lastUpdate < self.tick:
            if not self.timer.is_alive():
                self.timer = Timer(self.tick, self.unCache)
                self.timer.start()
        else:
            self.unCache()



patch = Patch()
values = UIValues(patch)
ui = UIframe(0.2)

def interface():
    imgui.new_frame()
    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("File", True):
            clicked_quit, selected_quit = imgui.menu_item("Quit", 'Cmd+Q', False, True)
            if clicked_quit:
                exit(1)
            imgui.end_menu()
        if imgui.begin_menu('Windows', True):
            clicked_fixtureC, selected_fixtureC = imgui.menu_item('Fixture Controls', shortcut=None)
            if clicked_fixtureC:
                if values.showFixtureControl:
                    values.showFixtureControl = False
                else:
                    values.showFixtureControl = True

            imgui.end_menu()
        imgui.end_main_menu_bar()

    if values.showFixtureControl:
        imgui.begin("Fixture Control", True)
        for r in patch.rooms.values():
            expanded, visible = imgui.collapsing_header(r.name)
            if expanded:
                imgui.indent()
                for f in r.fixtureList:
                    expanded, visible = imgui.collapsing_header(f.name)
                    rgb = values.values[f.name]
                    if expanded:
                        imgui.columns(2, f.name)
                        imgui.indent()
                        imgui.text('Red')
                        changed, value = imgui.slider_int('##int%sred' % f.name, rgb[0], 0, 255)
                        if changed:
                            rgb[0] = value
                            ui.cache(f.setColor, [rgb, 0.2])
                            ui.update()
                        imgui.text('Green')
                        changed, value = imgui.slider_int('##int%sgreen' % f.name, rgb[1], 0, 255)
                        if changed:
                            rgb[1] = value
                            ui.cache(f.setColor, [rgb, 0.2])
                            ui.update()
                        imgui.text('Blue')
                        changed, value = imgui.slider_int('##int%sblue' % f.name, rgb[2], 0, 255)
                        if changed:
                            rgb[2] = value
                            ui.cache(f.setColor, [rgb, 0.2])
                            ui.update()
                        imgui.next_column()
                        imgui.color_button('Color Sample', rgb[0]/255, rgb[1]/255, rgb[2]/255, width=100, height=100)
                        imgui.columns(1)
                        imgui.unindent()
                imgui.unindent()
        imgui.same_line(spacing=50)
        imgui.end()

def main():
    pygame.init()
    size = 1280, 960

    pygame.display.set_mode(size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE)

    #imgui.create_context()
    imgui.create_context()
    impl = PygameRenderer()

    io = imgui.get_io()
    io.display_size = size
    while 1:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            impl.process_event(event)
        interface()
        # note: cannot use screen.fill((1, 1, 1)) because pygame's screen
        #       does not support fill() on OpenGL sufraces
        gl.glClearColor(.1, .1, .1, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())

        pygame.display.flip()



if __name__ == "__main__":
    main()

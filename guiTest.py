from __future__ import absolute_import

from Tantallion import *
import sys

import pygame
import OpenGL.GL as gl

from imgui.integrations.pygame import PygameRenderer
import imgui
import time

patch = Patch()

def interface():
    imgui.new_frame()

    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("File", True):
            clicked_quit, selected_quit = imgui.menu_item("Quit", 'Cmd+Q', False, True)
            if clicked_quit:
                exit(1)
            imgui.end_menu()
        imgui.end_main_menu_bar()

    imgui.begin("Fixture Control", True)
    for f in patch.fixtures:
        fixture = patch.fixtures[f]
        if imgui.collapsing_header(fixture.name):
            if imgui.button('%s On' % fixture.name):
                fixture.on()
            imgui.same_line()
            if imgui.button('%s Off' % fixture.name):
                fixture.off()
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

        # note: cannot use screen.fill((1, 1, 1)) because pygame's screen
        #       does not support fill() on OpenGL sufraces
        gl.glClearColor(.1, .1, .1, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())

        pygame.display.flip()



if __name__ == "__main__":
    main()

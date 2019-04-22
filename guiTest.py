from __future__ import absolute_import

from Tantallion import *
import sys

import pygame
import OpenGL.GL as gl

from imgui.integrations.pygame import PygameRenderer
import imgui
import time

rgbVal = [0, 255, 255]
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

        imgui.new_frame()
        print(io.framerate)
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File", True):

                clicked_quit, selected_quit = imgui.menu_item(
                    "Quit", 'Cmd+Q', False, True
                )

                if clicked_quit:
                    exit(1)

                imgui.end_menu()
            imgui.end_main_menu_bar()

        imgui.begin("Custom window", True)
        changed, rgbVal[0] = imgui.slider_int('Desk Lamp Red Level', rgbVal[0], 0, 255)
        if changed:
            fixtureDict['Worklight'].setColor(rgbVal, 0)
            fixtureDict['Whiteboard'].setColor(rgbVal, 0)
        changed, rgbVal[1] = imgui.slider_int('Desk Lamp Green Level', rgbVal[1], 0, 255)
        if changed:
            fixtureDict['Worklight'].setColor(rgbVal, 0)
            fixtureDict['Whiteboard'].setColor(rgbVal, 0)
        changed, rgbVal[2] = imgui.slider_int('Desk Lamp Blue Level', rgbVal[2], 0, 255)
        if changed:
            fixtureDict['Worklight'].setColor(rgbVal, 0)
            fixtureDict['Whiteboard'].setColor(rgbVal, 0)
        imgui.end()

        # note: cannot use screen.fill((1, 1, 1)) because pygame's screen
        #       does not support fill() on OpenGL sufraces
        gl.glClearColor(.1, .1, .1, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())

        pygame.display.flip()



if __name__ == "__main__":
    main()

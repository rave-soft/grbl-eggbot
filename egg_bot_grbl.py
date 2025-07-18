#!/usr/bin/env python
import os

import inkex  # import the inkex Module so that we can use the debug function below
from inkex import Boolean

from svg_to_gcode.svg_parser import parse_root, Transformation
from svg_to_gcode.compiler import Compiler

from grbl_sender import GRBLSender
from svg_gcode import generate_custom_interface


class EggBot(inkex.EffectExtension):  #This is your program

    def add_arguments(self, pars):
        add_argument = pars.add_argument
        add_argument("--usb_port", help="USB Port")
        add_argument("--tab", type=self.arg_method('tab'), default=self.tab_help,
                     help="Defines which tab is active")
        add_argument("--pen_up_command", help="Pen Up Command")
        add_argument("--pen_down_command", help="Pen Down Command")
        add_argument("--directory", help="Directory")
        add_argument("--filename", help="Filename")
        add_argument("--delay_after_config_enabled", type=Boolean, help="Delay after config enabled")
        add_argument("--delay_after_config", type=int, help="Delay after config in seconds")
        add_argument("--movement_speed", type=int, help="Movement speed in mm/min")
        add_argument("--cutting_speed", type=int, help="Cutting speed in mm/min")


    def effect(self):  # This is a function this is were you define what your program in going to do
        # Act 1: --------------------------------------------------------------------------------DISPLAY A TEXT SAYING "HELLO WORLD" IN A MESSAGE BOX
        # inkex.utils.debug("Hello World!!!123123")  # Create the message box with the Hello world message
        # inkex.utils.debug("name: " + __name__)  # Create the message box with the Hello world message

        self.options.tab()

        return  # end of the program

    def tab_help(self):
        inkex.utils.errormsg("Switch to another tab to run the extensions.\n"
                             "No changes are made if the preferences or help tabs are active.\n\n"
                             "Tutorials, manuals and support can be found at\n"
                             " English support forum:\n"
                             "    http://www.cnc-club.ru/gcodetools\n"
                             "and Russian support forum:\n"
                             "    http://www.cnc-club.ru/gcodetoolsru")
        return

    def tab_generate_gcode(self):
        try:
            assert os.path.isdir(self.options.directory)
        except:
            inkex.utils.errormsg(f"{self.options.directory} is not a directory")
            exit(2)

        if self.options.filename:
            filename = self.options.filename
            if '.' not in filename:
                filename += ".gcode"
        else:
            filename = "untitled.gcode"

        output_path = os.path.join(self.options.directory, filename)

        root = self.document.getroot()

        custom_interface = generate_custom_interface(self.options.pen_up_command, self.options.pen_down_command)

        # grbl_conf = open("grbl.conf").read().splitlines()
        # grbl_conf = [
        #     '$32 = 0;',
        #     '$100 = 22.857',
        #     '$101 = 21.68;',
        #     '$110 = 10000;',
        #     '$111 = 10000;',
        #     '$120 = 50;',
        #     '$121 = 50;',
        #     '$130 = 140;',
        #     '$131 = 41;',
        # ]
        custom_header = [
            'G21',
        ]
        gcode_compiler = Compiler(custom_interface, movement_speed=4000, cutting_speed=1000, pass_depth=1, custom_header=custom_header)

        transformation = Transformation()

        transformation.add_translation(0, 0)

        width = root.get("width")
        height = root.get("height")
        if width == None or height == None:
            viewbox = root.get("viewBox")
            if viewbox:
                _, _, width, height = viewbox.split()

        if width == None or height == None:
            # raise ValueError("Unable to get width or height for the svg")
            print("Unable to get width and height for the svg")
            exit(1)

        # If it's a string and pt or px is in it, remove it
        if type(width) == str:
            width = width.replace("pt", "")
            width = width.replace("px", "")

        if type(height) == str:
            height = height.replace("pt", "")
            height = height.replace("px", "")

        scale_x = 140 / float(width)
        scale_y = 41 / float(height)
        scale = min(scale_x, scale_y)
        if scale > 1:
            scale = 1

        inkex.utils.errormsg(f"Scale: {scale} width: {width} height: {height}")

        transformation.add_scale(scale)



        curves = parse_root(root, transform_origin=False, root_transformation=transformation,
                            canvas_height=41)

        gcode_compiler.append_curves(curves)
        gcode_compiler.compile_to_file('output.gcode', passes=1)

        return self.document

    def tab_print(self):
        sender = GRBLSender( self.options.usb_port, 115200, 1)

        try:
            # Подключение
            if not sender.connect():
                inkex.utils.errormsg("Не удалось подключиться к GRBL")
                return 1

            status = sender.get_status()
            inkex.utils.errormsg(f"Статус GRBL: {status}")
            if not sender.send_gcode_file('test_sample.gcode'):
                inkex.utils.errormsg("Ошибка при отправке файла")
                return 1

            inkex.utils.errormsg("Файл успешно отправлен")
            return 0

        except KeyboardInterrupt:
            inkex.utils.errormsg("Прервано пользователем")
            sender.emergency_stop()
            return 1
        except Exception as e:
            inkex.utils.errormsg(f"Неожиданная ошибка: {e}")
            return 1
        finally:
            sender.disconnect()

if __name__ == '__main__':
    EggBot().run()

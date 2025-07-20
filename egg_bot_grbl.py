#!/usr/bin/env python
import os

import inkex  # import the inkex Module so that we can use the debug function below
from inkex import Boolean

from svg_to_gcode.svg_parser import parse_root, Transformation

from grbl_sender import GRBLSender
from svg_to_gcode.compiler import Compiler, interfaces

class DocumentDimensions:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def __str__(self):
        return f"Width: {self.width}, Height: {self.height}"

def generate_custom_interface(laser_off_command, laser_power_command):
    """Wrapper function for generating a Gcode interface with a custom laser power command"""

    class CustomInterface(interfaces.Gcode):
        """A Gcode interface with a custom laser power command"""

        def __init__(self):
            super().__init__()

        def laser_off(self):
            return f"{laser_off_command}"

        def set_laser_power(self, _):
            return f"{laser_power_command}"

    return CustomInterface

class EggBot(inkex.EffectExtension):  #This is your program

    def add_arguments(self, pars):
        add_argument = pars.add_argument
        add_argument("--usb_port", help="USB Port")
        add_argument("--tab", type=self.arg_method('tab'), default=self.tab_help,
                     help="Defines which tab is active")
        add_argument("--pen_up_command", help="Pen Up Command")
        add_argument("--pen_down_command", help="Pen Down Command")
        add_argument("--gcode_filepath", help="Filename of Gcode file")
        add_argument("--log_filepath", help="Filename of log file")
        add_argument("--invert_y_axis", type=Boolean, help="Invert Y Axis")
        add_argument("--movement_speed", type=int, help="Movement speed in mm/min")
        add_argument("--cutting_speed", type=int, help="Cutting speed in mm/min")


    def effect(self):  # This is a function this is were you define what your program in going to do
        self.options.tab()

        return  # end of the program

    def get_document_dimensions(self):
        root = self.document.getroot()
        width = root.get("width")
        height = root.get("height")

        if width is None or height is None:
            view_box = root.get("viewBox")
            if view_box:
                _, _, width, height = view_box.split()

        if width is None or height is None:
            # raise ValueError("Unable to get width or height for the svg")
            print("Unable to get width and height for the svg")
            exit(1)

        # Удаляем px/pt
        if width and type(width) == str:
            width = float(width.replace("px", "").replace("pt", ""))
        if height and type(height) == str:
            height = float(height.replace("px", "").replace("pt", ""))

        return DocumentDimensions(width, height)

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

        output_path = self.options.gcode_filepath
        root = self.document.getroot()
        custom_interface = generate_custom_interface(self.options.pen_up_command, self.options.pen_down_command)

        custom_header = [
            'G21;',
            'G10 P0 L20 X0 Y20.5;',
        ]
        gcode_compiler = Compiler(custom_interface,
                  movement_speed=self.options.movement_speed,
                  cutting_speed=self.options.cutting_speed,
                  pass_depth=1,
                  custom_header=custom_header
        )

        transformation = Transformation()

        transformation.add_translation(0, 0)

        dimensions = self.get_document_dimensions()
        width = dimensions.width
        height = dimensions.height

        scale_x = 140 / float(width)
        scale_y = 41 / float(height)
        scale = min(scale_x, scale_y)
        if scale > 1:
            scale = 1

        transformation.add_scale(scale)

        curves = parse_root(root, transform_origin=not self.options.invert_y_axis, root_transformation=transformation, canvas_height=41)

        gcode_compiler.append_curves(curves)



        gcode_compiler.compile_to_file(output_path, passes=1)

        return self.document

    def tab_print(self):
        output_path = self.options.gcode_filepath
        if not os.path.exists(output_path):
            inkex.utils.errormsg("Файл не найден")
            return 1
        logfile = self.options.log_filepath
        if not os.path.exists(logfile):
            logfile = None

        sender = GRBLSender( self.options.usb_port, 115200, 1, logfile)

        try:
            # Подключение
            if not sender.connect():
                inkex.utils.errormsg("Не удалось подключиться к GRBL")
                return 1

            status = sender.get_status()
            inkex.utils.errormsg(f"Статус GRBL: {status}")
            if not sender.send_gcode_file(output_path):
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

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
        add_argument("--tab", type=self.arg_method('tab'), default=self.tab_generate_gcode,
                     help="Defines which tab is active")
        add_argument("--pen_up_command", help="Pen Up Command")
        add_argument("--pen_down_command", help="Pen Down Command")
        add_argument("--gcode_filepath", help="Filename of Gcode file")
        add_argument("--log_filepath", help="Filename of log file")
        add_argument("--invert_y_axis", type=Boolean, help="Invert Y Axis")
        add_argument("--movement_speed", type=int, help="Movement speed in mm/min")
        add_argument("--cutting_speed", type=int, help="Cutting speed in mm/min")
        add_argument("--x_circumference", type=int, help="X circumference")
        add_argument("--y_circumference", type=int, help="Y circumference")
        add_argument("--x_axis_maximum_rate", type=int, help="X-axis maximum rate, mm/min")
        add_argument("--y_axis_maximum_rate", type=int, help="Y-axis maximum rate, mm/min")
        add_argument("--x_axis_accel", type=int, help="X-axis acceleration, mm/sec^2")
        add_argument("--y_axis_accel", type=int, help="Y-axis acceleration, mm/sec^2")
        add_argument("--bed_width", type=int, help="X-axis maximum travel, millimeters")
        add_argument("--bed_height", type=int, help="Y-axis maximum travel, millimeters")


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

    def tab_generate_gcode(self):

        output_path = self.options.gcode_filepath
        root = self.document.getroot()
        custom_interface = generate_custom_interface(self.options.pen_up_command, self.options.pen_down_command)

        bed_width = int(self.options.bed_width)
        bed_height = int(self.options.bed_height)

        custom_header = [
            'G21',
            'G10 P0 L20 X0 Y%.2f' % (bed_height / 2),
        ]
        custom_footer = [
            self.options.pen_up_command,
            'G1 X0 Y%.2f' % (bed_height / 2),
        ]
        gcode_compiler = Compiler(custom_interface,
                  movement_speed=self.options.movement_speed,
                  cutting_speed=self.options.cutting_speed,
                  pass_depth=1,
                  custom_header=custom_header,
                  custom_footer=custom_footer
        )

        transformation = Transformation()

        transformation.add_translation(0, 0)

        dimensions = self.get_document_dimensions()
        width = dimensions.width
        height = dimensions.height

        scale_x = bed_width / float(width)
        scale_y = bed_height / float(height)
        scale = min(scale_x, scale_y)
        if scale > 1:
            scale = 1

        transformation.add_scale(scale)

        curves = parse_root(root, transform_origin=not self.options.invert_y_axis, root_transformation=transformation, canvas_height=41)

        gcode_compiler.append_curves(curves)



        gcode_compiler.compile_to_file(output_path, passes=1)

        return self.document
    def tab_connection(self):
        sender = GRBLSender(self.options.usb_port)

        try:
            # Подключение
            if not sender.connect():
                inkex.utils.errormsg("Не удалось подключиться к GRBL")
                return 1

            status = sender.get_status()
            inkex.utils.errormsg(f"Статус GRBL:\n {status}")

            configuration = sender.get_configuration()
            inkex.utils.errormsg(f"Конфигурация GRBL:\n {configuration}")

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

    def tab_print(self):
        output_path = self.options.gcode_filepath
        if not os.path.exists(output_path):
            inkex.utils.errormsg("Файл не найден")
            return 1
        logfile = self.options.log_filepath
        if not os.path.exists(logfile):
            logfile = None

        sender = GRBLSender(self.options.usb_port, logfile=logfile)

        try:
            # Подключение
            if not sender.connect():
                inkex.utils.errormsg("Не удалось подключиться к GRBL")
                return 1

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

    def tab_configure_grbl(self):

        sender = GRBLSender(self.options.usb_port)

        try:
            # Подключение
            if not sender.connect():
                inkex.utils.errormsg("Не удалось подключиться к GRBL")
                return 1

            status = sender.get_status()
            inkex.utils.errormsg(f"Статус GRBL: {status}")
            lines = [
                '$1 = 255',
                '$32 = 0',
                "$100 = %.3f" % (3200 / int(self.options.x_circumference)),
                "$101 = %.3f" % (3200 / int(self.options.y_circumference)),
                '$110 = %d' % int(self.options.x_axis_maximum_rate),
                '$111 = %d' % int(self.options.y_axis_maximum_rate),
                '$120 = %d' % int(self.options.x_axis_accel),
                '$121 = %d' % int(self.options.y_axis_accel),
                '$130 = %d' % int(self.options.bed_width),
                '$131 = %d' % int(self.options.bed_height),
            ]

            if not sender.send_gcode_lines(lines):
                inkex.utils.errormsg("Ошибка при отправке конфигурации")
                return 1

            inkex.utils.errormsg("Конфигурация успешно установлена")
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

    def tab_calibrate_grbl(self):

        sender = GRBLSender(self.options.usb_port)

        try:
            # Подключение
            if not sender.connect():
                inkex.utils.errormsg("Не удалось подключиться к GRBL")
                return 1

            status = sender.get_status()
            inkex.utils.errormsg(f"Статус GRBL : {status}")
            height_center =  int(self.options.bed_height) / 2
            lines = [
                'G21',
                'G90',
                'G17',
                'G94',
                self.options.pen_up_command,
                'G10 P0 L20 X0 Y%.3f' % height_center,
                self.options.pen_down_command,
                'G1 Y%d F%d' % (int(self.options.bed_height), int(self.options.cutting_speed)),
                'G1 X%d' % int(self.options.bed_width),
                'G1 Y0',
                'G1 X0',
                'G0 X0 Y%.3f' % height_center,
                self.options.pen_up_command,
            ]

            if not sender.send_gcode_lines(lines):
                inkex.utils.errormsg("Ошибка при отправке команд")
                return 1

            inkex.utils.errormsg("Команды успешно отправлены")
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

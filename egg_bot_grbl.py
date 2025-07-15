#!/usr/bin/env python

import inkex  # import the inkex Module so that we can use the debug function below
from inkex import Boolean
from grbl_sender import GRBLSender


class EggBot(inkex.EffectExtension):  #This is your program

    def add_arguments(self, pars):
        add_argument = pars.add_argument
        add_argument("--usb_port", help="USB Port")
        add_argument("--tab", type=self.arg_method('tab'), default=self.tab_help,
                     help="Defines which tab is active")
        add_argument("--color_param", type=int, help="An example option, put your options here")
        add_argument("--int_param", type=int, help="An example option, put your options here")
        add_argument("--float_param", type=float, help="An example option, put your options here")
        add_argument("--option_param", help="An example option, put your options here")
        add_argument("--bool_param", type=Boolean, help="An example option, put your options here")

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

    def tab_about(self):
        return self.tab_help()

    def tab_preferences(self):
        return self.tab_help()

    def tab_options(self):
        return self.tab_help()

    def tab_connection(self):
        sender = GRBLSender('/dev/ttyUSB0', 115200, 1)

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

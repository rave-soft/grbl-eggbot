from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces


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

# custom_interface = generate_custom_interface(f"M3 S20;", f"M3 S70;")
#
#
# grbl_conf = open("grbl.conf").read().splitlines()
# # Instantiate a compiler, specifying the custom interface and the speed at which the tool should move.
# gcode_compiler = Compiler(custom_interface, movement_speed=1000, cutting_speed=300, pass_depth=1, custom_header=grbl_conf)
#
# curves = parse_file("drawing.svg", canvas_height=41, transform_origin=False) # Parse an svg file into geometric curves
#
# gcode_compiler.append_curves(curves)
# gcode_compiler.compile_to_file("drawing.gcode")
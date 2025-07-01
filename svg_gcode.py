from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces

class CustomInterface(interfaces.Gcode):
    def __init__(self):
        super().__init__()
        self.fan_speed = 1

    # Override the laser_off method such that it also powers off the fan.
    def laser_off(self):
        return f"M3 S20;"

    # Override the set_laser_power method
    def set_laser_power(self, power):
        return f"M3 S70;"


grbl_conf = open("grbl.conf").read().splitlines()
# Instantiate a compiler, specifying the custom interface and the speed at which the tool should move.
gcode_compiler = Compiler(CustomInterface, movement_speed=1000, cutting_speed=300, pass_depth=1, custom_header=grbl_conf)

curves = parse_file("drawing.svg", canvas_height=41, transform_origin=False) # Parse an svg file into geometric curves

gcode_compiler.append_curves(curves)
gcode_compiler.compile_to_file("drawing.gcode")
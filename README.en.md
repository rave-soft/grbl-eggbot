# GRBL EggBot Extension for Inkscape
## Description
This extension allows converting SVG files into G-Code and sending them to a GRBL controller for EggBot operation.
## Features
- Generating G-Code from SVG
- Sending G-Code to a GRBL controller
- Configuration of speed and other parameters
- Support for custom commands for pen up/down
## Installation
1. Copy the `grbl-eggbot` folder to the Inkscape extensions directory.
2. You can find the extensions directory in Inkscape settings.

   `Edit -> Preferences -> System -> User extensions`
3. Restart Inkscape.
4. The extension should appear in the menu `Extensions -> Eggbot GRBL`.

## Usage
1. Create or open an SVG file.
2. Go to the menu `Extensions -> Eggbot GRBL`.
3. Select the `Generate G-Code` tab and configure the settings:
   - Movement speed: Speed of the pen moving between points (mm/min).
   - Cutting speed: Speed at which the pen draws (mm/min). 
   - Pen up/down commands: GRBL commands for pen lifting and lowering.
4. Specify the output path for the G-Code file.
5. Click `Apply`.
6. Go to the `Print G-Code File` tab and configure the settings:
   - GRBL controller USB port: Specify the port your GRBL controller is connected to.
   - Log file path (optional): Specify a path to save logs.
7. Click `Apply`.

## GRBL Configuration
Go to the `GRBL Configuration` tab and set:
  - **GRBL controller USB port:** Specify the port your GRBL controller is connected to.
  - **X/Y Circumference:** Circumference for X and Y axes (affects step calculations).
  - **Bed Width/Height:** Print area size in X and Y axes (mm).
  - **X/Y Axis Acceleration:** Acceleration for X and Y axes (mm/sec^2).
  - **X/Y Axis Maximum Rate:** Maximum movement speed for X and Y axes (mm/min).
Click `Apply`.

## Calibration
1. Select the `Calibration` tab.
2. Configure:
   - GRBL controller USB port: COM3 (Windows) /dev/ttyUSB0 (Linux)
3. Click Apply.
   During calibration, GRBL commands are sent to draw the print area boundaries.
   Based on the result, you can adjust pen up/down commands, area boundaries, and drawing speed.

## Examples

### Example 1: Generating G-Code
1. Create an SVG file with a simple contour.
2. Open Inkscape and go to `Extensions -> Eggbot GRBL`.
3. Configure:
  - Movement speed: 4000 mm/min
  - Cutting speed: 1000 mm/min
  - Pen up/down commands: M3 S75; / M3 S90;
1. Output file path: `/path/to/output.gcode`
2. Click `Apply`.

### Example 2: Sending G-Code to Controller
1. Make sure your GRBL controller is connected to your computer.
2. Open Inkscape and go to `Extensions -> Eggbot GRBL`.
3. Select the `Print G-Code File` tab.
4. Configure:
   - GRBL controller USB port: `COM3` (Windows) `/dev/ttyUSB0` (Linux)
   - Path to G-Code file: `/path/to/output.gcode`
   - Path to log file: `/path/to/output.log` (optional)
5. Click Apply.

## Tips and Recommendations
- The extension allows sending G-Code directly to the GRBL controller, but for convenience, it is better to use other G-Code printing applications, such as Universal G-Code Sender.
- To use other applications for printing, generate G-Code into a file and open it in another application.
- GRBL configuration is saved directly in GRBL, so to confirm it is correct, send the command `$$` from your chosen printing application.
- If using another G-Code printing application, make sure it supports GRBL.

## Requirements
Inkscape 1.4.2+
Python 3.7+

## License
GNU GENERAL PUBLIC LICENSE
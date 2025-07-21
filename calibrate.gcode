G21 ; millimeters
G90 ; absolute coordinate
G17 ; XY plane
G94 ; units per minute feed rate mode
M3 S70 ; Pen Up

G10 P0 L20 X0 Y21; Reset Coordinates

; Go to zero location
G0 X0 Y0

M3 S90; Pen Down
; Create rectangle
G1 X0 Y0 F4000
G1 Y42
G1 X144
G1 Y0
G1 X0


G0 X0 Y21; Go to zero location

M3 S70 ; Pen Up

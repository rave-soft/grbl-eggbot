import sys
import glob
import serial

def find_port():
    try:
        from serial.tools.list_ports import comports
    except ImportError:
        return None
    if comports:
        com_ports_list = comports()
        ebb_port = None
        for port in com_ports_list:
            if port.description.startswith("USB"):
                ebb_port = port.device
                break
        return ebb_port
    return None


if __name__ == '__main__':
    print(find_port())
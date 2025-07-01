import asyncio
import time

import serial
import serial_asyncio


class GRBLProtocol(asyncio.Protocol):
    def __init__(self):
        self.transport = None
        self.buffer = b""

    def connection_made(self, transport):
        self.transport = transport
        print("Serial port opened")
        # self.transport.write(b"?\n")

    def data_received(self, data):
        self.buffer += data
        if b"\n" in self.buffer:
            lines = self.buffer.split(b"\n")
            for line in lines[:-1]:
                print(f"Received: {line.decode()}")
            self.buffer = lines[-1]

    def connection_lost(self, exc):
        print("Serial port closed")
        asyncio.get_event_loop().stop()

    def write(self, data):
        self.transport.write(b"{}\n", data)

async def main():
    loop = asyncio.get_event_loop()
    try:
        transport, protocol = await serial_asyncio.create_serial_connection(
            loop, GRBLProtocol, "/dev/ttyUSB0", baudrate=115200
        )
    except Exception as e:
        print(f"Error opening serial port: {e}")
        return

    try:
        await asyncio.Future()  # Keep the loop running until stopped
    except asyncio.CancelledError:
        pass
    finally:
        if transport:
            transport.close()

def main2():
    ser = serial.Serial('/dev/ttyUSB0', 115200)
    # ser.write(str.encode("\r\n\r\n"))
    time.sleep(2)  # Wait for Printrbot to initialize
    ser.reset_input_buffer()
    print(ser.readall().decode('utf-8'))
    time.sleep(1)
    print(ser.readall().decode('utf-8'))
    ser.close()

if __name__ == "__main__":
    # asyncio.run(main())
    main2()
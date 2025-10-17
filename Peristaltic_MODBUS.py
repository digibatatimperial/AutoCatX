#!/usr/bin/env python3

# -*- coding: utf-8 -*-
 
"""

JBT-B/C peristaltic pump — Modbus RTU control (locked to discovered settings)
 
Found:

  device_id = 1

  SPEED_REG = 999 (literal)

  COILS: START/STOP = 999 (single-coil), DIRECTION = 1000
 
Demo flow:

  set_direction(True) → set_speed(500) → start → read (5×) → stop

"""
 
import time

from pymodbus.client import ModbusSerialClient

from pymodbus.framer import FramerType

from pymodbus.exceptions import ModbusException
 
# ---------- Discovered settings ----------

PORT = "COM5"

DEVICE_ID = 1

SPEED_REG = 999            # Fn06 write setpoint, Fn04 read feedback

STARTSTOP_COIL = 999       # single-coil: True=start, False=stop

DIRECTION_COIL = 1000      # True=forward, False=reverse
 
# ---------- Serial config (per manual: 9600 8E1) ----------

client = ModbusSerialClient(

    port=PORT,

    framer=FramerType.RTU,

    baudrate=9600,

    bytesize=8,

    parity="E",

    stopbits=1,

    timeout=1.5,

    retries=2,

)
 
def write_single_coil(addr: int, value: bool):

    # Try Fn05 first; if device prefers Fn15, fall back.

    rr = client.write_coil(address=addr, value=bool(value), device_id=DEVICE_ID)

    if rr.isError():

        rr = client.write_coils(address=addr, values=[bool(value)], device_id=DEVICE_ID)

    return rr
 
def set_direction(forward: bool = True):

    return write_single_coil(DIRECTION_COIL, bool(forward))
 
def start_pump():

    return write_single_coil(STARTSTOP_COIL, True)
 
def stop_pump():

    return write_single_coil(STARTSTOP_COIL, False)
 
def set_speed(speed: int):

    # Integer units per controller (often rpm or mL/min * factor)

    return client.write_register(address=SPEED_REG, value=int(speed), device_id=DEVICE_ID)
 
def read_speed_input():

    # Fn04 Input Register 999 (feedback). Some firmwares update slowly—retry.

    rr = client.read_input_registers(address=SPEED_REG, count=1, device_id=DEVICE_ID)

    if rr.isError():

        return None

    return rr.registers[0]
 
def main():

    if not client.connect():

        raise SystemExit("❌ Could not open COM port.")

    print(f"✅ Connected on {PORT}")
 
    # Direction

    rr = set_direction(True);      print("direction:", "OK" if not rr.isError() else rr)
 
    # Set speed

    rr = set_speed(50);           print("set_speed(50):", "OK" if not rr.isError() else rr)
 
    # Start

    rr = start_pump();             print("start:", "OK" if not rr.isError() else rr)
 
    # Give the controller time to ramp/update then read a few times

    time.sleep(0.5)

    for i in range(5):

        val = read_speed_input()

        print(f"read_speed [{i+1}/5]:", val if val is not None else "read error")

        time.sleep(0.5)
 
    # Stop

    rr = stop_pump();              print("stop:", "OK" if not rr.isError() else rr)
 
    client.close()

    print("🔌 Disconnected.")
 
if __name__ == "__main__":

    main()

 
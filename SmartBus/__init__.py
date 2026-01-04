# -*- coding: utf-8 -*-
#
#  __init__.py
#
#  Copyright 2026 Thomas Castleman <batcastle@draugeros.org>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
"""
SmartBus Driver for TAFY

SmartBus is an I2C-backed communications bus designed to enable devices like smart magazines,
powered barrel extensions, and more. Is has 5 pins with the following pin out:

 - Power (3.3v, 1amp)
 - Ground
 - I2C SDA
 - I2C SCL
 - ID/Sense

The ID/Sense line should be shorted to power with a resistor. This resistor should have a specific
value to communicate what type of device it is.
"""
from machine import Pin, ADC, I2C

INTERNAL_CONFIG = {
        "VERSION": "v1.2",
        "SmartBus_enabled": True,
        "SmartBus_SDA": 20,
        "SmartBus_SCL": 21,
        "SmartBus_ID_Downstream": 26,
        "SmartBus_ID_Upstream": 27,
        "SmartBus_Freq": 100000,
        "SmartBus_Internal_Resistor": 47000,
    }

MANIFEST = None

COMMS = None
ID = None
KNOWN_RESISTORS = []
CURRENT_RESISTANCE = 0


def init(config, locks: dict):
    """Initialize and configure SmartBus"""
    global COMMS, ID, MANIFEST

    if not config.get("main", "SmartBus_enabled"):
        return

    print(f"Initializing SmartBus {INTERNAL_CONFIG['VERSION']}!")
    MANIFEST = config.get_section("SmartBus_Manifest")

    if "SmartBus_SDA" in config.get_section("pin_out"):
        INTERNAL_CONFIG["SmartBus_SDA"] = config.get("pin_out", "SmartBus_SDA")

    if "SmartBus_SCL" in config.get_section("pin_out"):
        INTERNAL_CONFIG["SmartBus_SCL"] = config.get("pin_out", "SmartBus_SCL")

    if "SmartBus_ID_Downstream" in config.get_section("pin_out"):
        INTERNAL_CONFIG["SmartBus_ID_Downstream"] = config.get("pin_out",
                                                                   "SmartBus_ID_Downstream")

    if "SmartBus_ID_Upstream" in config.get_section("pin_out"):
        INTERNAL_CONFIG["SmartBus_ID_Upstream"] = config.get("pin_out",
                                                                 "SmartBus_ID_Upstream")

    if "SmartBus_Freq" in config.get_section("main"):
        INTERNAL_CONFIG["SmartBus_Freq"] = config.get("main", "SmartBus_Freq")

    if "SmartBus_Internal_Resistor" in config.get_section("main"):
        INTERNAL_CONFIG["SmartBus_Internal_Resistor"] = config.get("main",
                                                                       "SmartBus_Internal_Resistor")

    if INTERNAL_CONFIG["SmartBus_SCL"] in config.get("pin_out", "I2C_MAP")["0"]:
        if INTERNAL_CONFIG["SmartBus_SDA"] in config.get("pin_out", "I2C_MAP")["0"]:
            bus = 0
    elif INTERNAL_CONFIG["SmartBus_SCL"] in config.get("pin_out", "I2C_MAP")["1"]:
        if INTERNAL_CONFIG["SmartBus_SDA"] in config.get("pin_out", "I2C_MAP")["1"]:
            bus = 1
    else:
        raise RuntimeError("SmartBus I2C lines not on same bus")

    with locks["i2c_sb"]:
        COMMS = I2C(bus, scl=Pin(INTERNAL_CONFIG["SmartBus_SCL"], Pin.PULL_UP),
                    sda=Pin(INTERNAL_CONFIG["SmartBus_SDA"], Pin.PULL_UP),
                    freq=INTERNAL_CONFIG["SmartBus_Freq"])
        ID = {"upstream": ADC(INTERNAL_CONFIG["SmartBus_ID_Downstream"]),
              "downstream": ADC(INTERNAL_CONFIG["SmartBus_ID_Upstream"])}
        results = COMMS.scan()
        return scan


def scan(config, locks):
    """Scan SmartBus for new devices"""
    # Need to figure out allowed slop here!
    if get_current_resistance():
        pass

def get_current_resistance():
    """Get the current resistance on client side of voltage divider"""
    upstream = ID["upstream"].read_u16()
    downstream = ID["downstream"].read_u16()
    return (INTERNAL_CONFIG["SmartBus_Internal_Resistor"] * downstream) / (upstream - downstream)

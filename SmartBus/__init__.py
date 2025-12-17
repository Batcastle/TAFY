# -*- coding: utf-8 -*-
#
#  __init__.py
#
#  Copyright 2025 Thomas Castleman <batcastle@draugeros.org>
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
from machine import Pin
from machine import I2C as i2c

INTERNAL_CONFIG = {
        "VERSION": "v1.2",
        "SmartBus_enabled": True,
        "SmartBus_SDA": 20,
        "SmartBus_SCL": 21,
        "SmartBus_ID": 26,
        "SmartBus_Freq": 100000
    }


I2C = None


def init(config, manifest):
    """Initialize and configure SmartBus"""
    print(f"Initializing SmartBus {INTERNAL_CONFIG['VERSION']}!")
    if "SmartBus_enabled" in config:
        INTERNAL_CONFIG["SmartBus_enabled"] = config["SmartBus_enabled"]
    if "SmartBus_SDA" in config:
        INTERNAL_CONFIG["SmartBus_SDA"] = config["SmartBus_SDA"]
    if "SmartBus_SCL" in config:
        INTERNAL_CONFIG["SmartBus_SCL"] = config["SmartBus_SCL"]
    if "SmartBus_ID" in config:
        INTERNAL_CONFIG["SmartBus_ID"] = config["SmartBus_ID"]
    if "SmartBus_Freq" in config:
        INTERNAL_CONFIG["SmartBus_Freq"] = config["SmartBus_Freq"]

    if INTERNAL_CONFIG["SmartBus_enabled"]:
        I2C = i2c(1, scl=Pin(INTERNAL_CONFIG["SmartBus_SCL"]), sda=Pin(INTERNAL_CONFIG["SmartBus_SDA"]), freq=INTERNAL_CONFIG["SmartBus_Freq"])
        results = I2C.scan()

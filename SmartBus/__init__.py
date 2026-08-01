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

 - Power (3.3v, 1A)
 - Ground
 - I2C SDA
 - I2C SCL
 - ID/Sense

The ID/Sense line should be shorted to GND with a resistor. This resistor should have a specific
value to communicate what type of device it is.
"""
from machine import Pin, ADC, I2C
import time

class SmartBus:
    """SmartBus Management Class"""
    def __init__(self, config, locks):
        INTERNAL_CONFIG = {
            "VERSION": "v1.3",
            "SmartBus_enabled": True,
            "SmartBus_SDA": 20,
            "SmartBus_SCL": 21,
            "SmartBus_ID_Downstream": 26,
            "SmartBus_ID_Upstream": 27,
            "SmartBus_Freq": 100000,
            "SmartBus_Internal_Resistor": 47000,
        }

        self.MANIFEST = None
        self.drivers_to_load = []
        self.drivers_to_unload = []
        self.drivers = {}
        self.COMMS = None
        self.ID = None
        self.KNOWN_RESISTORS = []
        self.CURRENT_RESISTANCE = 0
        self.CONNECTED_DEVICES = {}

        print(f"Initializing SmartBus {self.INTERNAL_CONFIG['VERSION']}!")
        self.MANIFEST = config.get_section("SmartBus_Manifest")

        if "SmartBus_SDA" in config.get_section("pin_out"):
            self.INTERNAL_CONFIG["SmartBus_SDA"] = config.get("pin_out", "SmartBus_SDA")

        if "SmartBus_SCL" in config.get_section("pin_out"):
            self.INTERNAL_CONFIG["SmartBus_SCL"] = config.get("pin_out", "SmartBus_SCL")

        if "SmartBus_ID_Downstream" in config.get_section("pin_out"):
            self.INTERNAL_CONFIG["SmartBus_ID_Downstream"] = config.get("pin_out",
                                                                        "SmartBus_ID_Downstream")

        if "SmartBus_ID_Upstream" in config.get_section("pin_out"):
            self.INTERNAL_CONFIG["SmartBus_ID_Upstream"] = config.get("pin_out",
                                                                      "SmartBus_ID_Upstream")

        if "SmartBus_Freq" in config.get_section("main"):
            self.INTERNAL_CONFIG["SmartBus_Freq"] = config.get("main", "SmartBus_Freq")

        if "SmartBus_Internal_Resistor" in config.get_section("main"):
            self.INTERNAL_CONFIG["SmartBus_Internal_Resistor"] = config.get("main",
                                                                            "SmartBus_Internal_Resistor")

        if self.INTERNAL_CONFIG["SmartBus_SCL"] in config.get("pin_out", "I2C_MAP")["0"]:
            if self.INTERNAL_CONFIG["SmartBus_SDA"] in config.get("pin_out", "I2C_MAP")["0"]:
                bus = 0
            else:
                raise RuntimeError("INTERNAL I2C lines not on same bus")
        elif self.INTERNAL_CONFIG["SmartBus_SCL"] in config.get("pin_out", "I2C_MAP")["1"]:
            if self.INTERNAL_CONFIG["SmartBus_SDA"] in config.get("pin_out", "I2C_MAP")["1"]:
                bus = 1
            else:
                raise RuntimeError("INTERNAL I2C lines not on same bus")
        else:
            raise RuntimeError("SmartBus I2C lines not on same bus")

        with locks["i2c_sb"]:
            self.COMMS = I2C(bus, scl=Pin(self.INTERNAL_CONFIG["SmartBus_SCL"], Pin.PULL_UP),
                        sda=Pin(self.INTERNAL_CONFIG["SmartBus_SDA"], Pin.PULL_UP),
                        freq=self.INTERNAL_CONFIG["SmartBus_Freq"])
            self.ID = {"upstream": ADC(self.INTERNAL_CONFIG["SmartBus_ID_Upstream"]),
                  "downstream": ADC(self.INTERNAL_CONFIG["SmartBus_ID_Downstream"])}

    def _scan_i2c(self, locks):
        """Scan I2C Bus"""
        with locks["i2c_sb"]:
            return self.COMMS.scan()

    def _get_current_resistance(self):
        """Get the current resistance on client side of voltage divider"""
        upstream = self.ID["upstream"].read_uv()
        downstream = self.ID["downstream"].read_uv()
        # If nothing is hooked up yet, we need to say no resistance
        if (upstream - downstream) == 0:
            return 0
        return (self.INTERNAL_CONFIG["SmartBus_Internal_Resistor"] * downstream) / (upstream - downstream)

    def scan(self, locks):
        """Run a full SmartBus scan"""
        # Need to figure out allowed slop here!
        resistance = [get_current_resistance()]
        time.sleep_ms(5)
        resistance.append(get_current_resistance())
        time.sleep_ms(5)
        resistance.append(get_current_resistance())
        resistance = sum(resistance) / 3

        # NOTHING CONNECTED
        if resistance == 0:
            # No devices connected. Nothing to do.
            if self.KNOWN_RESISTORS != []:
                for each in self.KNOWN_RESISTORS:
                    self.deregister_device(each)
            self.drivers_to_load = {}
            return {}
        # Calculate new resistor
        if self.KNOWN_RESISTORS != []:
            for each in self.KNOWN_RESISTORS:
                resistance = resistance - (1 / each)
            # resistance should now contain the value of 1 over the new resistor

            if resistance < 0:
                # RESISTOR HAS BEEN REMOVED!
                self.deregister_device(resistance)
            else:
                # RESISTOR ADDED
                resistance = round(1 / resistance)
                self.register_new_device(resistance)
        else:
            # RESISTOR ADDED
                resistance = round(1 / resistance)
                self.register_new_device(resistance)

    def register_new_device(self, resistance: float):
        """Register new device:
        - Add known resistor
        - Add pointer to new driver to load
        - Add to known devices dict with new, unique ID
        """
        # RESISTOR ADDEED
        self.KNOWN_RESISTORS.append(resistance)
        for each in enumerate(sort(self.MANIFEST["smartbus"]["devices"].keys())):
            if each[0] == 0:
                if resistance < (int(self.MANIFEST["smartbus"]["devices"][each[0]]) * 1.15):
                    # NEED TO FIGURE OUT HOW TO ASSIGN IDS
                    pass
            elif each[0] < (len(sort(self.MANIFEST["smartbus"]["devices"].keys())) - 1):
                if resistance > (int(self.MANIFEST["smartbus"]["devices"][each[0]]) * 0.85):
                    if resistance < (int(self.MANIFEST["smartbus"]["devices"][each[0]]) * 1.15):
                        # NEED TO FIGURE OUT HOW TO ASSIGN IDS
                        pass
            else:
                if resistance > (int(self.MANIFEST["smartbus"]["devices"][each]) * 0.85:
                    # NEED TO FIGURE OUT HOW TO ASSIGN IDS
                    pass

    def deregister_device(self, resistance: float):
        pass

    def load_drivers(self):
        """Load necessary drivers"""
        if self.drivers_to_load == []:
            return

    def unload_drivers(self):
        """Remove unnecessary drivers"""
        if self.drivers_to_unload == []:
            return

    def run_drivers(self):
        """Run necessary driver code"""
        pass



def init(config, locks: dict):
    """Initialize and configure SmartBus"""
    if not config.get("main", "SmartBus_enabled"):
        return

    SB = SmartBus(config, locks)
    def scan(config, locks):
        """Scan SmartBus for new devices"""
        SB.scan(locks)

    def load_drivers(config, locks):
        """Load new SmartBus Drivers, as needed"""
        SB.load_drivers()

    def unload_drivers(config, locks):
        """Load new SmartBus Drivers, as needed"""
        SB.unload_drivers()

    def run_drivers(config, locks):
        SB.run_drivers()


    return [scan, load_drivers, unload_drivers, run_drivers]


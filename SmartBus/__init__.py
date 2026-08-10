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
import random
import _thread
import SmartBus.drivers as drivers


class SmartBus:
    """SmartBus Management Class"""
    def __init__(self, config, locks):
        self.INTERNAL_CONFIG = {
            "VERSION": "v1.3",
            "SmartBus_enabled": True,
            "SmartBus_SDA": 20,
            "SmartBus_SCL": 21,
            "SmartBus_ID_Downstream": 26,
            "SmartBus_ID_Upstream": 27,
            "SmartBus_Freq": 100000,
            "SmartBus_Internal_Resistor": 47000,
        }

        self.sb_data_lock = _thread.allocate_lock()
        self.RETURNED_DATA = {}

        self.sb_data_send_lock = _thread.allocate_lock()
        self.SENDING_DATA = {}

        self.MANIFEST = None
        self.drivers = {}
        self.COMMS = None
        self.ID = None
        self.KNOWN_RESISTORS = []
        self.CURRENT_RESISTANCE = 0

        self.sb_device_lock = _thread.allocate_lock()
        self.CONNECTED_DEVICES = {}
        self.known_drivers = drivers.available()
        self.acceptable_tolerance = 0.15

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

    def _check_tolerance(self, reading, reference):
        """Check if a passed reading is within acceptable tolerances of reference"""
        lower = reference * (1 - self.acceptable_tolerance)
        upper = reference * (1 + self.acceptable_tolerance)
        if reading >= lower:
            if reading <= upper:
                return True
        return False


    def _get_current_resistance(self):
        """Get the current resistance on client side of voltage divider"""
        upstream = _get_voltage(self.ID["upstream"].read_u16())
        downstream = _get_voltage(self.ID["downstream"].read_u16())
        # If nothing is hooked up yet, we need to say no resistance
        if (upstream - downstream) == 0:
            return 0
        return (self.INTERNAL_CONFIG["SmartBus_Internal_Resistor"] * downstream) / (upstream - downstream)

    def scan(self, locks):
        """Run a full SmartBus scan"""
        # Need to figure out allowed slop here!
        resistance = [self._get_current_resistance()]
        time.sleep_ms(5)
        resistance.append(self._get_current_resistance())
        time.sleep_ms(5)
        resistance.append(self._get_current_resistance())
        resistance = sum(resistance) / 3

        # NOTHING CONNECTED
        if resistance == 0:
            # No devices connected. Nothing to do.
            if self.KNOWN_RESISTORS != []:
                for each in range(len(self.KNOWN_RESISTORS) - 1, -1, -1):
                    self.deregister_device(self.KNOWN_RESISTORS[each], locks)
            return {}
        # Calculate new resistor
        if self.KNOWN_RESISTORS != []:
            inv = 1 / resistance
            for each in self.KNOWN_RESISTORS:
                inv = inv - (1 / each)
            # resistance should now contain the value of 1 over the new resistor
            if abs(inv) < 1e-3:
                # NO CHANGES, exit
                return
            else:
                resistance = 1 / inv
            if resistance < 0:
                # RESISTOR HAS BEEN REMOVED!
                self.deregister_device(resistance, locks)
            else:
                # RESISTOR ADDED
                self.register_new_device(resistance)
        else:
            # RESISTOR ADDED
            self.register_new_device(resistance)

    def register_new_device(self, resistance: float):
        """Register new device:
        - Add known resistor
        - Add pointer to new driver to load
        - Add to known devices dict with new, unique ID
        """
        # RESISTOR ADDEED
        for each in enumerate(sorted(self.MANIFEST["smartbus"]["devices"].keys())):
            if self._check_tolerance(resistance, int(each[1])):
                # NEED TO FIGURE OUT HOW TO ASSIGN IDS
                self.KNOWN_RESISTORS.append(resistance)
                while True:
                    new_id = _gen_id()
                    if new_id not in self.CONNECTED_DEVICES:
                        break
                with self.sb_device_lock:
                    self.CONNECTED_DEVICES[new_id] = {
                                                    "DEVICE_TYPE": self.MANIFEST["smartbus"]["devices"][each[1]]["role"],
                                                    "DEVICE_DRIVER": None,
                                                    "I2C_ADDR": None,
                                                    "RESISTOR": resistance,
                                                    "KEY": each[1]
                                                }
                with self.sb_data_lock:
                    self.RETURNED_DATA[new_id] = {}

                with self.sb_data_sending_lock:
                    self.SENDING_DATA[new_id] = None
                print(f"FOUND NEW SMARTBUS DEVICE: {self.MANIFEST['smartbus']['devices'][each[1]]['name']}")

                break

    def deregister_device(self, resistance: float, locks):
        """Figure out which resistor was removed and deregister it with the system"""
        if resistance < 0:
            resistance = -1 * resistance
        index = None
        try:
            # Try to find an exact match first as it's faster.
            index = self.KNOWN_RESISTORS.index(resistance)
        except ValueError:
            # If that fails, check for known resistors within the same tolerances
            for each in enumerate(self.KNOWN_RESISTORS):
                if self._check_tolerance(resistance, each[1]):
                    index = each[0]
        if index is not None:
            del self.KNOWN_RESISTORS[index]
        else:
            raise ValueError(f"UNKNOWN RESISTOR VALUE: {resistance} Ohms")
        to_del = []
        with self.sb_device_lock:
            for each in self.CONNECTED_DEVICES:
                if self._check_tolerance(resistance, self.CONNECTED_DEVICES[each]["RESISTOR"]):
                    if self.CONNECTED_DEVICES[each]["I2C_ADDR"] in ([], None):
                        to_del.append(each)
                        break
                    scan = self._scan_i2c(locks)
                    if not isinstance(self.CONNECTED_DEVICES[each]["I2C_ADDR"], (tuple, list)):
                        if self.CONNECTED_DEVICES[each]["I2C_ADDR"] not in scan:
                            to_del.append(each)
                            break
                        continue
                    goal = len(self.CONNECTED_DEVICES[each]["I2C_ADDR"])
                    count = 0
                    for each1 in self.CONNECTED_DEVICES[each]["I2C_ADDR"]:
                        if each1 not in scan:
                            count += 1
                    if count == goal:
                        to_del.append(each)
                        break
            with self.sb_data_lock:
            for each in to_del:
                del self.CONNECTED_DEVICES[each]
                del self.RETURNED_DATA[each]
                del self.SENDING_DATA[each]



    def load_drivers(self, config, locks):
        """Load necessary drivers"""
        with self.sb_device_lock:
            for each in self.CONNECTED_DEVICES:
                if self.CONNECTED_DEVICES[each]["DEVICE_DRIVER"] is None:
                    if self.CONNECTED_DEVICES[each]["DEVICE_TYPE"] in self.known_drivers:
                        self.CONNECTED_DEVICES[each]["DEVICE_DRIVER"] = drivers.load(self.CONNECTED_DEVICES[each]["DEVICE_TYPE"])
                    else:
                        print(f"UNKNOWN DRIVER: {self.CONNECTED_DEVICES[each]['DEVICE_TYPE']}! LOADING DUMMY!")
                        self.CONNECTED_DEVICES[each]["DEVICE_DRIVER"] = drivers.load("dummy")
                    self.CONNECTED_DEVICES[each]["DEVICE_DRIVER"] = self.CONNECTED_DEVICES[each]["DEVICE_DRIVER"].init(self.MANIFEST["smartbus"]["devices"][self.CONNECTED_DEVICES[each]["KEY"]]["i2c_addresses"], config, locks, self.COMMS, self.ID)
                    self.CONNECTED_DEVICES[each]["I2C_ADDR"] = self.CONNECTED_DEVICES[each]["DEVICE_DRIVER"].get_address(locks)
        # There is actually no need to unload drivers, as they get unloaded when we del the entry from self.CONNECTED_DEVICES

    def run_drivers(self, config, locks):
        """Run necessary driver code"""
        with self.sb_device_lock:
            for each in self.CONNECTED_DEVICES:
                if self.CONNECTED_DEVICES[each]["DEVICE_DRIVER"] is not None:
                    with self.sb_data_lock:
                        with self.sb_data_send_lock:
                            self.RETURNED_DATA[each] = self.CONNECTED_DEVICES[each]["DEVICE_DRIVER"].run(config, locks, self.SENDING_DATA[each])

    def get_returned_data(self, name):
        """Get data returned by SmartBus device"""
        with self.sb_data_lock:
            return self.RETURNED_DATA[name]

    def send_data(self, name, data):
        """Get data returned by SmartBus device"""
        with self.sb_data_send_lock:
            return self.SENDING_DATA[name] = data

    def get_devices(self):
        """Get devices"""
        with self.sb_device_lock:
            return self.CONNECTED_DEVICES.keys()



def _gen_id(length=8):
    """Generate a unique ID for each connected device that follows these rules:
    - Arbitrary length
    - The remaining characters should be a randomly generated string of uppercase letters and numbers
    - Avoid Letters:
        - O, I
    - Avoid numnbers:
        - 0, 1
    - Have no special characters"""
    allowed_letters = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    allowed_numbers = [2, 3, 4, 5, 6, 7, 8, 9]
    suffix = []
    while length > 0:
        if (random.randint(0, 10) % 2) == 0:
            # letter
            suffix.append(random.choice(allowed_letters))
        else:
            # number
            suffix.append(str(random.choice(allowed_numbers)))
        length -= 1
    return "".join(suffix)


def _get_voltage(measure: int):
    """Convert u16 to uv"""
    max16 = 65535
    maxv = 3.3
    return maxv * (measure / max16)


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
        SB.load_drivers(config, locks)

    def run_drivers(config, locks):
        SB.run_drivers(config, locks)


    return ([scan, load_drivers, run_drivers], SB)


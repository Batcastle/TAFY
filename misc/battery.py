# -*- coding: utf-8 -*-
#
#  battery.py
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
from machine import Pin, ADC
import time

class Battery():
    def __init__(self, config, disp, batt_in_pin, charge_pin):
        """Set up to monitor battery"""
        # Pin and Resource access variables
        self.disp = disp
        self.batt_in_pin = batt_in_pin
        self.charge_pin = charge_pin

        # Configuration data
        local_config = config.get_section("battery")
        self.battery_type = config.get("main", "batt_chem")
        self.cell_count = config.get("main", "batt_cells")
        self.config = local_config["general"]
        self.battery_settings = local_config["chems"][self.battery_type]

        # Status data
        self.charge = None
        self.previous_charge = None
        self.last_reading = -100000
        self.reading_count = 0

    def is_charging(self):
        """Return if battery is charging"""
        return bool(self.charge_pin.value())

    def get_charge(self):
        """
    Return current state of charge
    If source voltage is calculated to be 0, then return None, indicating no battery connected.
        """
        if (time.ticks_diff(time.ticks_ms(), self.last_reading) / 1000) <= self.config["check_time"]:
            return self.charge
        voltage = self._get_battery_voltage()
        if self.reading_count >= 10:
            if self.charge is None:
                return None
        else:
            if voltage == 0:
                return None
        source_voltage = voltage * (self.config["r1_value"] + self.config["r2_value"])
        source_voltage = source_voltage / self.config["r2_value"]
        cell_voltage = round(source_voltage / self.cell_count, 2)

        self.previous_charge = self.charge
        try:
            self.charge = self.battery_settings["charge_curve"][str(cell_voltage)]
        except KeyError:
            # First, find the points closest to our reading:
            points = {"high": 100, "low": 0}
            for each in self.battery_settings["charge_curve"]:
                if float(each) > cell_voltage:
                    if float(each) < points["high"]:
                        points["high"] = float(each)
                else:
                    # We know we aren't going to find anything equal. That's why we're in this except clause. Everything is > or <
                    if float(each) > points["low"]:
                        points["low"] = float(each)
            # We now have the points closest to our reading. Now, we can interpolate
            ratio = (cell_voltage - points["low"]) / (points["high"] - points["low"])
            result = ratio * (self.battery_settings["charge_curve"][str(points["high"])] - self.battery_settings["charge_curve"][str(points["low"])])
            result = self.battery_settings["charge_curve"][str(points["low"])] + result
            self.charge = round(result, 2)
        return self.charge

    def update(self, locks):
        """Update display with current charge state"""
        if self.previous_charge != self.charge:
            self.disp.STATE.set("CHARGING", self.is_charging())
            self.disp.STATE.set("BATTERY", self.charge)
            self.disp.STATE.set("DIRTY", True)

    def _get_battery_voltage(self):
        """Get the current battery voltage"""
        # ADC reads in microvolts. Divide by 1 million to convert to volts
        # Round to nearest 1/100th of a volt, to help reduce calculations needed
        self.last_reading = time.ticks_ms()
        if self.reading_count < 10:
            self.reading_count += 1
        return round(self.batt_in_pin.read_uv() / 1000000, 2)


def init(config, disp):
    """Intialize battery subsystem"""
    bip = Pin(config.get("pin_out", "Batt_Charge_Pin"), Pin.IN)
    adc = ADC(Pin(config.get("pin_out", "Batt_Status")))
    batt = Battery(config, disp, bip, adc)

    def check_bat(_, lcks):
        """Background process to check battery"""
        batt.get_charge()
        batt.update(lcks)

    return check_bat

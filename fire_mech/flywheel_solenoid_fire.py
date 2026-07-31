# -*- coding: utf-8 -*-
#
#  flywheel_solenoid_fire.py
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
"""
This file provides a basic driver,
designed for blasters with electric flywheels and solenoid pushers

It also serves as a template to start from to write new fire mechanism drivers
"""
import time
from machine import Pin, PWM
import fire_mech.flywheel_mechanical_fire as fmf


class FireMechanism(fmf.FireMechanism):
    """Extend Mechanical Fire Flywheel blasters to support solenoid pushers instead."""
    def __init__(self, config: dict):
        super().__init__(config, silent=True)
        self.INTERNAL_CONFIG["TRIG_PIN"] = [11, None]
        self.INTERNAL_CONFIG["TRIG_PIN_NORMAL"] = 0
        self.INTERNAL_CONFIG["SOL_PIN"] = [10, None]
        self.FIRE_TYPE = "flywheel_solenoid"
        self.HARDWARE_CONFIG = {
            "rev_switch": True,
            "motor": True,
            "solenoid": True,
            "fire_switch": True
        }
        if self.config.get("main", "mode").lower() == "debug":
            print("initalizing flywheel/solenoid fire mechanism!")

        if "trigger_pin" in self.config.get_section("pin_out"):
            self.INTERNAL_CONFIG["TRIG_PIN"][0] = self.config.get("pin_out", "trigger_pin")
        else:
            raise KeyError("Setting `trigger_pin' not found in pin_out.json")

        if "trigger_pin_normal" in self.config.get_section("main"):
            self.INTERNAL_CONFIG["TRIG_PIN_NORMAL"] = self.config.get("main", "trigger_pin_normal")
        else:
            raise KeyError("Setting `trigger_pin_normal' not found in main.json")


        if "solenoid_pin" in self.config.get_section("pin_out"):
            self.INTERNAL_CONFIG["SOL_PIN"][0] = self.config.get("pin_out", "solenoid_pin")
        else:
            raise KeyError("Setting `solenoid_pin' not found in pin_out.json")

        if "solenoid_pwm_duty" in self.config.get_section("main"):
            duty = self.config.get("main", "solenoid_pwm_duty")
            if duty > 1:
                duty = 1
            elif duty < 0:
                duty = 0
            self.INTERNAL_CONFIG["SOL_PWM_DUTY"] = duty

        if "solenoid_pwm_freq" in self.config.get_section("main"):
            self.SOL_PWM_FREQ = self.config.get("main", "solenoid_pwm_freq")


        # Setup all new pins
        if self.INTERNAL_CONFIG["TRIG_PIN_NORMAL"]:
            self.INTERNAL_CONFIG["TRIG_PIN"][1] = Pin(self.INTERNAL_CONFIG["TRIG_PIN"][0], Pin.IN,
                                                      Pin.PULL_UP)
        else:
            self.INTERNAL_CONFIG["TRIG_PIN"][1] = Pin(self.INTERNAL_CONFIG["TRIG_PIN"][0], Pin.IN,
                                                      Pin.PULL_DOWN)
        self.INTERNAL_CONFIG["SOL_PIN"][1] = PWM(Pin(self.INTERNAL_CONFIG["SOL_PIN"][0], Pin.OUT))
        self.INTERNAL_CONFIG["SOL_PIN"][1].freq(self.SOL_PWM_FREQ)


    def fire_trigger_pulled(self) -> bool:
        """
        Simple function to check if the firing trigger has been pulled.
        Config will determine if it will pull a pin down or up.

        This function is for the firing trigger.
        """
        result1 = self.INTERNAL_CONFIG["TRIG_PIN"][1].value() != self.INTERNAL_CONFIG["TRIG_PIN_NORMAL"]
        time.sleep(0.025)
        result2 = self.INTERNAL_CONFIG["TRIG_PIN"][1].value() != self.INTERNAL_CONFIG["TRIG_PIN_NORMAL"]
        time.sleep(0.025)
        return result1 and result2 and self.INTERNAL_CONFIG["TRIG_PIN"][1].value() != self.INTERNAL_CONFIG["TRIG_PIN_NORMAL"]

    def fire(self):
        """
        Fire a dart

        This blaster uses a solenoid, so we just trigger that.
        """
        self.trigger_solenoid()


    def trigger_solenoid(self):
        """This function sends a pulse to fire a solenoid"""
        max_duty = 65535.0
        duty = max_duty * self.INTERNAL_CONFIG["SOL_PWM_DUTY"]
        if duty > max_duty:
            duty = int(max_duty)
        elif duty < 0:
            duty = 0
        else:
            duty = round(duty)
        self.INTERNAL_CONFIG["SOL_PIN"][1].duty_u16(duty)
        time.sleep(0.05)
        self.INTERNAL_CONFIG["SOL_PIN"][1].duty_u16(0)

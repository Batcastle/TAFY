# -*- coding: utf-8 -*-
#
#  flywheel_mechanical_fire.py
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
This file provides a basic driver, designed for blasters with
electric flywheels but mechanical pushers

It also serves as a template to start from to write new fire mechanism drivers
"""
import time
from machine import Pin, PWM
import fire_mech.base


class FireMechanism(fire_mech.base.FireMechanism):
    """Fire Mechanism object for flywheel blasters with mechanical pushers"""
    def __init__(self, config: dict, silent=False):
        super().__init__(config)
        if not silent:
            if self.config.get("main", "mode").lower() == "debug":
                print("initalizing flywheel/mechanical fire mechanism!")
        if "flywheel_pwm_pin" in self.config.get_section("pin_out"):
            self.INTERNAL_CONFIG["PWM_PIN"][0] = self.config.get("pin_out", "flywheel_pwm_pin")
        if "flywheel_pwm_freq" in self.config.get_section("main"):
            self.PWM_FREQ = self.config.get("main", "flywheel_pwm_freq")
        if "flywheel_pwm_duty" in self.config.get_section("main"):
            duty = self.config.get("main", "flywheel_pwm_duty")
            if duty > 1:
                duty = 1
            elif duty < 0:
                duty = 0
            self.INTERNAL_CONFIG["PWM_DUTY"] = duty



        if "flywheel_rev_pin" in self.config.get_section("pin_out"):
            self.INTERNAL_CONFIG["REV_PIN"][0] = self.config.get("pin_out", "flywheel_rev_pin")

        if "flywheel_rev_pin_normal" in self.config.get_section("main"):
            self.INTERNAL_CONFIG["REV_PIN_NORMAL"] = self.config.get("main",
                                                                     "flywheel_rev_pin_normal")
        if self.INTERNAL_CONFIG["REV_PIN_NORMAL"] == 0:
            normal = Pin.PULL_DOWN
        elif self.INTERNAL_CONFIG["REV_PIN_NORMAL"] == 1:
            normal = Pin.PULL_UP
        else:
            normal = Pin.PULL_DOWN

        self.INTERNAL_CONFIG["REV_PIN"][1] = Pin(self.INTERNAL_CONFIG["REV_PIN"][0], Pin.IN, normal)
        self.INTERNAL_CONFIG["PWM_PIN"][1] = PWM(Pin(self.INTERNAL_CONFIG["PWM_PIN"][0]))
        self.INTERNAL_CONFIG["PWM_PIN"][1].freq(self.PWM_FREQ)

        self.FIRE_TYPE = "flywheel_mechanical"
        self.HARDWARE_CONFIG = {
            "rev_switch": True,
            "motor": True,
            "solenoid": False,
            "fire_switch": False
            }

    def rev_trigger_pulled(self) -> bool:
        """
        Simple function to check if the flywheel spin up trigger has been pulled.
        Config will determine if it will pull a pin down or up.

        On AEBs, this should call fire_trigger_pulled(),
        as they do the same thing on those blasters.
        This function also includes a small bit of debounce handling,
        so it does pause execution for 1/10th of a second.
        """
        result1 = self.INTERNAL_CONFIG["REV_PIN_NORMAL"] != self.INTERNAL_CONFIG["REV_PIN"][1].value()
        time.sleep(0.05)
        result2 = self.INTERNAL_CONFIG["REV_PIN_NORMAL"] != self.INTERNAL_CONFIG["REV_PIN"][1].value()
        time.sleep(0.05)
        return result1 and result2 and self.INTERNAL_CONFIG["REV_PIN_NORMAL"] != self.INTERNAL_CONFIG["REV_PIN"][1].value()

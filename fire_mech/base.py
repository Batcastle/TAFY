# -*- coding: utf-8 -*-
#
#  base.py
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
This file provides the base ABI for fire mechanisms.
It is not a dummy driver. These functions must be defined.
"""
import time


class FireMechanism():
    """FireMechanism class

       Provides an object through with TAFY can control the fire mechanism,
       in any of it's varied forms
    """
    def __init__(self, config):
        """Initalize your fire mechanism"""
        # This is, in part a documentation field.
        self.FIRE_TYPE = "BASE"

        # This defines the pin out to control the fire mechanism, and other necessary variables
        self.INTERNAL_CONFIG = {
                "MOTOR1_PWM_PIN": [4, None],
                "MOTOR1_FWD_PIN": [2, None],
                "MOTOR1_REV_PIN": [3, None],
                "MOTOR2_PWM_PIN": [7, None],
                "MOTOR2_FWD_PIN": [5, None],
                "MOTOR2_REV_PIN": [6, None],
                "REV_PIN": [13, None],
                "TRIG_PIN": [11, None],
                "SOL_PIN": [20, None],
                "REV_PIN_NORMAL": 0,
                "PWM_DUTY": 1.0,
                "SOL_PWM_DUTY": 1.0,
                "MOTOR_CHANNELS": 2
            }

        # Higher PWM frequencies allow more control,
        # but also increase the chance of something going wrong.
        self.PWM_FREQ = 1000
        self.SOL_PWM_FREQ = 1000

        """This configuration will be READ by main, but not changed.
They tell main what motors we have and what triggers we have, so it knows what to check and move.
if:
    {
        "rev_switch": True,
        "motor": True,
        "solenoid": False,
        "fire_switch": False
    }
Rev switch controls motor. This is a flywheel blaster with mechanical pusher

if:
    {
        "rev_switch": True,
        "motor": True,
        "solenoid": True,
        "fire_switch": True
    }
rev switch controls motor, fire switch controls solenoid. This is a fully electric flywheel blaster

if:
    {
        "rev_switch": False,
        "motor": True,
        "solenoid": True,
        "fire_switch": True
    }
The fire switch controls both. Expect a short delay before firing begins,
and a short delay before the flywheel spins down.
This is fully electric flywheel blaster, with a simpler, cheaper design.

if:
    {
        "rev_switch": False,
        "motor": True,
        "solenoid": False,
        "fire_switch": True
    }
The fire switch controls the motor, this is an AEB.

if:
    {
        "rev_switch": False,
        "motor": False,
        "solenoid": True,
        "fire_switch": True
    }
The fire switch controls the solenoid. This is essentially either a solenoid-backed AEB,
or a solenoid blaster.

**The user must have at least *ONE* switch and *ONE* of either a motor or solenoid.
"""
        self.HARDWARE_CONFIG = {
            "rev_switch": False,
            "motor": False,
            "solenoid": False,
            "fire_switch": False
            }

        # This is just to ensure that the config object is available later
        self.config = config

    def fire_trigger_pulled(self) -> bool:
        """
        Simple function to check if the firing trigger has been pulled.
        Config will determine if it will pull a pin down or up.

        This function is for the firing trigger. As this form of flywheel has a mechanically
        operated pusher instead of a solenoid, we leave this essentially empty.
        """
        return False

    def rev_trigger_pulled(self):
        """
        Simple function to check if the flywheel spin up trigger has been pulled.
        Config will determine if it will pull a pin down or up.

        On AEBs, this should call fire_trigger_pulled(), as they do the same thing
        on those blasters. This function also includes a small bit of debounce handling,
        so it does pause execution for 1/10th of a second.
        """

    def spin_up(self):
        """Spin up a motor"""
        self.INTERNAL_CONFIG["MOTOR1_REV_PIN"][1].value(0)
        self.INTERNAL_CONFIG["MOTOR1_FWD_PIN"][1].value(0)
        if self.INTERNAL_CONFIG["MOTOR_CHANNELS"] == 2:
            self.INTERNAL_CONFIG["MOTOR2_FWD_PIN"][1].value(0)
            self.INTERNAL_CONFIG["MOTOR2_REV_PIN"][1].value(0)
        max_duty = 65535.0
        duty = max_duty * self.INTERNAL_CONFIG["PWM_DUTY"]
        if duty > max_duty:
            duty = int(max_duty)
        elif duty < 0:
            duty = 0
        else:
            duty = round(duty)
        time.sleep_ms(20)
        self.INTERNAL_CONFIG["MOTOR1_REV_PIN"][1].value(0)
        self.INTERNAL_CONFIG["MOTOR1_FWD_PIN"][1].value(1)
        self.INTERNAL_CONFIG["MOTOR1_PWM_PIN"][1].duty_u16(duty)
        if self.INTERNAL_CONFIG["MOTOR_CHANNELS"] == 2:
            self.INTERNAL_CONFIG["MOTOR2_REV_PIN"][1].value(0)
            self.INTERNAL_CONFIG["MOTOR2_FWD_PIN"][1].value(1)
            self.INTERNAL_CONFIG["MOTOR2_PWM_PIN"][1].duty_u16(duty)

    def spin_down(self):
        """Spin down a motor"""
        self.INTERNAL_CONFIG["MOTOR1_REV_PIN"][1].value(0)
        self.INTERNAL_CONFIG["MOTOR1_FWD_PIN"][1].value(0)
        self.INTERNAL_CONFIG["MOTOR1_PWM_PIN"][1].duty_u16(0)
        if self.INTERNAL_CONFIG["MOTOR_CHANNELS"] == 2:
            self.INTERNAL_CONFIG["MOTOR2_FWD_PIN"][1].value(0)
            self.INTERNAL_CONFIG["MOTOR2_REV_PIN"][1].value(0)
            self.INTERNAL_CONFIG["MOTOR2_PWM_PIN"][1].duty_u16(0)


    def trigger_solenoid(self):
        """This function sends a pulse to fire a solenoid"""

    def fire(self):
        """
        Fire a dart

        On this on this fire mechanism, firing is done mechanically. So, this should be empty.
        """
        # This function is likely to vary wildly, from blaster to blaster.
        # On a flywheel blaster with mechanical pusher, it can be empty
        # On a solenoid-backed blaster, this can just call self.trigger_solenoid()
        # On a AEB though? This may need to be calibrated some.

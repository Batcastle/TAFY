# -*- coding: utf-8 -*-
#
#  flywheel_mechanical_fire.py
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
"""
This file provides a basic driver, designed for blasters with electric flywheels but mechanical pushers

It also serves as a template to start from to write new fire mechanism drivers
"""
from machine import Pin, PWM
import time


# Always make sure to set a fire mechanism type string. This is useful for debugging.
FIRE_TYPE = "flywheel_mechanical"


# This is the internal config. It will not be interacted with by the main function
# The first entry in each list is the pin number for each needed pin, the second pin
# is the object needed to interact with that pin
# The pin numbers provided here are intended to be the defaults. If the setting in the provided config
# does not work, makes no sense, or the settings does not exist, these are your fall backs.
INTERNAL_CONFIG = {
        "PWM_PIN": [0, None],
        "REV_PIN": [2, None],
        "REV_PIN_NORMAL": 0,
        "PWM_DUTY": 1.0
    }

# Default PWM frequency
PWM_FREQ = 1000

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
The fire switch controls both. Expect a short delay before firing begins, and a short delay before the flywheel spins down.
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
The fire switch controls the solenoid. This is essentially either a solenoid-backed AEB, or a solenoid blaster.

**The user must have at least *ONE* switch and *ONE* of either a motor or solenoid.
"""
HARDWARE_CONFIG = {
        "rev_switch": True,
        "motor": True,
        "solenoid": False,
        "fire_switch": False
    }


def init(config):
    """
    This function would serves to initalize any necessary hardware. In this case, we are setting up a pin for PWM

    Here, since we need to simply set up 2 pins: one for a simple switch, and the other for PWM control of the flywheels

    Fire control is handled in the main thread. Any function should be quick to run in order to return control to the
    main function.

    This function should also avoid actually returning anything, and instead keep it's work internal.
    """
    print("initalizing flywheel/mechanical fire mechanism!")
    if "flywheel_pwm_pin" in config:
        INTERNAL_CONFIG["PWM_PIN"][0] = config["flywheel_pwm_pin"]
    if "flywheel_pwm_freq" in config:
        PWM_FREQ = config["flywheel_pwm_freq"]
    if "flywheel_pwm_duty" in config:
        if config["flywheel_pwm_duty"] > 1:
            config["flywheel_pwm_duty"] = 1
        elif config["flywheel_pwm_duty"] < 0:
            config["flywheel_pwm_duty"] = 0
        INTERNAL_CONFIG["PWM_DUTY"] = config["flywheel_pwm_duty"]

    INTERNAL_CONFIG["PWM_PIN"][1] = PWM(Pin(INTERNAL_CONFIG["PWM_PIN"][0]))
    INTERNAL_CONFIG["PWM_PIN"][1].freq(PWM_FREQ)

    if "flywheel_rev_pin" in config:
        INTERNAL_CONFIG["REV_PIN"][0] = config["flywheel_rev_pin"]

    if "flywheel_rev_pin_normal" in config:
        INTERNAL_CONFIG["REV_PIN_NORMAL"] = config["flywheel_rev_pin_normal"]

    INTERNAL_CONFIG["REV_PIN"][1] = Pin(INTERNAL_CONFIG["REV_PIN"][0], Pin.IN)




def fire_trigger_pulled():
    """
    Simple function to check if the firing trigger has been pulled. Config will determine if it will pull a pin down or up.

    This function is for the firing trigger. As this form of flywheel has a mechanically operated pusher instead of a solenoid, we leave this empty.
    """
    pass


def spin_up_trigger_pulled():
    """
    Simple function to check if the flywheel spin up trigger has been pulled. Config will determine if it will pull a pin down or up.

    On AEBs, this should call fire_trigger_pulled(), as they do the same thing on those blasters.
    """
    return INTERNAL_CONFIG["REV_PIN_NORMAL"] != INTERNAL_CONFIG["REV_PIN"][1].value()


def fire():
    """
    Fire a dart

    On this on this fire mechanism, firing is done mechanically. So, this should be empty.
    """
    pass


def spin_up():
    """Spin up a motor"""
    max_duty = 65535.0
    duty = max_duty * INTERNAL_CONFIG["PWM_DUTY"]
    if duty > max_duty:
        duty = int(max_duty)
    elif duty < 0:
        duty = 0
    else:
        duty = round(duty)
    INTERNAL_CONFIG["PWM_PIN"][1].duty_u16(duty)


def spin_down():
    """Spin down a motor"""
    INTERNAL_CONFIG["PWM_PIN"][1].duty_u16(0)


def trigger_solenoid():
    """This function sends a pulse to fire a solenoid"""
    pass

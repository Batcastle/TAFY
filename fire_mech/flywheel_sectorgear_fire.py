# -*- coding: utf-8 -*-
#
#  flywheel_sectorgear_fire.py
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
electric flywheels and pushers controlled by a sector gear driven by a motor
"""
from fire_mech import flywheel_mechanical_fire as fmf

class FireMechanism(fmf.FireMechanism):
    """Control class for our fire mechanism"""
    def __init__(self, config: dict, silent=False):
        """Intialize our code"""
        super().__init__(config, silent=True)

        # Reset some things to accomidate our new electric pusher
        self.FIRE_TYPE = "flywheel_sectorgear"
        self.HARDWARE_CONFIG = {
            "rev_switch": True,
            "motor": True,
            "solenoid": False,
            "fire_switch": True
            }

        """
        TAFY currently supports 2 motor channels and 1 solenoid. This can be useful for tuning flywheels to have close to the same speed
        or having a dual-stage flywheel system. However, here, we are limited.

        The flywheels MUST be driven in parallel, from Channel One, while Channel Two controls the pusher.
        """

        self.INTERNAL_CONFIG["MOTOR_CHANNELS"] = 1

    def fire(self):
        """
        Fire a dart
        This blaster uses a motorized pusher, so we control that
        """

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
"""fire mechanism driver loader for TAFY"""
import os
# import importlib


def load(fire: str):
    """Load the specified UI type"""
    if f"{fire}_fire.py" in os.listdir("fire_mech"):
        print(f"Loading Module: {fire}")
        return __import__(f"fire_mech/{fire}_fire")
    raise ImportError(f"Module {fire}_fire is not present!")


def available() -> list:
    """List available GUIs/toolkits"""
    options = os.listdir("fire_mech")
    output = [each.split("_")[0] for each in options if "_fire" == each[-8:-3]]
    return output

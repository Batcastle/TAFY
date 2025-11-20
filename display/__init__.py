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
"""UI for Edamame"""
import os
import importlib


def load(display_type: str):
    """Load the specified UI type"""
    display = display_type.upper()
    if os.path.exists(f"display/{display}_display"):
        return importlib.import_module(f"display.{display}_display")
    raise ImportError(f"Module {display}_display is not present!")


def available() -> list:
    """List available GUIs/toolkits"""
    options = os.listdir("display")
    output = [each.split("_")[0] for each in uis if "_display" == each[-3:]]
    return output

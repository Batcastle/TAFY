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
This file defines the base that all display drivers need, at minimum
"""

# Shared state — imported by name into each driver module so main.py can
# reach it as disp.STATE. Only ever mutated (never reassigned), so all
# drivers that import it share the same live dict correctly.
STATE = {"CAPACITY": 0,
         "MODE":     "SAFE",
         "BATTERY":  None,
         "CHARGING": False,
         "UPDATING": False,
         "DIRTY":    True}

# This will likely be converted into a data class in the future.
DISPLAY_TYPE = None

DISPLAY_MODE = 0

# -*- coding: utf-8 -*-
#
#  lcd1602_i2c_display.py
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
This file provides a display driver for blasters with 4 digit 7 segment display arrays over I2C
"""
DRIVER = None

DISPLAY_TYPE = "7 SEGMENT"

THREAD_OBJ = None

I2C_OBJ = None

INTERNAL_SETTINGS = {}


def init(config, i2c_obj, locks, silent=False, split_thread=True) -> None:
    """Initalize 7 segment display, determine type and load necessary driver"""
    I2C_OBJ = i2c_obj
    results = I2C_OBJ.scan()
    INTERNAL_SETTINGS = config.get_section("7_seg")

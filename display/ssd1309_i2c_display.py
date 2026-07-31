# -*- coding: utf-8 -*-
#
#  ssd1309_i2c_display.py
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
"""SSD1309 128x64 OLED over I2C — TAFY display driver."""
import display.oled_i2c_base as _base

STATE        = _base.STATE
STATE.DISPLAY_TYPE = "SSD1309 OLED - I2C"

# SSD1309 requires external VCC — no charge pump command.
_INIT_SEQ = bytes([
    0xAE,        # display off
    0xD5, 0x80,  # clock divider / oscillator frequency
    0xA8, 0x3F,  # multiplex ratio (64 rows - 1)
    0xD3, 0x00,  # display offset: 0
    0x40,        # display start line: 0
    0xA1,        # segment remap (col 127 -> SEG0)
    0xC8,        # COM scan direction remapped
    0xDA, 0x12,  # COM pins hardware config
    0x81, 0x7F,  # contrast
    0xD9, 0x22,  # pre-charge period (external VCC)
    0xDB, 0x30,  # VCOMH deselect level
    0xA4,        # output follows RAM
    0xA6,        # normal (non-inverted)
    0x20, 0x00,  # horizontal addressing mode
    0xAF,        # display on
])

_OLED = None


class _SSD1309(_base._OLEDBase):
    def __init__(self, i2c, addr):
        super().__init__(i2c, addr)
        self._send_init(_INIT_SEQ)


def init(config, i2c_obj, locks, silent=False, split_thread=True):
    global _OLED
    _OLED = _base.init_oled(config, i2c_obj, locks,
                             "ssd130x_i2c", _SSD1309, silent)
    return display_main if split_thread else _OLED


def display_main(_, locks):
    _base.run_display(locks, _OLED)

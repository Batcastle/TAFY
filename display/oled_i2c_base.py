# -*- coding: utf-8 -*-
#
#  oled_i2c_base.py
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
Shared base for 128x64 monochrome OLED drivers over I2C.

Concrete drivers (ssd1306, ssd1309, etc.) subclass _OLEDBase and supply
their own _INIT_SEQ. Everything else — buffers, framebuf, ABI wiring —
lives here so it is not duplicated.
"""
import time
import framebuf
from display.global_base import *


class _OLEDBase:
    """Hardware abstraction for a 128x64 OLED over I2C."""

    def __init__(self, i2c, addr):
        self._i2c   = i2c
        self._addr  = addr
        # Pixel buffer — 128 * 64 / 8 = 1024 bytes, MONO_VLSB matches
        # the SSD130x page layout in horizontal addressing mode.
        self._buf   = bytearray(1024)
        self._fb    = framebuf.FrameBuffer(
                          self._buf, 128, 64, framebuf.MONO_VLSB)
        # Pre-allocated transmit buffer reused every frame: [0x40] + pixels.
        self._tx    = bytearray(1025)
        self._tx[0] = 0x40
        # Pre-allocated column + page range command sent before each frame.
        # 0x00 = command stream; 0x21/0x22 set col/page address in one write.
        self._range = bytearray(b'\x00\x21\x00\x7f\x22\x00\x07')

    def _send_init(self, seq):
        """Send an init byte sequence as a single I2C command stream."""
        buf = bytearray(len(seq) + 1)
        buf[0] = 0x00
        buf[1:] = seq
        self._i2c.writeto(self._addr, buf)
        # Force clear display VRAM immediately after init
        self.clear()
        self.show()

    def show(self):
        """Push the framebuffer to the display."""
        for page in range(8):
            self._i2c.writeto(self._addr,
                bytes([0x00, 0x21, 0x00, 0x7F, 0x22, page, page]))
            start = page * 128
            tx = bytearray(129)
            tx[0] = 0x40
            tx[1:] = self._buf[start:start + 128]
            self._i2c.writeto(self._addr, tx)

    def clear(self):
        self._fb.fill(0)

    def text(self, s, x, y):
        self._fb.text(s, x, y, 1)

    def hline(self, x, y, w):
        self._fb.hline(x, y, w, 1)

    def display_string(self, s):
        """Show a single string centered on screen (used by update())."""
        s = s[:16]
        self.clear()
        self.text(s, max(0, (128 - len(s) * 8) // 2), 28)
        self.show()


def run_display(locks, oled):
    """
    Shared display refresh logic called by each driver's display_main().

    Reads STATE under the state lock, clears DIRTY while still holding it
    (preventing missed updates), then renders outside the lock.
    """
    flag = False

    if STATE.get("DIRTY"):
        mode = f"MODE:  {STATE.get('MODE'):<8}"
        ammo = f"AMMO:  {STATE.get('CAPACITY'):<8}"
        bat  = STATE.get("BATTERY")
        batt = f"BAT:   {str(bat) + '%' if bat is not None else '---':<8}"
        STATE.set("DIRTY", False)
        flag = True

    if flag:
        with locks["i2c_int"]:
            oled.clear()
            oled.text(mode, 0, 0)
            oled.hline(0, 10, 128)
            oled.text(ammo, 0, 16)
            oled.text(batt, 0, 32)
            oled.show()


def init_oled(config, i2c_obj, locks, cfg_section, display_class, silent):
    """
    Shared init logic for all OLED I2C drivers.

    Scans the bus, matches against cfg['supported'], constructs the display
    object, and shows the welcome screen unless silent=True.

    Returns the constructed display object.
    """
    cfg     = config.get_section(cfg_section)
    results = i2c_obj.scan()
    addr    = None

    for each in results:
        if str(each) in cfg["supported"]:
            addr = each
            break

    if addr is None:
        raise Exception(f"OLED ({cfg_section}) not found at any supported I2C address.")

    with locks["i2c_int"]:
        oled = display_class(i2c_obj, addr)
        time.sleep_ms(100)  # Give display time to stabilize
        if not silent:
            oled.clear()
            time.sleep_ms(50)
            oled.text("Welcome to TAFY!", 0, 0)
            oled.text(config.VERSION,    0, 16)
            oled.show()

    return oled

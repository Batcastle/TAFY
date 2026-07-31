# -*- coding: utf-8 -*-
#
#  led_array_i2c_display.py
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
LED Array display driver for TAFY — MCP23017 + PCA9685 over I2C.

Follows the TAFY display driver ABI. STATE fields map to hardware as follows:
    STATE.get("MODE")     → mode LEDs     (MCP23017 Port B, pins 0-3)
    STATE.get("CAPACITY") → ammo bar LEDs (MCP23017 Port A, pins 0-7, up to 8)
    STATE.get("BATTERY")  → RGB indicator (PCA9685 PWM channels, smooth color shift)

Hardware layout:
    MCP23017 Port A (PA0-PA7): ammo LEDs, max 8, configurable count
    MCP23017 Port B (PB0-PB3): mode LEDs (SAFE / SINGLE / BURST / AUTO)
    PCA9685  channels 0, 1, 2: RGB LED red, green, blue (configurable)

Battery color transitions:
    100% → 50%  green → yellow
     50% → 20%  yellow → red
      < 20%     solid red
      < thresh  flashing red (threshold configurable, default 10%)
    None        blue (no battery data available)
"""
import time
from display.global_base import *

STATE.DISPLAY_TYPE = "LED Array - I2C"

_ARRAY      = None
_flash_tick = 0
_flash_on   = False

# Last rendered values — used to skip redundant I2C writes.
_last_mode  = None
_last_cap   = -1
_last_bat   = -1
_last_flash = None

# MCP23017 register addresses
_MCP_IODIR = 0x00   # Direction: IODIRA at 0x00, IODIRB at 0x01 (sequential)
_MCP_GPIO  = 0x12   # Output:    GPIOA  at 0x12, GPIOB  at 0x13 (sequential)

# MODE → Port B bitmask. One bit per LED; only one is ever high.
_MODE_BITS = {"SAFE": 0x01, "SINGLE": 0x02, "BURST": 0x04, "AUTO": 0x08}


class _LEDArray:
    """
    Hardware abstraction over MCP23017 (GPIO) and PCA9685 (PWM).

    All I2C writes use pre-allocated bytearrays in the hot path
    to avoid heap allocation during display_main.
    """

    def __init__(self, i2c, mcp_addr, pca_addr, ammo_count,
                 max_cap, pwm_freq, r_ch, g_ch, b_ch, flash_thresh):
        self._i2c    = i2c
        self._mcp    = mcp_addr
        self._pca    = pca_addr
        # Port A is 8 bits wide; clamp ammo count accordingly.
        self._ammo   = min(ammo_count, 8)
        # Guard against division by zero on an unconfigured blaster.
        self._maxcap = max(max_cap, 1)
        self._r_ch   = r_ch
        self._g_ch   = g_ch
        self._b_ch   = b_ch
        self.thresh  = flash_thresh

        # Pre-allocate write buffers to keep display_main allocation-free.
        self._mcp_buf = bytearray(3)   # [register, port_A_byte, port_B_byte]
        self._pca_buf = bytearray(5)   # [register, ON_L, ON_H, OFF_L, OFF_H]

        self._init_mcp()
        self._init_pca(pwm_freq)

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_mcp(self):
        """Set all MCP23017 pins to output, all off."""
        self._i2c.writeto(self._mcp, bytes([_MCP_IODIR, 0x00, 0x00]))
        self._i2c.writeto(self._mcp, bytes([_MCP_GPIO,  0x00, 0x00]))

    def _init_pca(self, freq):
        """Set PCA9685 PWM frequency and wake from sleep."""
        # Clamp prescale to valid range (3-255).
        prescale = max(3, min(255, round(25_000_000 / (4096 * freq)) - 1))
        self._i2c.writeto(self._pca, bytes([0x00, 0x10]))       # sleep
        self._i2c.writeto(self._pca, bytes([0xFE, prescale]))   # prescaler
        self._i2c.writeto(self._pca, bytes([0x00, 0x00]))       # wake
        time.sleep_ms(5)                                         # stabilise
        self._i2c.writeto(self._pca, bytes([0x00, 0xA0]))       # auto-increment on

    # ------------------------------------------------------------------
    # Hardware writes
    # ------------------------------------------------------------------

    def _set_rgb(self, r, g, b):
        """Write r, g, b (0-4095 each) to their PCA9685 channels."""
        buf = self._pca_buf
        buf[1] = 0x00
        buf[2] = 0x00
        for ch, val in ((self._r_ch, r), (self._g_ch, g), (self._b_ch, b)):
            buf[0] = 0x06 + 4 * ch
            buf[3] = val & 0xFF
            buf[4] = (val >> 8) & 0x0F
            self._i2c.writeto(self._pca, buf)

    def _write_mcp(self, ammo_byte, mode_byte):
        """Write both MCP23017 ports in one I2C transaction."""
        buf    = self._mcp_buf
        buf[0] = _MCP_GPIO
        buf[1] = ammo_byte
        buf[2] = mode_byte
        self._i2c.writeto(self._mcp, buf)

    # ------------------------------------------------------------------
    # State → hardware mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _battery_color(pct):
        """
        Map battery percentage (0-100) to an (r, g, b) tuple (0-4095 each).

        100% → green, 50% → yellow, 20% → red.
        Linear interpolation between each pair of waypoints.
        """
        if pct >= 50:
            t = (100 - pct) / 50      # 0.0 at 100%, 1.0 at 50%
            return (int(4095 * t), 4095, 0)
        if pct >= 20:
            t = (pct - 20) / 30       # 1.0 at 50%, 0.0 at 20%
            return (4095, int(4095 * t), 0)
        return (4095, 0, 0)

    def update(self, mode, cap, bat, flash_on):
        """Push current blaster state to all LEDs."""
        # Ammo bar: light LEDs proportional to remaining capacity.
        lit       = round(cap / self._maxcap * self._ammo)
        lit       = max(0, min(self._ammo, lit))
        ammo_byte = (1 << lit) - 1 if lit else 0

        # Mode LED: one pin high on Port B.
        mode_byte = _MODE_BITS.get(mode, _MODE_BITS["SAFE"])

        self._write_mcp(ammo_byte, mode_byte)

        # Battery RGB indicator.
        if bat is None:
            self._set_rgb(0, 0, 4095)           # blue  — no data
        elif bat < self.thresh:
            if flash_on:
                self._set_rgb(4095, 0, 0)        # red on
            else:
                self._set_rgb(0, 0, 0)           # red off
        else:
            self._set_rgb(*self._battery_color(bat))

    def all_off(self):
        """Turn all LEDs off (used at startup and on error)."""
        self._write_mcp(0x00, 0x00)
        self._set_rgb(0, 0, 0)

    def display_string(self, _):
        """
        No-op. Satisfies the display ABI check in update() which looks for
        this method before trying to display text on the active display.
        An LED array has no way to show arbitrary text, so we silently ignore it.
        """


# ------------------------------------------------------------------
# TAFY display ABI
# ------------------------------------------------------------------

def init(config, i2c_obj, locks, silent=False, split_thread=True):
    """Initialise the LED array and return the background display function."""
    global _ARRAY
    cfg      = config.get_section("led_array_i2c")
    results  = i2c_obj.scan()
    mcp_addr = cfg["mcp23017_address"]
    pca_addr = cfg["pca9685_address"]

    if mcp_addr not in results:
        raise Exception(f"MCP23017 not found at I2C address {mcp_addr}")
    if pca_addr not in results:
        raise Exception(f"PCA9685 not found at I2C address {pca_addr}")

    with locks["i2c_int"]:
        _ARRAY = _LEDArray(
            i2c_obj,
            mcp_addr,
            pca_addr,
            ammo_count   = cfg.get("ammo_led_count",    8),
            max_cap      = config.get("main", "dart_capacity"),
            pwm_freq     = cfg.get("pwm_freq",           1000),
            r_ch         = cfg.get("rgb_red_channel",    0),
            g_ch         = cfg.get("rgb_green_channel",  1),
            b_ch         = cfg.get("rgb_blue_channel",   2),
            flash_thresh = cfg.get("flash_threshold",    10),
        )
        if not silent:
            # Startup flash: all LEDs on briefly, then off.
            _ARRAY._write_mcp(0xFF, 0x0F)
            _ARRAY._set_rgb(0, 4095, 0)
            time.sleep_ms(500)
            _ARRAY.all_off()

    if split_thread:
        return display_main
    return _ARRAY


def display_main(_, locks):
    """Background display refresh — called repeatedly by the background thread."""
    global _ARRAY, _flash_tick, _flash_on
    global _last_mode, _last_cap, _last_bat, _last_flash

    if _ARRAY is None:
        return

    mode = STATE.get("MODE")
    cap  = STATE.get("CAPACITY")
    bat  = STATE.get("BATTERY")

    # Advance flash counter on every call.
    # ~50 calls at 10ms/call ≈ 500ms per flash half-period.
    _flash_tick += 1
    if _flash_tick >= 50:
        _flash_tick = 0
        _flash_on   = not _flash_on

    # Flash state is only meaningful when battery is below threshold.
    # Tracking it separately means a flash toggle always triggers an I2C
    # write when active, but never does so when the battery is fine.
    flashing    = bat is not None and bat < _ARRAY.thresh
    flash_state = _flash_on if flashing else None

    if (mode != _last_mode or cap  != _last_cap  or
        bat  != _last_bat  or flash_state != _last_flash):
        _last_mode  = mode
        _last_cap   = cap
        _last_bat   = bat
        _last_flash = flash_state
        with locks["i2c_int"]:
            _ARRAY.update(mode, cap, bat, _flash_on)

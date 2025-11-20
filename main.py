# -*- coding: utf-8 -*-
#
#  main.py
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
Welcome to TAFY!

Tactical
Advanced
Foam
Yeeter

TAFY is designed to be a modular, extensible, flexible firmware for foam dart blasters written in MicroPython for the Raspberry Pi Pico 2

Features:
    - Supports multiple firing mechanisms:
        - AEB/AEGs
        - Flywheelers
        - Ability to easily add more!
    - Supports multiple display output types:
        - 3x 7-segment displays over I2C
        - OLED over I2C or UART
        - LED array controlled by I2C or UART LED controller
    - Startup sound
    - Safety switch
    - SmartBus
        - SmartBus is a modular, hot-swappable I2C based bus system, adding support for SmartMags, barrel extensions, and more!
    - LED arrays
    - Updates over I2C

TAFY and associated hardware files are 100% open-source and free to use!
"""
import json
from machine import Pin, PWM
from time import sleep_ms

BUZZER_PIN = 15

# -------------
# JSON loaders
# -------------

def load_json(filename, default):
    try:
        with open(filename) as f:
            return json.load(f)
    except:
        return default

config = load_json("config.json", {
    "startup_sound": True,
    "startup_tune": "nerf_arming_v1",
    "volume": 0.5
})

tunes = load_json("tunes.json", {
    "startup": {},
    "status": {}
})

# -------------
# Core playback
# -------------

def _play_tune_dict(tune_dict, volume):
    """Play a tune dict of form { 'tempo': float, 'notes': [[freq, dur_ms], ...] }."""
    if not tune_dict:
        return

    notes = tune_dict.get("notes", [])
    tempo = tune_dict.get("tempo", 1.0)

    buzzer = PWM(Pin(BUZZER_PIN))
    duty = int(65535 * max(0.0, min(1.0, volume)))  # clamp 0..1

    for freq, dur_ms in notes:
        dur = int(dur_ms * tempo)

        if freq <= 0:
            buzzer.duty_u16(0)
        else:
            buzzer.freq(int(freq))
            buzzer.duty_u16(duty)

        sleep_ms(dur)

    buzzer.duty_u16(0)
    buzzer.deinit()

def play_tune(name, category="startup", volume=None):
    """Play tune by name and category: 'startup' or 'status'."""
    cat = tunes.get(category, {})
    tune = cat.get(name)
    if not tune:
        return  # silently ignore unknown

    if volume is None:
        volume = config.get("volume", 0.5)

    _play_tune_dict(tune, volume)

# -------------
# Convenience wrappers
# -------------

def play_startup_tune():
    if not config.get("startup_sound", True):
        return
    name = config.get("startup_tune", "nerf_arming_v1")
    play_tune(name, category="startup")

def play_status_sound(name, volume=None):
    play_tune(name, category="status", volume=volume)





def main() -> None:
    """Main TAFY Loop"""
    # Call this early from your main boot sequence
    startup_sound()




if __name__ == "__main__":
    main()

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
from machine import Pin, PWM
import time
import json


def load_config():
    try:
        with open("config.json", "r") as file:
            output = json.load(file)
    except:
        output = {
    "frequency": 2,
    "buzzer_pin": 25,
    "startup_sound": True,
    "volume": 0.5
}
    return output


def load_tunes():
    try:
        with open("tunes.json", "r") as file:
            output = json.load(file)
    except:
        output = {
  "startup": {
    "nerf_arming_v1": {
      "tempo": 1.0,
      "notes": [
        [1047, 80],
        [1397, 80],
        [2093, 60],
        [0,    40],
        [1568, 120]
      ]
    }
  },
  "status": {
    "low_battery": {
      "tempo": 1.0,
      "notes": [
        [988,  150],
        [784,  200],
        [523,  300]
      ]
    },
    "battery_charged": {
      "tempo": 1.0,
      "notes": [
        [784,  120],
        [988,  120],
        [1319, 160]
      ]
    },
    "safety_on": {
      "tempo": 1.0,
      "notes": [
        [784,  60],
        [523,  100]
      ]
    },
    "safety_off": {
      "tempo": 1.0,
      "notes": [
        [523,  60],
        [784,  100]
      ]
    },
    "mode_changed": {
      "tempo": 1.0,
      "notes": [
        [1319, 60],
        [1568, 80]
      ]
    }
  }
}
    return output


def play_tune(event, config, tunes):
    if event.lower() == "startup":
        try:
            tune = tunes[event][config["startup_sound"]]
        except:
            # No tune found with that name
            return
    else:
        try:
            tune = tunes["status"][event]
        except:
            return

    notes = tune["notes"]
    tempo = tune["tempo"]

    buzzer = PWM(Pin(config["buzzer_pin"]))
    # Scale volume (0.0–1.0) into duty_u16 (0–65535)
    duty = int(65535 * max(0.0, min(1.0, config["volume"])))

    for freq, dur_ms in notes:
        dur = int(dur_ms * tempo)

        if freq <= 0:
            buzzer.duty_u16(0)
        else:
            buzzer.freq(int(freq))
            buzzer.duty_u16(duty)

        time.sleep_ms(dur)

    buzzer.duty_u16(0)
    buzzer.deinit()


def main():
    """Main TAFY Loop"""
    # Call this early from your main boot sequence
    led = Pin("LED", Pin.OUT)
    config = load_config()
    tunes = load_tunes()
    play_tune("startup", config, tunes)
    # Blink LED to show we are online

    flop = False
    while True:
        if flop:
            led.value(0)
            flop = False
        else:
            led.value(1)
            flop = True
        time.sleep(config["frequency"])



if __name__ == "__main__":
    main()

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

TAFY is designed to be a modular, extensible, flexible firmware for
foam dart blasters written in MicroPython for the Raspberry Pi Pico 2

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
        - SmartBus is a modular, hot-swappable I2C based system
        - adds support for SmartMags, barrel extensions, and more!
    - LED arrays
    - Updates over I2C

TAFY and associated hardware files are 100% open-source and free to use!
"""
import time
import json
from machine import Pin, PWM, I2C, Timer
import fire_mech as fm
import display
import SmartBus

# Global variables
VERSION = "v0.0.5-alpha0"


def load_config():
    """Load Global config. If an error occurs, return a hard-coded default"""
    try:
        with open("config/main.json", "r") as file:
            output = json.load(file)
    except:
        output = {
    "frequency": 0.5,
    "buzzer_pin": 25,
    "startup_sound": True,
    "volume": 0.5,
    "blaster_type": "flywheel_mechanical",
    "display_type": "dummy",
    "aeb_steps_per_cycle": 800,
    "aeb_step_freq_hz": 800,
    "flywheel_pwm_pin": 1,
    "flywheel_rev_pin": 28,
    "flywheel_rev_pin_normal": 0,
    "flywheel_pwm_freq": 1000,
    "flywheel_pwm_duty": 1.0,
    "dart_capacity": 30,
    "SmartBus_enabled": True,
    "internal_light": True,
    "Internal_SDA": 19,
    "Internal_SCL": 18,
    "Internal_freq": 400000,
    "SmartBus_SDA": 16,
    "SmartBus_SCL": 17,
    "SmartBus_ID": 26,
    "SmartBus_Freq": 400000,
    "I2C_MAP": { "0": [0, 1, 4, 5, 8, 9, 12, 13, 16, 17, 20, 21],
                 "1": [2, 3, 6, 7, 10, 11, 14, 15, 18, 19, 26, 27]
                }
}
    output["I2C_MAP"][0] = output["I2C_MAP"]["0"]
    output["I2C_MAP"][1] = output["I2C_MAP"]["1"]
    del output["I2C_MAP"]["0"]
    del output["I2C_MAP"]["1"]
    return output


def load_tunes():
    """Load Tune config. If an error occurs, return a hard-coded default"""
    try:
        with open("config/tunes.json", "r") as file:
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


def load_SmartBus_config():
    """Load SmartBus conbfig and Manifest. If an error occurs, return a hard-coded default"""
    try:
        with open("config/SmartBus_Manifest.json", "r") as file:
            output = json.load(file)
    except:
        output = {
  "smartbus": {
    "devices": [
      {
        "name": "smartspine_v1",
        "role": "mag_spine",
        "rid_bucket_ohms": 47000,
        "i2c_addresses": [48],

        "provides": ["ammo_level", "mag_id"],
        "consumes": ["fire_mode", "blaster_state"],

        "routes": {
          "to_firing_system": ["ammo_level"],
          "to_display": ["ammo_level", "mag_id"],
          "to_device": []
        }
      },

      {
        "name": "smartmag_v1",
        "role": "mag",
        "rid_bucket_ohms": 22000,
        "i2c_addresses": [49],

        "provides": ["ammo_level", "mag_id"],
        "consumes": ["fire_mode", "blaster_state"],

        "routes": {
          "to_firing_system": ["ammo_level"],
          "to_display": ["ammo_level", "mag_id"],
          "to_device": []
        }
      },

      {
        "name": "barrel_chrono_v1",
        "role": "barrel",
        "rid_bucket_ohms": 33000,
        "i2c_addresses": [80],

        "provides": ["muzzle_velocity"],
        "consumes": ["fire_mode", "blaster_state"],

        "routes": {
          "to_firing_system": [],
          "to_display": ["muzzle_velocity"],
          "to_device": ["blaster_state"]
        }
      },

      {
        "name": "power_only",
        "role": "power_only",
        "rid_bucket_ohms": 4700,
        "i2c_addresses": [],

        "provides": [],
        "consumes": [],

        "routes": {
          "to_firing_system": [],
          "to_display": [],
          "to_device": []
        }
      }
    ],

    "defaults": {
      "mag_role_priority": ["mag", "mag_spine"],
      "max_devices": 4
    }
  }
}

    return output


def play_tune(event, config, tunes, buzzer):
    """Play tune over piezo or low-power speaker using PWM"""
    if event.lower() == "startup":
        try:
            tune = tunes[event][config["startup_sound"]]
        except KeyError:
            # No tune found with that name
            print(f"No tune found with name: {config['startup_sound']}")
            return
    else:
        try:
            tune = tunes["status"][event]
        except KeyError:
            # No tune found with that name
            print(f"No tune found with name: {event}")
            return

    notes = tune["notes"]
    tempo = tune["tempo"]

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


def init(config, manifest):
    """Initialize Libraries and Hardware"""
    output_fm = None
    output_display = None
    if config["blaster_type"] in fm.available():
        output_fm = fm.load(config["blaster_type"])
    if config["display_type"] in display.available():
        output_display = display.load(config["display_type"])

    if config["Internal_SCL"] in config["I2C_MAP"][0]:
        if config["Internal_SDA"] in config["I2C_MAP"][0]:
            bus = 0
    elif config["Internal_SCL"] in config["I2C_MAP"][1]:
        if config["Internal_SDA"] in config["I2C_MAP"][1]:
            bus = 1
    else:
        raise Exception("INTERNAL I2C lines not on same bus")
    int_i2c = I2C(bus, scl=Pin(config["Internal_SCL"], Pin.PULL_UP),
                  sda=Pin(config["Internal_SDA"], Pin.PULL_UP),
                  freq=config["Internal_freq"])

    # Here, we should now run any hardware initialization code we need to.
    if output_display is not None:
        try:
            output_display.init(config, int_i2c)
        except Exception as e:
            print(f"ERROR SETTING UP DISPLAY: {e}")
            print("Falling back to no-display mode")
            output_display = display.load("dummy")
    else:
        print("COULD NOT FIND VALID DISPLAY!")
        print("Falling back to no-display mode")
        output_display = display.load("dummy")


    if output_fm is not None:
        output_fm.init(config)


    SmartBus.init(config, manifest)

    print("Successfully Initialized!")

    return (output_fm, output_display, int_i2c)


def blink(sleep, led):
  """Blink built-in LED"""
  flop = False
  while True:
    if flop:
      led.value(0)
      flop = False
    else:
      led.value(1)
      flop = True
    time.sleep(sleep)


def main():
    """Main TAFY Loop"""
    # Call this early from your main boot sequence
    led = Pin("LED", Pin.OUT)
    try:
        config = load_config()
    except Exception as error:
        print(f"FATAL CONFIG ERROR: {error}")
        blink(1, led)

    config["VERSION"] = VERSION
    buzzer = PWM(Pin(config["buzzer_pin"]))

    try:
        tunes = load_tunes()
    except Exception as error:
        print(f"FATAL TUNE CONFIG ERROR: {error}")
        blink(0.5, led)
    try:
        SmartBus_config = load_SmartBus_config()
    except Exception as error:
        print(f"FATAL SMARTBUS CONFIG ERROR: {error}")
        play_tune("error", config, tunes, buzzer)
        blink(0.3, led)
    try:
        mech, disp, int_i2c = init(config, SmartBus_config)
    except Exception as error:
        # Fatal Error. Set the onboard LED to always on to show the error.
        print(f"FATAL DRIVER/SMARTBUS ERROR: {error}")
        play_tune("error", config, tunes, buzzer)
        blink(0.25, led)

    if disp is None:
        print(f"No known working driver for display of type: {config['display_type']}")
        play_tune("warning", config, tunes, buzzer)
    print(f"Loaded driver for display of type: {disp.DISPLAY_TYPE}")


    if mech is None:
        print(f"No known working driver for firing mechanisims of type: {config['blaster_type']}")
        blink(3, led)
        play_tune("error", config, tunes, buzzer)
        return
    print(f"Loaded driver for firing mechanism of type: {mech.FIRE_TYPE}")


    # Safety low == safety on, therefore, set the safety pin to default low
    # in case of a disconnect for safety purposes
    safety_pin = Pin(config["safety_pin"], Pin.IN, Pin.PULL_DOWN)
    print(f"Welcome to TAFY! Version: {VERSION}")
    play_tune("startup", config, tunes, buzzer)
    # buzzer = PWM(Pin(config["buzzer_pin"]))
    # buzzer.freq(2000)
    # buzzer.duty_u16(32768)
    # time.sleep(10)
    # buzzer.duty_u16(0)
    # Set LED to on to show we are online
    if config["internal_light"]:
        led.value(1)

    if mech.HARDWARE_CONFIG["motor"]:
        # Most devices have a motor
        # First up, the flywheel blaster with a mechanical pusher:
        if mech.HARDWARE_CONFIG == {"rev_switch": True, "motor": True,
                                    "solenoid": False, "fire_switch": False}:
            while True:
                if not is_safety_on(safety_pin):
                    disp.STATE["SAFETY"] = False

                    # this line is here for future enablement. This allows
                    # us to control what mode the display says we're in
                    # disp.STATE["MODE"] = None
                    if mech.spin_up_trigger_pulled():
                        # print("Trigger pulled!")
                        mech.spin_up()
                # Both of these else statements need to exist so we don't
                # constantly keep turning flywheels or AEB motors on and off
                # over and over, but also so that if the safety is suddenly
                # turned on, then we turn the flywheels off automatically
                    else:
                        # print("Trigger released")
                        mech.spin_down()
                else:
                    # print("Trigger released")
                    mech.spin_down()
                time.sleep(0.01)

    else:
        # The only device without a motor is a solenoid blaster or solenoid-backed AEB
        while True:
            if mech.fire_trigger_pulled():
                mech.trigger_solenoid()
            time.sleep(0.01)




def is_safety_on(pin):
    """Get the state of the safety pin. Low means the safety is on, High means it is off."""
    # The reason we do the below if statements instead of just:
    #   return (pin.value() == 0)
    # is because if the internal pull down resistor isn't working, and we get a disconnect,
    # we want to err on the side of caution. This may be a Nerf blaster, but
    # we don't want anyone getting shot in the eyes.
    if pin.value() == 0:
        return True
    if pin.value() == 1:
        return False
    return True

if __name__ == "__main__":
    main()

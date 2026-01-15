# -*- coding: utf-8 -*-
#
#  main.py
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
import _thread
from machine import Pin, PWM, I2C, Timer
import micropython
import fire_mech as fm
import display
import SmartBus
import config

# Global variables
VERSION = "v0.0.8-alpha0"


def play_tune(event, local_config, buzzer):
    """Play tune over piezo or low-power speaker using PWM"""
    tunes = local_config.get_section("tunes")
    if event.lower() == "startup":
        try:
            tune = tunes["startup"][local_config.get("main", "startup_sound")]
        except KeyError:
            # No tune found with that name
            print(f"No tune found with name: {local_config.get("main", "startup_sound")}")
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
    duty = int(65535 * max(0.0, min(1.0, local_config.get("main", "volume"))))

    for freq, dur_ms in notes:
        dur = int(dur_ms * tempo)

        if freq <= 0:
            buzzer.duty_u16(0)
        else:
            buzzer.freq(int(freq))
            buzzer.duty_u16(duty)

        time.sleep_ms(dur)

    buzzer.duty_u16(0)


def init_locks():
    """Initialize all the locks we will need"""
    return {"state": _thread.allocate_lock(),
            "i2c_int": _thread.allocate_lock(),
            "i2c_sb": _thread.allocate_lock(),
            "uart" : _thread.allocate_lock()}


def init(local_config):
    """Initialize Libraries and Hardware"""
    output_fm = None
    output_display = None
    locks = init_locks()
    if local_config.get("main", "blaster_type") in fm.available():
        output_fm = fm.load(local_config.get("main", "blaster_type"))
    if local_config.get("main", "display_type") in display.available():
        output_display = display.load(local_config.get("main", "display_type"))

    if local_config.get("pin_out", "Internal_SCL") in local_config.get("pin_out", "I2C_MAP")["0"]:
        if local_config.get("pin_out", "Internal_SDA") in local_config.get("pin_out", "I2C_MAP")["0"]:
            bus = 0
    elif local_config.get("pin_out", "Internal_SCL") in local_config.get("pin_out", "I2C_MAP")["1"]:
        if local_config.get("pin_out", "Internal_SDA") in local_config.get("pin_out", "I2C_MAP")["1"]:
            bus = 1
    else:
        raise RuntimeError("INTERNAL I2C lines not on same bus")
    int_i2c = I2C(bus, scl=Pin(local_config.get("pin_out", "Internal_SCL"), Pin.PULL_UP),
                  sda=Pin(local_config.get("pin_out", "Internal_SDA"), Pin.PULL_UP),
                  freq=local_config.get("main", "Internal_freq"))

    # Here, we should now run any hardware initialization code we need to.
    disp = None
    if output_display is not None:
        try:
            disp = output_display.init(local_config, int_i2c, locks)
        except Exception as e:
            print(f"ERROR SETTING UP DISPLAY: {e}")
            print("Falling back to no-display mode")
            output_display = display.load("dummy")
            disp = output_display.init(config, int_i2c, locks)
    else:
        print("COULD NOT FIND VALID DISPLAY!")
        print("Falling back to no-display mode")
        output_display = display.load("dummy")
        disp = output_display.init(config, int_i2c, locks)




    if output_fm is not None:
        output_fm.init(local_config)

    background_procs = [disp]
    procs = SmartBus.init(local_config, locks)
    if isinstance(procs, (list, tuple)):
        background_procs = background_procs + procs
    else:
        background_procs.append(procs)
    _thread.start_new_thread(background_process, (background_procs, local_config, locks))

    print("Successfully Initialized!")

    return (output_fm, output_display, locks)


def blink(sleep, led):
    """Blink built-in LED"""
    while True:
        led.toggle()
        time.sleep(sleep)


def main():
    """Main TAFY Loop"""
    # Call this early from your main boot sequence
    led = Pin("LED", Pin.OUT)
    try:
        CONFIG = config.Config(VERSION)
    except Exception as error:
        print(f"FATAL CONFIG ERROR: {error}")
        blink(1, led)

    buzzer = PWM(Pin(CONFIG.get("pin_out", "buzzer_pin")))

    try:
        mech, disp, locks = init(CONFIG)
    except Exception as error:
        # Fatal Error. Set the onboard LED to always on to show the error.
        print(f"FATAL DRIVER/SMARTBUS ERROR: {error}")
        play_tune("error", CONFIG, buzzer)
        blink(0.25, led)

    print(f"Loaded driver for display of type: {disp.DISPLAY_TYPE}")

    if mech is None:
        print(f"No known working driver for firing mechanisims of type: {CONFIG.get("main", 'blaster_type')}")
        blink(3, led)
        play_tune("error", CONFIG, buzzer)
        return
    print(f"Loaded driver for firing mechanism of type: {mech.FIRE_TYPE}")


    # Safety low == safety on, therefore, set the safety pin to default low
    # in case of a disconnect for safety purposes
    mode_switch = {"SINGLE": Pin(CONFIG.get("pin_out", "mode_single"), Pin.IN, Pin.PULL_DOWN),
                   "BURST": Pin(CONFIG.get("pin_out", "mode_burst"), Pin.IN, Pin.PULL_DOWN),
                   "AUTO": Pin(CONFIG.get("pin_out", "mode_auto"), Pin.IN, Pin.PULL_DOWN),
                   "SAFE": Pin(CONFIG.get("pin_out", "safety_pin"), Pin.IN, Pin.PULL_DOWN)}
    print(f"Welcome to TAFY! Version: {VERSION}")
    play_tune("startup", CONFIG, buzzer)
    # buzzer = PWM(Pin(config["buzzer_pin"]))
    # buzzer.freq(2000)
    # buzzer.duty_u16(32768)
    # time.sleep(10)
    # buzzer.duty_u16(0)
    # Set LED to on to show we are online
    if CONFIG.get("main", "internal_light"):
        led.value(1)

    prev_mode = None
    if mech.HARDWARE_CONFIG["motor"]:
        # Most devices have a motor
        # First up, the flywheel blaster with a mechanical pusher:
        if mech.HARDWARE_CONFIG == {"rev_switch": True, "motor": True,
                                    "solenoid": False, "fire_switch": False}:


            while True:
                mode = get_mode(mode_switch)

                if mode == "SAFE":
                    if prev_mode != mode:
                        play_tune("safety_on", CONFIG, buzzer)
                        mech.spin_down()
                        with locks["state"]:
                            disp.STATE["MODE"] = "SAFE"
                            disp.STATE["DIRTY"] = True
                        prev_mode = mode

                else:
                    if prev_mode != mode:
                        if prev_mode == "SAFE":
                            play_tune("safety_off", CONFIG, buzzer)
                        else:
                            play_tune("mode_changed", CONFIG, buzzer)
                        with locks["state"]:
                            disp.STATE["MODE"] = mode
                            disp.STATE["DIRTY"] = True
                        prev_mode = mode
                        # this line is here for future enablement. This allows
                        # us to control what mode the display says we're in
                        if mech.spin_up_trigger_pulled():
                            mech.spin_up()

        if CONFIG.get("main", "mode").lower() == "debug":
            micropython.mem_info()

    else:
        # The only device without a motor is a solenoid blaster or solenoid-backed AEB
        while True:
            if mech.fire_trigger_pulled():
                mech.trigger_solenoid()
            time.sleep(0.01)


def background_process(funcs: list, local_config: dict, locks: dict) -> None:
    """Main background process"""
    count = 0
    for each in funcs:
        if each is None:
            count += 1
    if count == len(funcs):
        print("No functions to run! Closing background thread!")
        return
    # Wait 4 seconds to let the rest of the system start up.
    time.sleep(4)
    while True:
        for each in funcs:
            each(local_config, locks)
            time.sleep(0.01)
        time.sleep(0.01)


# This functions are not to run continuously. Other operations must be performed in the main loop
# Further, these functions DO NOT CHECK THE SAFETY. That is done in the main loop.
# In fact, none of these should interact with pins directly, but instead use the helper functions.
def single_shot():
    pass


def burst_shot():
    pass


def full_auto():
    pass


def get_mode(mode_pins) -> str:
    """Get current mode. If no pins or more than one pin are pulled high, default to safe."""
    # If safe is pulled high, nothing else matters, we're safe.
    if mode_pins["SAFE"].value():
        return "SAFE"

    if mode_pins["SINGLE"].value() and not mode_pins["BURST"].value() and not mode_pins["AUTO"].value():
        return "SINGLE"

    if mode_pins["BURST"].value() and not mode_pins["SINGLE"].value() and not mode_pins["AUTO"].value():
        return "BURST"

    if mode_pins["AUTO"].value() and not mode_pins["BURST"].value() and not mode_pins["SINGLE"].value():
        return "AUTO"

    return "SAFE"


def update(completed=False):
    """This function is only to be called when an update is being started or done."""
    led = Pin('LED', Pin.OUT)
    try:
        CONFIG = config.Config(VERSION)
    except Exception as error:
        print(f"FATAL CONFIG ERROR: {error}")
        blink(1, led)

    locks = init_locks()

    buzzer = PWM(Pin(CONFIG.get("pin_out", "buzzer_pin")))

    if CONFIG.get("main", "display_type") in display.available():
        output_display = display.load(CONFIG.get("main", "display_type"))

    if CONFIG.get("pin_out", "Internal_SCL") in CONFIG.get("pin_out", "I2C_MAP")["0"]:
        if CONFIG.get("pin_out", "Internal_SDA") in CONFIG.get("pin_out", "I2C_MAP")["0"]:
            bus = 0
    elif CONFIG.get("pin_out", "Internal_SCL") in CONFIG.get("pin_out", "I2C_MAP")["1"]:
        if CONFIG.get("pin_out", "Internal_SDA") in CONFIG.get("pin_out", "I2C_MAP")["1"]:
            bus = 1
    else:
        raise RuntimeError("INTERNAL I2C lines not on same bus")
    int_i2c = I2C(bus, scl=Pin(CONFIG.get("pin_out", "Internal_SCL"), Pin.PULL_UP),
                  sda=Pin(CONFIG.get("pin_out", "Internal_SDA"), Pin.PULL_UP),
                  freq=CONFIG.get("main", "Internal_freq"))

    # Here, we should now run any hardware initialization code we need to.
    disp = None
    if output_display is not None:
        disp = output_display.init(CONFIG, int_i2c, locks, silent=True, split_thread=False)

    if not completed:
        def timer(_):
            led.toggle()

        tim = Timer()
        tim.init(freq=10, mode=Timer.PERIODIC, callback=timer)

        print("Updating...")
        if "display_string" in dir(disp):
            disp.display_string("Updating...")
    else:
        led.value(1)
        play_tune("update_complete", CONFIG, buzzer)
        print("UPDATE COMPLETE!")
        if "display_string" in dir(disp):
            disp.display_string("Update Complete!")


if __name__ == "__main__":
    main()

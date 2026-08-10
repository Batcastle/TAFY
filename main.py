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
import misc

# Global variables
VERSION = "v0.2.1-alpha2"


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
    return {"i2c_int": _thread.allocate_lock(),
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
        else:
            raise RuntimeError("INTERNAL I2C lines not on same bus")
    elif local_config.get("pin_out", "Internal_SCL") in local_config.get("pin_out", "I2C_MAP")["1"]:
        if local_config.get("pin_out", "Internal_SDA") in local_config.get("pin_out", "I2C_MAP")["1"]:
            bus = 1
        else:
            raise RuntimeError("INTERNAL I2C lines not on same bus")
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
            disp = output_display.init(local_config, int_i2c, locks)
    else:
        print("COULD NOT FIND VALID DISPLAY!")
        print("Falling back to no-display mode")
        output_display = display.load("dummy")
        disp = output_display.init(local_config, int_i2c, locks)

    background_procs = []
    try:
        background_procs.append(misc.controls.init(int_i2c, local_config, locks))
        background_procs.append(misc.battery.init(local_config, output_display))
    except Exception as e:
        print(f"Error setting up MISC: {e}")


    if output_fm is not None:
        output_fm = output_fm.FireMechanism(local_config)

    background_procs.append(disp)
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

    run_mode = CONFIG.get("main", "mode").lower()
    buzzer = PWM(Pin(CONFIG.get("pin_out", "buzzer_pin")))

    try:
        mech, disp, locks = init(CONFIG)
    except Exception as error:
        # Fatal Error. Set the onboard LED to always on to show the error.
        print(f"FATAL DRIVER/SMARTBUS ERROR: {error}")
        play_tune("error", CONFIG, buzzer)
        blink(0.25, led)

    if run_mode == "debug":
        print(f"Loaded driver for display of type: {disp.STATE.DISPLAY_TYPE}")

    if mech is None:
        print(f"No known working driver for firing mechanisims of type: {CONFIG.get("main", 'blaster_type')}")
        blink(3, led)
        play_tune("error", CONFIG, buzzer)
        return
    if run_mode == "debug":
        print(f"Loaded driver for firing mechanism of type: {mech.FIRE_TYPE}")


    # Safety low == safety on, therefore, set the safety pin to default low
    # in case of a disconnect for safety purposes
    pins = {"SINGLE": Pin(CONFIG.get("pin_out", "mode_single"), mode=Pin.IN, pull=Pin.PULL_DOWN),
            "BURST": Pin(CONFIG.get("pin_out", "mode_burst"), mode=Pin.IN, pull=Pin.PULL_DOWN),
            "AUTO": Pin(CONFIG.get("pin_out", "mode_auto"), mode=Pin.IN, pull=Pin.PULL_DOWN),
            "SAFE": Pin(CONFIG.get("pin_out", "safety_pin"), mode=Pin.IN, pull=Pin.PULL_DOWN)}
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


    # Main fire loop
    internal_state = {"SHOTS_FIRED": 0,
                      "MAX_SHOTS": 0}


    previous_mode = get_mode(pins, debug=(run_mode == "debug"))
    current_mode = get_mode(pins, debug=(run_mode == "debug"))
    disp.STATE.set("MODE", current_mode)
    disp.STATE.set("DIRTY", True)
    muted = (CONFIG.get("main", "volume") == 0)
    burst_shot_count = CONFIG.get("main", "burst_mode_shots")
    low_battery_limit = CONFIG.get("main", "battery_low_threshold")
    critical_battery_limit = CONFIG.get("main", "battery_critical_threshold")
    low_battery_alert_played = False
    critical_battery_alert_played = False
    while True:
        # Notify user of mode change, update display and play sound
        if previous_mode != current_mode:
            disp.STATE.set("MODE", current_mode)
            disp.STATE.set("DIRTY", True)
            if previous_mode == "SAFE":
                play_tune("safety_off", CONFIG, buzzer)
            elif current_mode == "SAFE":
                play_tune("safety_on", CONFIG, buzzer)
            else:
                play_tune("mode_changed", CONFIG, buzzer)
            previous_mode = current_mode

        if run_mode == "debug":
            print(f"MODE: {current_mode}")

        # Handle current mode
        if current_mode == "SINGLE":
            internal_state["MAX_SHOTS"] = 1
        elif current_mode == "BURST":
            internal_state["MAX_SHOTS"] = burst_shot_count
        elif current_mode == "AUTO":
            internal_state["MAX_SHOTS"] = -1

        # Fire as necessary
        if current_mode != "SAFE":
            # Not all blasters are flywheels.
            # As such, only flywheelers have rev triggers
            if mech.HARDWARE_CONFIG["rev_switch"]:
                if mech.rev_trigger_pulled():
                    mech.spin_up()
                else:
                    mech.spin_down()

            # Most blasters where it makes sense to have TAFY give access to triggers.
            # So, we go ahead and call this. If a blaster has TAFY but no access to triggers,
            # This function should always return False
            if mech.fire_trigger_pulled():
                fire_handler(mech, disp, locks, internal_state)
            else:
                internal_state["SHOTS_FIRED"] = 0
        else:
            internal_state["SHOTS_FIRED"] = 0

        # Update mode
        current_mode = get_mode(pins, debug=(run_mode == "debug"))

        # Print memory info if in debug mode
        if run_mode == "debug":
            micropython.mem_info()

        # Detect mute/unmute transitions and react accordingly.
        # This has to run every tick regardless of the previous state --
        # only checking the volume while already muted means `muted` can
        # only ever go False->once and never flips back to True, so a
        # later mute->unmute cycle would be invisible to this code.
        currently_muted = (CONFIG.get("main", "volume") == 0)
        if currently_muted != muted:
            if currently_muted:
                if run_mode == "debug":
                    print("Muted!")
            else:
                if run_mode == "debug":
                    print("Playing Unmute tone!")
                play_tune("unmuted", CONFIG, buzzer)
            muted = currently_muted

        # Play alert tones depending on battery state
        if disp.STATE.get("BATTERY") is not None:
            if disp.STATE.get("CHARGING") not in (None, True):
                # Alert code
                charge = round(disp.STATE.get("BATTERY"), ndigits=2)
                if charge < low_battery_limit:
                    if charge >= critical_battery_limit:
                        if not low_battery_alert_played:
                            play_tune("low_battery", CONFIG, buzzer)
                            low_battery_alert_played = True
                            critical_battery_alert_played = False
                    else:
                        if not critical_battery_alert_played:
                            play_tune("critical_battery", CONFIG, buzzer)
                            critical_battery_alert_played = True
                else:
                    critical_battery_alert_played = False
                    low_battery_alert_played = False
            else:
                low_battery_alert_played = False
                critical_battery_alert_played = False



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
            if each is not None:
                each(local_config, locks)


def fire_handler(mech, disp, locks, state):
    """Handle firing for all fire modes"""
    # Stop firing at whatever necessary for fire mode
    if state["MAX_SHOTS"] != -1:
        if state["SHOTS_FIRED"] >= state["MAX_SHOTS"]:
            return

    mech.fire()
    if disp.STATE.get("CAPACITY")> 0:
        disp.STATE.set("CAPACITY", disp.STATE.get("CAPACITY") - 1)
        disp.STATE.set("DIRTY", True)
    state["SHOTS_FIRED"] += 1


def get_mode(mode_pins: dict, debug=False) -> str:
    """Get current fire mode"""
    # 1. Read all states ONCE to save time and ensure consistency
    is_safe   = get_pin_value(mode_pins["SAFE"])
    is_single = get_pin_value(mode_pins["SINGLE"])
    is_burst  = get_pin_value(mode_pins["BURST"])
    is_auto   = get_pin_value(mode_pins["AUTO"])

    # 2. Logic Check
    if is_safe:
        return "SAFE"

    # Check for exactly one pin being high
    if is_single and not is_burst and not is_auto:
        return "SINGLE"

    if is_burst and not is_single and not is_auto:
        return "BURST"

    if is_auto and not is_single and not is_burst:
        return "AUTO"

    if debug:
        print("ERROR! Pins are not toggling right!")
        print(f"STATE:\n\tSINGLE: {is_single}\n\tBURST: {is_burst}\n\tAUTO: {is_auto}")
    # Default if multiple pins are high or none are high
    return "SAFE"


def get_pin_value(pin) -> bool:
    """Get a debounced value for given pin"""
    count = 5
    status = {True: 0, False: 0}
    for _ in range(count):
        if pin.value():
            status[True] += 1
        else:
            status[False] += 1
        time.sleep(0.001)
    if status[True] > status[False]:
        return True
    return False


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

    output_display = None
    if CONFIG.get("main", "display_type") in display.available():
        output_display = display.load(CONFIG.get("main", "display_type"))

    if CONFIG.get("pin_out", "Internal_SCL") in CONFIG.get("pin_out", "I2C_MAP")["0"]:
        if CONFIG.get("pin_out", "Internal_SDA") in CONFIG.get("pin_out", "I2C_MAP")["0"]:
            bus = 0
        else:
            raise RuntimeError("INTERNAL I2C lines not on same bus")
    elif CONFIG.get("pin_out", "Internal_SCL") in CONFIG.get("pin_out", "I2C_MAP")["1"]:
        if CONFIG.get("pin_out", "Internal_SDA") in CONFIG.get("pin_out", "I2C_MAP")["1"]:
            bus = 1
        else:
            raise RuntimeError("INTERNAL I2C lines not on same bus")
    else:
        raise RuntimeError("INTERNAL I2C lines not on same bus")
    int_i2c = I2C(bus, scl=Pin(CONFIG.get("pin_out", "Internal_SCL"), Pin.PULL_UP),
                  sda=Pin(CONFIG.get("pin_out", "Internal_SDA"), Pin.PULL_UP),
                  freq=CONFIG.get("main", "Internal_freq"))

    # Here, we should now run any hardware initialization code we need to.
    disp = None
    if output_display is not None:
        disp = output_display.init(CONFIG, int_i2c, locks, silent=True, split_thread=False)
    disp.STATE.set("UPDATING", True)

    if not completed:
        def timer(_):
            led.toggle()

        tim = Timer()
        tim.init(freq=10, mode=Timer.PERIODIC, callback=timer)

        if CONFIG.get("main", "mode").lower() == "debug":
            print("Updating...")
        if "display_string" in dir(disp):
            time.sleep(1)
            disp.display_string("Updating...")
    else:
        led.value(1)
        play_tune("update_complete", CONFIG, buzzer)
        if CONFIG.get("main", "mode").lower() == "debug":
            print("UPDATE COMPLETE!")
        if "display_string" in dir(disp):
            disp.display_string("Update Complete!")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
#
#  controls.py
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
Create a unified interface for all control systems except for trigger, safety,
and mode switch. This includes the SEN0502 volume knob, display control
buttons, and more.

SEN0502 I2C register map:
    0x08 : Encoder count value, 2 bytes MSB first, range 0-1023
    0x0A : Button status, 1 byte, bit 0 = pressed
    0x0B : Gain coefficient, 1 byte, range 1-51
           1  = one LED lights per ~2.5 full rotations
           51 = one LED lights per detent (maximum resolution)

I2C addresses (set via DIP switches on rear of module):
    SW1=0, SW2=0 → 0x54 (default)
    SW1=0, SW2=1 → 0x55
    SW1=1, SW2=0 → 0x56
    SW1=1, SW2=1 → 0x57
"""
import time

# SEN0502 register addresses
_REG_ENCODER_VALUE = 0x08   # 2 bytes, MSB first, range 0-1023
_REG_BUTTON_STATUS = 0x0A   # 1 byte,  bit 0 = button pressed
_REG_GAIN          = 0x0B   # 1 byte,  range 1-51

# Module constants
_GAIN_MAX    = 51    # One LED per detent — maximum LED resolution
_LED_COUNT   = 20    # Number of LEDs on the ring
_ENC_MAX     = 1023  # Maximum raw encoder value
_DEBOUNCE_MS = 250   # Minimum time between accepted button presses


class Knob:
    """Abstraction class to handle SEN0502 rotary encoder"""
    def __init__(self, initial_value: int, i2c, locks, addr: int = 0x54) -> None:
        """
        initialise the SEN0502 rotary encoder.

        initial_value : starting encoder position (0-1023 raw counts)
        i2c           : MicroPython I2C object
        addr          : I2C address (default 0x54, both DIP switches off)
        """
        self._addr              = addr
        self.i2c               = i2c
        self.disabled          = False
        self.initial_value     = initial_value
        self._last_btn_state   = False   # raw reading from the previous call
        self._last_btn_time    = 0       # time.ticks_ms() of last accepted click
        self.press_log = {}
        self.max_age = 4000
        self.last_gesture = 0

        # Maximum gain: one LED lights for every detent turned.
        # This gives the tightest LED-to-position coupling and makes
        # set_knob_lights() behave predictably.
        with locks["i2c_int"]:
            self.i2c.writeto_mem(self._addr, _REG_GAIN, bytes([_GAIN_MAX]))

        # Apply starting position
        self._set_raw(initial_value, locks)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set_raw(self, value: int, locks) -> None:
        """Write a raw encoder count (0-1023) to the device."""
        value = max(0, min(_ENC_MAX, int(value)))
        with locks["i2c_int"]:
            self.i2c.writeto_mem(self._addr, _REG_ENCODER_VALUE,
                                 bytes([value >> 8, value & 0xFF]))

    def _get_raw(self, locks) -> int:
        """Read the raw encoder count (0-1023) from the device."""
        with locks["i2c_int"]:
            data = self.i2c.readfrom_mem(self._addr, _REG_ENCODER_VALUE, 2)
        return (data[0] << 8) | data[1]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_knob_position(self, locks) -> int:
        """
        Get the current encoder position scaled to 0-360 degrees.
        Returns 0 when the knob is disabled.
        """
        if self.disabled:
            return 0
        return round(self._get_raw(locks) / _ENC_MAX * 360)

    def get_knob_pressed(self, locks) -> bool:
        """
        Return True exactly once per physical button press (rising edge),
        software debounced.

        Unlike get_knob_position() and set_knob_lights(), this deliberately
        does NOT short-circuit when self.disabled is True. The button must
        keep being read while disabled, since that's the only way a press
        can ever be detected to re-enable the knob — gating this on
        `disabled` would make disable_knob_lights() permanent.

        This is implemented as software edge detection rather than relying
        on the hardware register self-clearing. Without it, every call
        while the button is still physically held (or briefly bouncing on
        release) reads as "pressed" with no way to distinguish an ongoing
        hold from a fresh click — which is exactly what caused mute-on-hold
        / unmute-on-release behaviour previously. Tracking the last raw
        reading ourselves and only firing on the 0->1 transition gives a
        correct one-shot "was clicked" result regardless of whether the
        underlying register is a live level or a latch, as long as it
        reflects "not pressed" again at some point after release.

        A best-effort clear-by-write is still attempted in case the
        hardware does use write-0-to-clear semantics for this register;
        it is harmless if the register turns out to be read-only or uses
        different clear semantics, since the software edge detection below
        does not depend on it.
        """
        with locks["i2c_int"]:
            data    = self.i2c.readfrom_mem(self._addr, _REG_BUTTON_STATUS, 1)
            current = bool(data[0] & 0x01)
            if current:
                self.i2c.writeto_mem(self._addr, _REG_BUTTON_STATUS, bytes([0]))

        fired = False
        if current and not self._last_btn_state:
            now = time.ticks_ms()
            if time.ticks_diff(now, self._last_btn_time) > _DEBOUNCE_MS:
                fired = True
                self._last_btn_time = now

        self._last_btn_state = current
        return fired

    def set_knob_lights(self, amount: int, locks) -> None:
        """
        Light up a given number of LEDs on the ring (0-20).
        Does nothing when the knob is disabled.

        amount=0  → all LEDs off
        amount=20 → all LEDs on
        """
        if self.disabled:
            return
        amount = max(0, min(_LED_COUNT, int(amount)))
        self._set_raw(round(amount / _LED_COUNT * _ENC_MAX), locks)

    def set_knob_lights_position(self, amount: int, locks) -> None:
        """
        Takes an angle, and passes that to set_knob_position(), and unterprets that same position to illuminate that same number of lights
        """
        if self.disabled:
            return
        self.set_knob_position(amount, locks)
        amount = max(0, min(360, int(amount)))
        led_count = round((amount / 360) * 20)
        self._set_raw(round(led_count/ _LED_COUNT * _ENC_MAX), locks)

    def set_knob_position(self, value: int, locks) -> None:
        """
        Set the encoder position in 0-360 degree units.
        Does nothing when the knob is disabled.
        Used by enable_knob_lights() to restore a saved position.
        """
        if self.disabled:
            return
        value = max(0, min(360, int(value)))
        self._set_raw(round(value / 360 * _ENC_MAX), locks)

    def disable_knob_lights(self, locks) -> None:
        """
        Save current position, blank the LED ring, and disable the knob.

        Also drops the gain coefficient to its minimum (1) so that physically
        turning the knob while disabled requires ~2.5 full rotations to light
        a single LED — effectively preventing accidental LED activation from
        physical input while the knob is logically off.
        """
        self.initial_value = self.get_knob_position(locks)
        self.set_knob_lights(0, locks)
        self.disabled = True
        # Drop gain AFTER blanking so set_knob_lights(0) still runs at full
        # resolution, then hand off to minimum gain to suppress physical input.
        with locks["i2c_int"]:
            self.i2c.writeto_mem(self._addr, _REG_GAIN, bytes([1]))

    def enable_knob_lights(self, locks) -> None:
        """
        Re-enable the knob and restore the LED ring to its saved position.

        Restores maximum gain (51) before restoring position so the LED ring
        immediately reflects the correct value at full resolution.
        """
        self.disabled = False
        with locks["i2c_int"]:
            self.i2c.writeto_mem(self._addr, _REG_GAIN, bytes([_GAIN_MAX]))
        self.set_knob_position(self.initial_value, locks)

    def log_knob(self, locks) -> None:
        """Keep an eye on the SEN0502 and log whether it's pressed or not."""
        pressed = self.get_knob_pressed(locks)
        if self.press_log == {}:
            self.press_log[time.ticks_ms()] = pressed
            return
        keys = sorted(self.press_log.keys())
        latest = keys[-1]
        if self.press_log[latest] != pressed:
            self.press_log[time.ticks_ms()] = pressed
        to_del = []
        for each in self.press_log.keys():
            if time.ticks_diff(time.ticks_ms(), each) > self.max_age:
                to_del.append(each)
        for each in to_del:
            del self.press_log[each]

    def get_log(self) -> dict:
        """Provide Press log"""
        return dict(self.press_log)

    def get_latest_gesture(self) -> str:
        """Get latest gesture as a string of periods and underscores. Periods are for short presses. underscores are for long."""
        gesture = ""
        keys = sorted(self.press_log.keys())
        keys.reverse()
        gesture_timeout = 250
        press_timeout = 1000
        for index, item in enumerate(keys):
            """Iterate over presses"""
            # Skip the last key to avoid an IndexError
            if index == (len(keys) - 1):
                break
            if index == 0:
                if self.press_log[item]:
                    # Button is currently pressed. We don't know if it's short or long press so exit and wait and see
                    return ""
                if time.ticks_diff(time.ticks_ms(), item) < gesture_timeout:
                    # Give the human an opportunity to continue the gesture
                    return ""
            if self.press_log[item]:
                # When button was pressed
                if time.ticks_diff(item, keys[index + 1]) > gesture_timeout:
                    break
            else:
                # Button was released
                if time.ticks_diff(item, keys[index + 1]) >= press_timeout:
                    gesture += "_"
                else:
                    gesture += "."
        if gesture == "":
            return ""
        self.last_gesture = time.ticks_ms()
        gesture = list(gesture)
        gesture.reverse()
        gesture = "".join(gesture)
        return gesture


class BackgroundProcess:
    def __init__(self):
        self.processes = []

    def run(self, config, locks):
        for each in self.processes:
            each(config, locks)


def determine_press_type(log: dict, max_time_between_presses=100, time_since_interaction=100) -> dict:
    """Determine how many presses we should operate under"""
    count = {}
    iterable = sorted(log.keys())
    iterable.reverse()
    for each in iterable:
        """How the fuck do we do this???"""


class GestureHandler:
    def __init__(self, config):
        """Register and handle gestures"""
        self.handler_funcs = {}
        self.persistant_storage = {}
        self.config = config

    def register_handler(self, gesture_string: str):
        """Register functions to handle gestures"""
        def decorator(func):
            self.handler_funcs[gesture_string] = func
            return func
        return decorator

    def dispatch(self, gesture_string: str) -> None:
        """Run handler function for a given gesture string"""
        if gesture_string == "":
            return
        self.handler_funcs[gesture_string]()



def init(i2c, config, locks):
    """Initalize control hardware"""
    bp = BackgroundProcess()
    with locks["i2c_int"]:
        results = i2c.scan()
    addr = 0
    for each in config.get("sen0502", "supported"):
        if each in results:
            addr = each
            break
    max_value = config.get("sen0502", "max_init_value")
    volume = config.get("main", "volume")
    knob = Knob(volume * max_value, i2c, locks, addr)
    knob.set_knob_lights_position(volume * 360, locks)

    handler = GestureHandler(config)

    @handler.register_handler(".")
    def toggle_mute():
        """Toggle Mute"""
        if "." not in handler.persistant_storage:
            handler.persistant_storage["."] = {
                                                "default": config.get("main", "volume"),
                                                "current": config.get("main", "volume"),
                                                "muted": config.get("main", "volume") == 0
                                            }
        if knob.disabled:
            handler.persistant_storage["."]["muted"] = False
            knob.enable_knob_lights(locks)
            vol_set = round(handler.persistant_storage["."]["current"] / 360, 2)
            config.set("main", "volume", vol_set)
        else:
            handler.persistant_storage["."]["current"] = config.get("main", "volume")
            handler.persistant_storage["."]["muted"] = True
            config.set("main", "volume", 0)
            knob.disable_knob_lights(locks)

    @handler.register_handler("..")
    def modify_pwm():
        if ".." not in handler.persistant_storage:
            handler.persistant_storage[".."] = {
                                                    "default": config.get("main", "flywheel_pwm_duty")
                                            }


    def check_knob(cfg, lcks):
        """Check Knob settings and report"""
        # print(f"Knob Position: {knob.get_knob_position(lcks)}")
        log = knob.get_log()
        if not knob.disabled:
            if log[sorted(log.keys())[-1]]:
                clicked +=1
                """
                # THE ENCLOSED IS A DISABLED CODEPATH UNTIL THE NECESSARY HARDWARE/SOFTWARE IS IN PLACE TO MAKE USE OF IT
                while click_timeout < 1.5:
                    time.sleep(0.05)
                    if knob.get_knob_pressed(lcks):
                        clicked +=1
                        no_click_timeout = 0
                    else:
                        no_click_timeout += 0.05
                    click_timeout += 0.05
                    if clicked >= 3:
                        clicked = 3
                        break
                    if no_click_timeout >= 0.35:
                        break
                """
                if clicked == 1:
                    cfg.set("main", "volume", 0)
                    knob.disable_knob_lights(lcks)
            else:
                vol_curr = cfg.get("main", "volume")
                vol_set = round(knob.get_knob_position(lcks) / 360, 2)
                if vol_curr != vol_set:
                    cfg.set("main", "volume", vol_set)
        else:
            if knob.get_knob_pressed(lcks):
                clicked +=1
                """
                # THE ENCLOSED IS A DISABLED CODEPATH UNTIL THE NECESSARY HARDWARE/SOFTWARE IS IN PLACE TO MAKE USE OF IT
                while click_timeout < 1.5:
                    time.sleep(0.05)
                    if knob.get_knob_pressed(lcks):
                        clicked +=1
                        no_click_timeout = 0
                    else:
                        no_click_timeout += 0.05
                    click_timeout += 0.05
                    if clicked >= 3:
                        clicked = 3
                        break
                    if no_click_timeout >= 0.35:
                        break
                """
                if clicked == 1:
                    knob.enable_knob_lights(lcks)
                    vol_set = round(knob.initial_value / 360, 2)
                    cfg.set("main", "volume", vol_set)

    def update_log(cfg, lcks):
        """Log Knob pressed state"""
        knob.log_knob(lcks)

    bp.processes.append(check_knob)
    bp.processes.append(update_log)
    return bp.run

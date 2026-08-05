# TAFY
## Tactical Advanced Foam dart Yeeter

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![MicroPython](https://img.shields.io/badge/MicroPython-RP2350-brightgreen)](https://micropython.org/)
[![Version](https://img.shields.io/badge/version-v0.1.8--alpha1-orange)]()
[![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%20Pico%202-red)](https://www.raspberrypi.com/products/raspberry-pi-pico-2/)

TAFY is an open-source, modular, extensible firmware for electric foam dart blasters, written in MicroPython for the Raspberry Pi Pico 2. The goal is universal firmware — one codebase that can run on flywheel pistols, AEB rifles, and everything in between, with smart accessories and deep customizability from boot sounds to pin assignments.

---

## Table of Contents

- [Features](#features)
- [Hardware Requirements](#hardware-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Writing a Driver](#writing-a-driver)
- [SmartBus](#smartbus)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Intended Use](#intended-use)
- [License](#license)

---

## Features

### What Works Right Now

**Modular Fire Mechanism Support**
TAFY auto-discovers fire mechanism drivers at boot. Drop a new `*_fire.py` into the `fire_mech/` folder and it becomes available immediately — no registry to update, no imports to add. Currently included drivers:

- **Flywheel + Solenoid** — Electric flywheels with a solenoid pusher. The primary development target.
- **Flywheel + Sector Gear** — Electric flywheels with a motor-driven sector gear.
- **Flywheel + Mechanical** — Electric flywheels with a mechanical pusher (e.g. a mechanical linkage pushing the dart).

**Modular Display Support**
Same auto-discovery pattern as fire mechanisms. Drop a new `*_display.py` into `display/` and it's available. Currently included drivers:

- **LCD1602 over I2C** — 16x2 character LCD, shows fire mode and ammo count.
- **SSD1309 OLED over I2C** — 128x64 OLED display.
- **SSD1306 OLED over I2C** — 128x64 OLED display *(driver exists, needs testing.)*.
- **7-Segment over I2C** — Numeric display array *(driver in progress)*.
- **Dummy** — No-display fallback. Automatically used if the configured display fails to initialize.

**Fire Modes**
- Single shot
- Burst fire (configurable shot count)
- Full auto
- Safety

Mode is determined by dedicated selector pins with a safe hardware default — if pin state is ambiguous, TAFY falls back to SAFE automatically.

**Startup Sound & Status Tones**
Plays configurable tunes over a piezo buzzer or low-power speaker via PWM. Sounds include startup, safety on/off, mode change, error, and update complete. Fully customizable via `config/tunes.json`.

**Ammo Counter**
Tracks remaining dart capacity and displays it in real time. Capacity is initialized from config and updated on each shot.

**Safety Switch**
Dedicated safety pin, defaulting low (safe) on disconnect. Hardware-safe by design.

**Thread-Safe Config System**
All configuration lives in JSON files under `config/`. The `Config` class provides a thread-safe get/set/dump API with per-file locking. Pin assignments, fire mode behavior, display type, volume, and more are all configurable without touching the code.

**SmartBus Scaffolding**
The I2C-based SmartBus accessory system is initialized and the manifest format is defined. Full device detection and communication are actively in development. See [SmartBus](#smartbus) below.

**Onboard LED Indicator**
Uses the Pico 2's built-in LED to signal status — solid on when running, slow blink on fatal config error, fast blink on driver error.

**OTA Update Support**
`update()` function provides a framework for over-the-air updates over USB (and later SmartBus), with visual and audio feedback during and after the update process.

**Battery percentage reporting and reporting charging status**
On screen indicators show how much battery you have left, and whether your blaster is charging or not.

---

## Hardware Requirements

| Component | Requirement |
|---|---|
| Microcontroller | Raspberry Pi Pico 2 (RP2350) |
| Firmware | MicroPython |
| Fire Mechanism | Configurable |
| Display | LCD1602 (I2C), SSD1309 OLED (I2C), or none |
| Buzzer | Piezo buzzer or low-power speaker on a PWM-capable pin |
| Power | 2S, 3S or 4S LiPo recommended for flywheel builds |

Default pin assignments are defined in `config/pin_out.json` and are fully remappable.

> **Note:** Motors must not be driven directly from Pico GPIO. A MOSFET-based motor driver board is required. Driving motors directly will destroy the Pico.

---

## Installation

**Requirements:** Python 3, `python3-seriel` (`sudo apt install python3-seriel`)

1. Flash MicroPython onto your Pico 2. Official instructions [here](https://micropython.org/download/RPI_PICO2/).

2. Clone this repo:
   ```bash
   git clone https://github.com/Batcastle/TAFY.git
   cd TAFY
   ```

3. Edit `config/main.json` to match your hardware (blaster type, display type, pin assignments, etc.).

4. Deploy to your Pico:
   ```bash
   python deploy.py
   ```

5. Your Pico will reboot and TAFY will start automatically.

---

## Updating

Simply run the deploy script again! It will flash any new or updated files to your Pico!

---

## Configuration

All configuration lives in `config/`. Each `.json` file is loaded at boot and is accessible through the thread-safe `Config` API.

| File | Purpose |
|---|---|
| `main.json` | Core settings: blaster type, display type, fire mode, volume, SmartBus, etc. |
| `pin_out.json` | GPIO pin assignments and I2C bus map |
| `tunes.json` | Startup and status sound definitions |
| `7_seg.json` | 7-segment display settings |
| `lcd1602_i2c.json` | LCD1602 display settings |
| `ssd130x_i2c.json` | SSD1309/SSD1306 OLED settings |
| `led_array_i2c.json` | Settings for LED array displays |
| `SmartBus_Manifest.json` | Known SmartBus device definitions |
| `sen0502.json` | Settings for volume knob |
| `battery.json` | Discharge curves for various battery chemistries |

Key settings in `main.json`:

```json
{
    "blaster_type": "flywheel_solenoid",
    "display_type": "lcd1602_i2c",
    "burst_mode_shots": 3,
    "volume": 0.25,
    "startup_sound": "lcars_boot_sequence",
    "mode": "release"
}
```

Set `"mode": "debug"` to enable verbose serial output and memory reporting.

---

## Writing a Driver

TAFY is designed to be extended. Adding support for a new blaster type or display is straightforward.

### Fire Mechanism Driver

1. Create `fire_mech/yourname_fire.py`
2. Subclass `fire_mech.base.FireMechanism`
3. Set `self.FIRE_TYPE` and `self.HARDWARE_CONFIG` to describe your hardware
4. Implement `fire_trigger_pulled()`, and optionally `rev_trigger_pulled()`, `spin_up()`, `spin_down()`, `fire()`, and `trigger_solenoid()`
5. Set `"blaster_type": "yourname"` in `main.json`

`HARDWARE_CONFIG` tells the main loop what your mechanism supports:

```python
self.HARDWARE_CONFIG = {
    "rev_switch": True,   # Has a separate flywheel rev trigger
    "motor": True,        # Has a motor
    "solenoid": True,     # Has a solenoid
    "fire_switch": True   # Has a fire trigger
}
```

### Display Driver

1. Create `display/yourname_display.py`
2. Define `DISPLAY_TYPE`, `STATE`, and `DISPLAY_MODE` at module level
3. Implement `init(config, i2c_obj, locks, silent=False, split_thread=True)` — return the `display_main` function if `split_thread=True`
4. Implement `display_main(config, locks)` — this runs in the background thread and pushes updates to the display
5. Set `"display_type": "yourname"` in `main.json`

See `display/dummy_display.py` for a minimal template and `display/lcd1602_i2c_display.py` for a full implementation.

### Other Drivers
Other drivers will need much more involved work to create, as they are not needed as often. But, they should be placed under the `misc` directory.

---

## SmartBus

SmartBus is TAFY's modular I2C accessory system. It allows smart devices to be hot-swapped onto the blaster and communicate with the firmware in real time.

**Physical Interface (5 pins):**
- 3.3V power (1A)
- Ground
- I2C SDA
- I2C SCL
- ID/Sense (analog — device type identified by resistor value)

Devices identify themselves by placing a specific resistor value on the ID/Sense line, which forms a voltage divider with an internal resistor on the mainboard. The firmware reads the resulting voltage, calculates the resistance, and looks up the device type in `SmartBus_Manifest.json`.

**Currently Defined Devices:**

| Resistor | Device | Role |
|---|---|---|
| 47kΩ | SmartSpine v1 | Clip-on smart mag adapter (Hall effect follower tracking) |
| 22kΩ | SmartMag v1 | Fully integrated smart magazine |
| 33kΩ | Barrel Chronometer v1 | Muzzle velocity measurement |
| 4.7kΩ | Power Only | Dumb powered accessories (lights, lasers, etc.) |

**SmartMag / SmartSpine**
Smart magazines report real-time ammo level and magazine ID over I2C using Hall effect sensors to track the dart follower position. SmartSpines are clip-on adapters that bring the same capability to standard Talon-compatible magazines, requiring only a small magnet pressed into the follower.

**Barrel Chronometer**
Measures muzzle velocity using IR break-beam sensors at a fixed known distance. Reports FPS to the display in real time. Future versions may include a dedicated onboard processor for higher precision and shot logging.

> SmartBus device detection and communication are actively in development. The manifest format and physical protocol are defined; firmware support for reading and routing device data is coming in an upcoming release.

---

## Roadmap

### Actively In Progress
- **SmartBus device detection** — Resistance reading, manifest lookup, and device initialization
- **Fire system reliability** — Debounce tuning, trigger logic validation, and real-hardware testing on custom PCB
- **Custom PCB hardware** — Dedicated mainboard, motor driver board, power board, and control board replacing the current breadboard prototype
- **USB-C charging** — Onboard charging via BMS integration

### Near Term
- **AEB rifle support** — Motor-driven pusher fire mechanism driver
- **SmartMag integration** — Live ammo count from Hall effect sensor data over SmartBus

### Long Term
- **Barrel Chronometer** — Hardware design and firmware integration for muzzle velocity measurement
- **SmartSpine hardware** — Physical design and production of the clip-on mag adapter
- **Gatling blaster support** — Rotating barrel coordination and high-capacity drum feeding
- **Shotgun blaster support** — Multi-dart simultaneous fire, shell-based capacity tracking
- **CO2/high-pressure sniper support** — Solenoid valve control for ultra-high-velocity builds

### Future Vision
- **High-precision chronometer** — Sub-microsecond timing for velocities well beyond 300fps

---

## Contributing

Contributions are very welcome. TAFY is designed from the ground up to be extended by the community, and the driver system is specifically built to make adding new hardware support approachable even for contributors who are new to embedded development.

**Good places to start:**

- Check the [Issues](https://github.com/Batcastle/TAFY/issues) page for open bugs and feature requests tagged `good first issue`
- Write a fire mechanism or display driver for hardware you own
- Improve documentation or add example configurations

**Guidelines:**

- Follow the existing driver ABI when adding new fire mechanism or display drivers — see [Writing a Driver](#writing-a-driver) above
- Keep hardware-specific logic inside drivers, not in `main.py`
- Configuration values belong in `config/*.json`, not hardcoded in source
- Test on real hardware if possible before submitting a PR

Questions, ideas, or just want to show off your TAFY build? Open an issue or start a discussion — all are welcome.

---

## Intended Use

TAFY is meant for recreational use, like Nerf battles, backyard skirmishes, office games, and community events, where kids and adults can have fun safely. However, depending on your fire mechanism, it can also be a high-performance system, on top of being a modular platform already. So, we would like to be up front about the fact that it can sting at higher speeds, with more powerful blasters, can cause serious eye injury without protection, and could be adapted for use in a real firearm. Because of that, we expect responsible use: wear eye protection, follow basic safety rules, and know your audience. The deciding factor is intent. Plinking, sport shooting, competitive Nerf, and other responsible recreational uses are up to the user, but using TAFY or anything derived from it to deliberately harm or kill someone is completely against what this project stands for. TAFY exists to make Nerf more fun, give blasters more personality, and bring people together, and we ask anyone who builds with it to carry that spirit forward.

---

## License

TAFY is free software, released under the [GNU General Public License v3.0](LICENSE).

Copyright 2026 Thomas Castleman

You are free to use, modify, and distribute this firmware under the terms of the GPL. Any modifications or derivative works must also be released under the GPL. Hardware designs included in this repository are released under the same terms.

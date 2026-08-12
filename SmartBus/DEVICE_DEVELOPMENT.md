# SmartBus Device Development

This document covers everything you need to know to design, implement, and
submit a new SmartBus device for TAFY.

## Overview

A SmartBus device consists of three components:

1. **Hardware** — A physical PCB with a SmartBus connector, an ID resistor,
   and whatever electronics the device needs to function
2. **Manifest entry** — A JSON entry in `config/SmartBus_Manifest.json`
   defining the device's resistor ID, I2C addresses, connection point,
   and data routing metadata
3. **Driver** — A MicroPython module in `SmartBus/drivers/` that TAFY loads
   automatically when the device is detected

For smart devices, all three must be submitted together in a pull request.
Partial submissions will not be accepted. Power-only devices require none
of the above — see the Power-Only Devices section below.

## Before You Start

Before designing a new SmartBus device, you must:

1. **Choose a resistor ID** that does not conflict with any existing entry
   in the Resistor ID Registry in [README.md](README.md)
2. **Choose I2C addresses** that comply with the collision rules below
3. **Choose a connection_point** that makes physical sense for your device
4. **Open a GitHub issue** to reserve your resistor ID and I2C addresses
   before submitting a pull request

Reserving values via an issue first prevents two contributors working on
different devices from accidentally claiming the same values simultaneously.

## Collision Rules

### Resistor ID Collisions

No two devices may share a resistor ID. Period. Even if two devices occupy
mutually exclusive connection points, sharing a resistor ID would prevent TAFY
from distinguishing between them if both were somehow connected simultaneously,
and creates ambiguity in the manifest.

### I2C Address Collisions

The rules for I2C address collisions depend on connection point:

**Strict — no sharing permitted:**
- 0x1A is permanently reserved for SmartDock and may never be used by any
  other device.

**Permitted — mutually exclusive connection points:**
- Two devices that occupy connection points which cannot be physically populated
  simultaneously may share an I2C address.
- Example: Two `barrel` devices may share an address since only one barrel
  device can be connected at a time.
- Example: A `magwell` device and a `barrel` device may share an address
  if no blaster shell has both connection points populated simultaneously.

**When in doubt, do not share.** The I2C address space is large enough
that sharing is rarely necessary.

### Checking for Collisions

Before submitting a pull request, verify your device against every existing
manifest entry:

1. Confirm your resistor ID does not appear anywhere in the manifest
2. For each of your I2C addresses, confirm no device that could be
   connected simultaneously uses the same address
3. Document your collision check in your pull request description

## Manifest Entry Format

Add your device to `config/SmartBus_Manifest.json` under
`smartbus.devices` using your resistor ID (as a string) as the key:

```json
"22000": {
    "name": "smartmag_v1",
    "role": "mag",
    "connection_point": "magwell",
    "i2c_addresses": [49],
    "provides": ["ammo_level"],
    "consumes": [],
    "routes": {
        "to_firing_system": ["ammo_level"],
        "to_display": ["ammo_level"],
        "to_device": []
    }
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Internal device name, lowercase with underscores |
| `role` | string | Yes | Driver name to load. Must match a file in `SmartBus/drivers/` |
| `connection_point` | string | Yes | Physical connection point. Must be one of: `barrel`, `upper`, `lower`, `magwell`, `handle`, `any` |
| `i2c_addresses` | array | Yes | List of I2C addresses this device may use. Empty array `[]` for power-only devices |
| `provides` | array | Yes | List of data keys this device sends to TAFY. Keys must be defined in `config/SmartBus_Key_Catalog.json` |
| `consumes` | array | Yes | List of data keys this device receives from TAFY. Keys must be defined in `config/SmartBus_Key_Catalog.json` |
| `routes` | object | Yes | Defines where provided data is routed |

### Routes Object

The `routes` object defines how data flows between the device and TAFY:

| Key | Description |
|-----|-------------|
| `to_firing_system` | Data keys routed to the fire control loop |
| `to_display` | Data keys routed to the display driver via STATE |
| `to_volume` | Data keys routed to the volume subsystem (reserved for future use) |
| `to_device` | Data keys sent from TAFY back to the device |

All keys used in `routes` must also appear in `provides` or `consumes` as
appropriate. Keys used in routing must be defined in
`config/SmartBus_Key_Catalog.json`. Do not invent new keys — open a GitHub
issue to propose additions to the catalog first.

## Driver Implementation

SmartBus drivers live in `SmartBus/drivers/`. The filename must match the
`role` field in your manifest entry exactly, with a `.py` extension.

All drivers must implement the following ABI. Use `SmartBus/drivers/dummy_sb.py`
as your starting point.

### Required Methods

#### `__init__(self, addresses, config, locks, comms, id_line)`

Called once when the device is first detected. Initialize your hardware here.

| Parameter | Type | Description |
|-----------|------|-------------|
| `addresses` | list | I2C addresses from the manifest entry |
| `config` | Config | TAFY config object |
| `locks` | dict | TAFY lock dictionary |
| `comms` | I2C | SmartBus I2C bus object |
| `id_line` | dict | SmartBus ID line ADC objects |

#### `run(self, config, locks, data_in)`

Called once per background loop tick. Perform your device's work here.
Must return a dict of data to pass back to TAFY, or `None` if no data.

**You must acquire `locks["i2c_sb"]` before accessing the SmartBus I2C bus.**
The bus is shared and failure to lock it will cause data corruption.

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | Config | TAFY config object |
| `locks` | dict | TAFY lock dictionary |
| `data_in` | any | Data sent from TAFY to this device, or `None` |

Returns: `dict` or `None`

#### `get_address(self, locks)`

Called once after `init()`. Return the I2C address currently in use by
your device so SmartBus can monitor for disconnection. Return `None` for
power-only devices.

| Parameter | Type | Description |
|-----------|------|-------------|
| `locks` | dict | TAFY lock dictionary |

Returns: `int`, `list`, or `None`

### Module-level `init()` Function

Your driver module must also expose a module-level `init()` function that
instantiates and returns your driver class:

```python
def init(addresses, config, locks, comms, id_line):
    """Setup driver and return instance"""
    return MyDriver(addresses, config, locks, comms, id_line)
```

### Example Driver Structure

```python
class MySmartBusDevice():
    def __init__(self, addresses, config, locks, comms, id_line):
        self.COMMS = comms
        self.ADDRESS = addresses[0]

    def run(self, config, locks, data_in):
        with locks["i2c_sb"]:
            # read from your device
            pass
        return {"my_data": value}

    def get_address(self, locks):
        return self.ADDRESS


def init(addresses, config, locks, comms, id_line):
    return MySmartBusDevice(addresses, config, locks, comms, id_line)
```

## Power-Only Devices

Power-only devices draw power from SmartBus but do not communicate over I2C.
All power-only devices share a single manifest entry with resistor ID 4.7kΩ —
TAFY does not distinguish between different power-only device types, only that
something is drawing power.

No custom driver is needed. TAFY automatically loads the dummy driver for all
power-only devices. You do not need to submit a driver or a manifest entry —
both already exist.

To build a power-only SmartBus device, you simply need:
- A SmartBus connector wired correctly
- A 4.7kΩ resistor (5% tolerance or better) between the ID/Sense pin and GND
- Whatever electronics your device needs, powered from the VCC and GND pins

That's it. No pull request required for a power-only device.

## Submitting Your Device

Pull requests for new SmartBus devices must include:

1. Manifest entry in `config/SmartBus_Manifest.json`
2. Driver in `SmartBus/drivers/`
3. Entry in `SmartBus/DEVICES.md`
4. Pull request description including:
   - Device purpose and connection point
   - Resistor ID chosen and confirmation it is unused
   - I2C addresses chosen and collision check results
   - Any special wiring or configuration requirements

Hardware design files and device-side firmware are **strongly encouraged**
to be submitted and open-sourced alongside the driver. Open hardware
submissions allow the TAFY team to validate the device directly.

If hardware files are not submitted, you **must** ship a physical sample
device to a TAFY developer for testing and validation before the pull
request can be accepted. Closed-source hardware is permitted but this
requirement cannot be waived.

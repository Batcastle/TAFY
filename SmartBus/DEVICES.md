# SmartBus Devices

This is the catalog of all currently supported SmartBus devices. For
information on designing and submitting a new device, see
[DEVICE_DEVELOPMENT.md](DEVICE_DEVELOPMENT.md).

## Power-Only Devices

Power-only devices draw power from SmartBus but do not communicate with TAFY.
All power-only devices use the 4.7kΩ resistor ID and the dummy driver. No
custom driver or manifest entry is required to build a power-only device.

Examples of power-only devices include lights, lasers, and any accessory that
only needs power and does not need to send or receive data.

See the Power-Only Devices section in
[DEVICE_DEVELOPMENT.md](DEVICE_DEVELOPMENT.md) for build instructions.

---

## Smart Devices

### SmartDock

| Property | Value |
|----------|-------|
| Resistor ID | 1MΩ |
| I2C Address | 0x1A / 26 (fully reserved) |
| connection_point | handle |
| Role | `SmartDock` |
| Status | Planned |

| Provides | Consumes |
|----------|----------|
| `charging` | `battery_charge` |
| `update` | `battery_charging_status` |

The SmartDock is a charging and update dock for TAFY blasters. It provides
USB-C charging and allows firmware updates to be pushed to the blaster over
SmartBus without removing the Pico or connecting a USB cable directly to the
blaster.

> **Note:** The `charging` key is a capability indicator only. When the
> SmartDock is connected, it asserts that the blaster should be charging.
> TAFY does not act on this value directly — charging state is monitored
> internally by the battery driver regardless of SmartBus connection.

---

### SmartMag Gen 1

| Property | Value |
|----------|-------|
| Resistor ID | 22kΩ |
| I2C Address | 0x31 / 49 |
| connection_point | magwell |
| Role | `mag` |
| Status | Planned |

| Provides | Consumes |
|----------|----------|
| `ammo_level` | Nothing |

A smart magazine that reports remaining dart count to TAFY over SmartBus.
TAFY uses this information to update the capacity display and can trigger a
magazine empty alert when rounds run out.

---

### SmartSpine Gen 1

| Property | Value |
|----------|-------|
| Resistor ID | 47kΩ |
| I2C Address | 0x30 / 48 |
| connection_point | magwell |
| Role | `mag_spine` |
| Status | Planned |

| Provides | Consumes |
|----------|----------|
| `ammo_level` | Nothing |

A smart spine that connects to the magazine from behind and reports dart count
similarly to the SmartMag. Intended for magazines that cannot be modified to
include SmartMag electronics directly.

If both a SmartMag and SmartSpine are connected simultaneously, SmartMag
takes priority per the manifest defaults.

---

### Chronometer Gen 1

| Property | Value |
|----------|-------|
| Resistor ID | 33kΩ |
| I2C Address | 0x50 / 80 |
| connection_point | barrel |
| Role | `barrel` |
| Status | Planned |

| Provides | Consumes |
|----------|----------|
| `fps` | `fire_mode` |

A barrel-mounted chronograph that measures dart velocity and reports it to
TAFY over SmartBus. TAFY can display live FPS readings on the blaster display.

---

## Adding a Device

To add a new SmartBus device to this catalog, submit a pull request following
the process defined in [DEVICE_DEVELOPMENT.md](DEVICE_DEVELOPMENT.md). Your
pull request must include an entry in this file.

Use the following template for your entry:

```markdown
### Device Name

| Property | Value |
|----------|-------|
| Resistor ID | XkΩ |
| I2C Address | 0xXX / XX |
| connection_point | connection_point_name |
| Role | `role_name` |
| Status | Planned / In Development / Available |

| Provides | Consumes |
|----------|----------|
| `data_key` | `data_key` |

Brief description of what the device does and how TAFY uses the data it
provides.
```

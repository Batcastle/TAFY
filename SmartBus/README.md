# SmartBus

SmartBus is TAFY's hot-swappable accessory system. It allows external devices
to connect to a TAFY blaster and communicate over I2C, receive power, and be
automatically detected and configured at runtime without rebooting.

## Overview

SmartBus uses a 5-pin magnetic connector (Mill-Max Maxnetic, 4mm pitch) at each
port. Devices are identified automatically when connected using a resistor on the
ID/Sense line — no configuration required from the user.

### Pin Out

| Pin | Function |
|-----|----------|
| 1 | VCC (3.3V, 1A max) |
| 2 | GND |
| 3 | I2C SDA |
| 4 | I2C SCL |
| 5 | ID/Sense |

The ID/Sense line uses a voltage divider to identify the connected device type.
Each device places a resistor of a specific value between the ID/Sense pin and
GND. TAFY reads this resistance and looks it up in the SmartBus manifest to
determine what device is connected and which driver to load.

## Connectors

TAFY blasters have up to 5 SmartBus connectors, each at a specific physical
location on the shell. The connector location determines which devices are
compatible with that port.

| connection_point | Location | Primary Use |
|-----------------|----------|-------------|
| `barrel` | End of barrel | Chronographs, muzzle accessories |
| `upper` | Top of upper receiver | Optics, cameras, rangefinders |
| `lower` | Underside of receiver | Lights, lasers, foregrips with electronics |
| `magwell` | Magazine well area | SmartMag, SmartSpine |
| `handle` | Base of handle | SmartDock, extended battery packs |
| `any` | Any connector | Power-only devices |

Not all blasters will have all five connectors. Smaller blasters like Pandora
may omit some connectors due to space constraints. All connector panels are
modular and user-replaceable. Blank panels are available for ports the user
does not wish to populate.

## Device Detection

When a device is connected, TAFY detects the change in resistance on the
ID/Sense line within milliseconds. It then:

1. Calculates the resistance of the newly connected device
2. Looks up the resistance in the SmartBus manifest within a 15% tolerance window
3. Assigns the device a unique randomly generated session ID
4. Loads the appropriate driver
5. Begins passing data to and from the device each background loop tick

When a device is disconnected, TAFY detects the change in resistance, verifies
the device's I2C address is no longer present on the bus (for smart devices),
and unloads the driver automatically.

## Data Routing

Each device declares what data it provides to TAFY and what data it consumes
from TAFY via the `provides`, `consumes`, and `routes` fields in the manifest.
This allows TAFY to automatically route data between devices, the firing system,
and the display without requiring custom routing code per device.

Valid route destinations are:

| Destination | Description |
|-------------|-------------|
| `to_display` | Data routed to the display driver via STATE |
| `to_firing_system` | Data routed to the fire control loop |
| `to_volume` | Data routed to the volume subsystem (reserved for future use) |
| `to_device` | Data sent from TAFY back to the device |

## Device Registry

The following resistor IDs and I2C addresses are currently defined. New devices
must not reuse these values unless explicitly permitted by the collision rules
defined in [DEVICE_DEVELOPMENT.md](DEVICE_DEVELOPMENT.md).

### Resistor ID Registry

| Resistance | Device | connection_point |
|------------|--------|-----------------|
| 4.7kΩ | Power-only devices | any |
| 22kΩ | SmartMag Gen 1 | magwell |
| 33kΩ | Chronometer Gen 1 | barrel |
| 47kΩ | SmartSpine Gen 1 | magwell |
| 1MΩ | SmartDock | handle |

### A Note on Resistor Tolerance

The 15% tolerance window used for device detection is **not** a specification
for the ID resistor itself. It exists to account for:

- ADC measurement inaccuracy
- Tolerance of TAFY's onboard voltage divider resistor
- Wire and connection resistance

ID resistors on SmartBus devices **must** have 5% tolerance or better.
1% tolerance resistors are preferred where possible. Using a resistor with
greater than 5% tolerance risks falling outside the detection window or
causing false matches with adjacent device IDs.

### I2C Address Registry

| Address | Device | Notes |
|---------|--------|-------|
| 0x1A (26) | SmartDock | Fully reserved, no sharing permitted under any circumstances |

## Further Reading

- [DEVICE_DEVELOPMENT.md](DEVICE_DEVELOPMENT.md) — How to design and submit a new SmartBus device
- [DEVICES.md](DEVICES.md) — Catalog of all supported SmartBus devices

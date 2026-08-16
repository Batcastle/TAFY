# Validation Progress
This document is to help others track validation progress for software and hardware related to TAFY as we progress through our Alpha (v0.0-9.x), Beta (v1.0-9.x) releases, up to a stable release.

## Legend
| Status | Meaning |
|--------|---------|
| Fully Validated | Tested and Known working. |
| Partially Validated | Tested, but with relevent components swapped for cheaper stand-ins. System is known behaving correctly logically but may have mechanical issues. |
| Validating | Code that has been written and loaded onto hardware, or hardware designed, fabricated, and assembled, and is currently undergoing validation |
| Written | Code is written, or hardware designed, but has yet to be loaded onto hardware, fabricated/assembled, and/or validated. |
| In progress | Code or hardware that is actively being developed. May be getting validated simultaneously. |
| Architected | Code or hardware has not yet been fully implemented, but it's methods of operation are understood. |
| Not yet started | Future work, has yet to be touched. |

## Core Functionality
| Component | Status | Notes |
|-----------|--------|-------|
| Boot up | Fully Validated | |
| Tone/Tune playback | Fully Validated | Due to Piezo buzzer limitatons, frequency response is limited. However, piezos are near indestructable. This is a sacrifice we are willing to make. |
| Dynamic Driver System | Fully Validated | Dynamic Diver System is sourced from a seperate application @Batcastle developed and has adapted for MicroPython. System has been validated against CPython versions 3.8 and up and MicroPython versions 1.26.1 and up. |
| Config system | Fully Validated | |
| Background process spawning | Fully Validated | Background thread was profiled, prior to SmartBus implementation, to loop once every 3ms or so, even with I2C writes actively going to display.|
| Display Driver ABI | Fully Validated | 2 known working full display drivers, plus a dummy driver, all follow the ABI. |
| Fire Mechanism Driver ABI | Partially Validated | Tested against LEDs in absence of motor controlboard, motors, and solenoids. |
| Fire Mode State Machine | Fully Validated | |
| Fire Control | Partially Validated | KNOWN BUG: Fire trigger will fire solenoids even if rev trigger is not pressed on flywheel blasters. This can cause jams. |
| Updates over USB | Fully Validated | Tested every deployment |

## Feature Set
| Component | Status | Notes |
|-----------|--------|-------|
| SSD1309 Driver | Fully Validated | Recommened display to use with TAFY thanks to better screen real estate and better power efficency.|
| LCD1602 Driver | Fully Validated | Cannot push writes too often as this is a character device and cannot handle frequent refreshes. As such, this display only refreshes when necessary. |
| SSD1306 | Written | Driver is assumed working due to similarities with SSD1309. Do not have this display in hand yet to test. |
| Volume Knob (SEN0502) | Partially Validated | Working at a basic level. Driver will likely see a minor rewrite to be non-blocking and also support double and triple press. Volume and Mute are working though. |
| Battery State Tracking | Partially Validated | Code was tested using noise from ADC. |
| Opportunistic Sleep | Designed | This is a late-game feature and has yet to be implemented. |
| Flywheel + Mechanical Pusher Fire Mechanism Driver | Written | Waiting on Validated Motor Controlboard |
| Flywheel + Solenoid Pusher Fire Mechanism Driver | Written | Waiting on Validated Motor Controlboard |
| Flywheel + Sector Gear Pusher Fire Mechanism Driver | In Progress | |
| AEB Fire Mechanism Driver | Not Yet Started | Must develop custom gearbox first. |
| CO2/HPA Fire Mechanism Driver | Not Yet Started | Do not have any solenoid valves. |


## SmartBus
| Component | Status | Notes |
|-----------|--------|-------|
| Device Recognition | Partially Validated | No sockets in electrical system yet, but recognition is successful. |
| Device Registration | Partially Validated | Only tested with dummy driver so far. |
| Device Deregistration | Partially validated | Need to monitor device registry for this. |
| Driver Loading | Partially Validated | Dummy Driver loads. |
| Data routing | In Progress | Currently Architecting and writing code. |
| Updates over SmartBus | Architected | Will be difficult to implement without a SmartDock in development |
| Device Hotswap | Validating | Testing validated two hot swaps on and at least one hot swap off, but no futher connections could be validated. Investigating. |

## Electrical
| Component | Status | Notes |
|-----------|--------|-------|
| Mainboard | Validating | Third hardware revision at fabrication. |
| Motor Controlboard | Validating | First revision fabricated and assembled. Testing showed major wiring issues. |
| Motor Controlboard - half-H-Bridge variant | Written | Fabricating... |
| Controlboard (3-way splitter) | Partially Validated | Intital revision fabricated and assembled. Validated basic function, noticed multiple issues. Second revision in fabrication... |
| Power Supply | Written | Fabricating... |
| Battery Holder | Written | Fabricating... |

## Mechanical
| Component | Status | Notes |
|-----------|--------|-------|
| Shells | Architected | Currently looking for a CAD designer/engineer. Attempted using AI to design, failed miserably. |
| AEB Gearbox | Not Started | Not entirely sure how to start this yet. |

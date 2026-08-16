# PCB Design Requirements

All PCBs made for TAFY should embody the below design philosphies:

## Rules
### 1: Safety First

Any board which handles high voltage should have multiple protection systems in place to prevent issues: overcurrent, over temp, over voltage, short circuit, etc. This is both to protect components and protect the user.

Any board which handles a fire mechanism should only work if:
 - It receives a signal that the SAFETY is off
 - It receives valid direction control signals for it's motors (if applicable)
 - It receives a valid PWM signal controling any sort of affector system (motors, solenoids, etc), to maintain speed control
If any one of these is false, a board should refuse to fire.

Finally, if a board fails, steps should be taken to ensure the user is protected.

### 2: Accessability

All boards should be easily assemblable. Any soldering should be on through-hole components. Surface mount componets are strictly banned, except in cases where they may be placed in an adapter. All wires connecting componets must utilize either some form of port/socket, or else use a screw terminal. The exception is for individual, passive components: switches, buttons, piezo buzzers/speakers, etc.

### 3: Durability

Boards will usually be placed inside blasters. These blasters will likely be used outdoors, in high activity environments, potentially by children. A board should be able to take such abuse. As such, surface-mount components are strictly banned, and only through-hole components may be used, except in cases where surface mount components may be placed in an adapter.

## Summary

There are no strict size or complexity requirements. However, keep in mind, these devices may be hand-soldered, and must fit in their respective blasters. You may have room in a Hydra, Ares, or Hades. But a Pandora is VERY space constrained. They are also being placed in a device that is traditionally seen and used as a toy, so simplicity is supreme.

When in doubt:
- **S**implicity is Supreme
- **A**ccessibility is Awesome
- **D**uribility Dominates
- **S**afety Saves Lives


# Assembly Instructions
This file provides Instructions on how to build a TAFY system, from components and boards, to shells and final testing. Prices rounded up to nearest dollar account for inflation, taxes, tariffs, and price fluctuations. Many of these parts or similar replacements may be able to be found for cheaper.

## PARTS LIST
Please note for Amazon orders, some parts come in multiples. You may have extras come when you order. Digikey will not send extras. If you wish for extra of a component, then you must budget for that accordingly when Digikey is involved.

| Component | Count | Source | Projected Price |
|-----------|-------|--------|-----------------|
| 2-pin screw terminals | 25 | [DigiKey](https://www.digikey.com/en/products/detail/altech-corporation/34-102/8547113) | $12 USD |
| 3-pin screw terminals | 5 | [Digikey](https://www.digikey.com/en/products/detail/altech-corporation/30-203/9321638) | $4 USD |
| 2N2222 Transistors | 4 | [Digikey](https://www.digikey.com/en/products/detail/diotec-semiconductor/2N2222A/13164037) | $1 USD|
| 2N3906 Transistors | 7 | [Digikey](https://www.digikey.com/en/products/detail/comchip-technology/2N3906-G/9477908) | $2 USD |
| IRF9540N MOSFETS | 4 | [Digikey](https://www.digikey.com/en/products/detail/infineon-technologies/IRF9540NPBF/812088) | $11 USD |
| IRLB3813 MOSFETS | 5 | [Digikey](https://www.digikey.com/en/products/detail/infineon-technologies/IRLB3813PBF/2118485) | $15 USD |
| IN4007 Diodes | 11 | [ Digikey](https://www.digikey.com/en/products/detail/diodes-incorporated/1N4007G-T/111822) | $2 USD |
| RioRand LM2596 Buck Converters | 3 | [Amazon](https://www.amazon.com/RioRand-LM2596-Converter-1-23V-30V-5Pcs-LM2596/dp/B008BHB4L8) | $10 USD |
| LD1117V33 Voltage Regulator | 1 | [Digikey](https://www.digikey.com/en/products/detail/stmicroelectronics/LD1117V33/586012) | $2 USD |
| 10K Ohm Resistors | 6 | [Digikey](https://www.digikey.com/en/products/detail/yageo/MFR-25FRF52-10K/14626) | $1 USD |
| 47K Ohm Resistors | 3 | [Digikey](https://www.digikey.com/en/products/detail/stackpole-electronics-inc/CF14JT47K0/1741444) | $1 USD |
| 100 Ohm Resistors | 1 | [Digikey](https://www.digikey.com/en/products/detail/yageo/CFR-25JR-52-100R/11950) | $1 USD |
| 300 Ohm Resistors | 7 | [Digikey](https://www.digikey.com/en/products/detail/koa-speer-electronics-inc/CF1-2CT52R301J/13537179) | $1 USD |
| 9.1K Ohm Resistors | 1 | [Digikey](https://www.digikey.com/en/products/detail/yageo/MFP-25BRD52-9K1/2058835?s=N4IgjCBcoMxaBjKAzAhgGwM4FMA0IB7KAbRAHYYIBdfABwBcoQBlegJwEsA7AcxAF98AJgAMADgCs8EEkhoseQiRABOAHRgABAGsA8gAsAtphA0QDJgFUuHeruQBZbKkwBXNtgH4AtEOmz2V0UiSFIpfBVTfkEQP1CQD0wOTHoCNhMqfiA) | $1 USD |
| 100nF capacitors | 15 | [Digikey](https://www.digikey.com/en/products/detail/vishay-beyschlag-draloric-bc-components/K104K15X7RF5TL2/286538) | $3 USD |
| 1A PPTCs | 3 | [Digikey](https://www.digikey.com/en/products/detail/littelfuse-inc/RXEF050/5015994) | $2 USD |
| 15-20A PPTC | 1 | [Digikey](https://www.digikey.com/en/products/detail/littelfuse-inc/RUEF800/5016007) | $2 USD |
| 40-pin ZIF Socket | 1 | [Digikey](https://www.digikey.com/en/products/detail/mikroelektronika/MIKROE-425/20841119) | $4 USD |
| Piezo Buzzer | 1 | [Digikey](https://www.digikey.com/en/products/detail/soberton-inc/PB-2211/1245324) | $4 USD | 
| Display (SSD1309 recommended) | 1 | [Amazon](https://www.amazon.com/HiLetgo-SSD1309-128x64-Display-Optional/dp/B0CFF19Z5G?content-id=amzn1.sym.0b2dff59-ea0a-4b9b-9517-29966f3a3547&th=1) | $17 USD |
| 18650 Battery Holder | 1 | [Amazon](https://www.amazon.com/dp/B07TRPV1ZJ) | $10 USD |
| SP3T Switch | 1 | [Digikey](https://www.digikey.com/en/products/detail/c-k/OS103011MS8QP1/1981414) | $1 USD |
| SPST Switchs | 2 | [Digikey](https://www.digikey.com/en/products/detail/c-k/L101011MS02Q/484142) | $8 USD |
| Limit Switchs | 2 | [Digikey](https://www.digikey.com/en/products/detail/e-switch/MS0850506F020V2A/3777960) | $4 USD |
| Raspberry Pi Pico 2 | 1 | [Amazon](https://www.amazon.com/Pico-Pre-Soldered-Compatible-Microcontroller-Dual-Architecture/dp/B0DG3QPQCT) | $14 USD |
| 4mm 5-pin magnetic connectors (Required for SmartBus, Optional for basic blaster operation.) | 5 max | [Digikey](https://www.digikey.com/en/products/detail/mill-max-manufacturing-corp/879-20-005-10-011000/22237160) | $0 - $84 USD depending on count purchased |
| 18650 Li-ion batteries | 3 recommended | [Digikey](https://www.digikey.com/en/products/detail/dantona-industries/UL1865-26-1P/13692651) | $21 USD |
| BMS Module (Must support your battery config! For the TAFY recommended system, that is 3S.) | 1 | [Amazon](https://www.amazon.com/Cermant-Balance-Charger-Protection-Charging/dp/B0CZ73S26M/134-2189246-7694062?content-id=amzn1.sym.f5690a4d-f2bb-45d9-9d1b-736fee412437&th=1) | $9 USD |
| USB-C trigger board | 1 | [Amazon](https://www.amazon.com/Seloky-Trigger-Module-Charger-Delivery/dp/B0DPHH5H41?content-id=amzn1.sym.380ebfe6-828b-40c9-b999-35bb4cd14ee6&th=1) | $8 USD |
| SEN0502 Rotary Encoder | 1 | [Digikey](https://www.digikey.com/en/products/detail/dfrobot/SEN0502/16678686) | $10 USD |

Depending on the blaster you wish to build, you may also need 1, 2 or 4 motors, and a solenoid.

### Flywheel blasters
| Component | Count | Source | Projected Price |
|-----------|-------|--------|-----------------|
| FANG ReVAMPed 130 2S Motor | 2 | [OutOfDarts](https://outofdarts.com/products/fang-revamped-130-motor) | $18 USD (Double for 4 motors) | 
| Neutron High ROF Solenoid | 1 | [OutOfDarts](https://outofdarts.com/products/neutron-high-rof-solenoid) | $30 |

### AEB Blasters
This section still under development.


### Tools
The below is a mandatory list. 
 - Soldering Iron (We recommend [the Pinecil](https://pine64.com/product/pinecil-smart-mini-portable-soldering-iron/))
 - Solder (We used 63/37 Rosin core solder during development and it work great.)
 - Flush cutters
 - Screwdriver (We recommend [the LTT Screwdriver](https://www.lttstore.com/products/screwdriver?variant=39666456297575), this is a premium option, but can speed up assembly. In reality, any screwdriver will suffice.)
 
These are optional, but may be helpful:
 - Flux (if you do not use rosin core solder)
 - Multimeter (To check your work) (Strongly recommended)
 - Helping hands or PCB vise
 - Wire strippers/cutters (Strongly recommended, but if you do not have these, scissors work well enough)
 
### Boards
All boards are required for the following blasters:
 - Poseidon
 - Zeus
 - Prometheus
 - Hephaestus
 - Hades
 - Hydra
 - Ares
 
For Pandora, the following boards/parts may be removed and still have a functional blaster:
 - Controlboard
 - SEN0502
 - Display
 - Piezo buzzer
 
A smaller mainboard or motor controlboard may be created down the line to allow a Pandora build to be entirely self-contained.

Boards can be ordered from Aisler starting at roughly $20 for fabrication. It is ideal to place your orders for boards all at once, as this allows you to have boards sent in one shipment, saving on shipping costs.

We recommend Aisler for board fabrication as they allow direct upload of the provided Fritzing files in this repo. JLCPCB or PCBWay both may be cheaper, but will require exporting Fritzing files to GERBER.

Please also keep in mind that minimum boards per batch from Aisler is 3. This means when you order boards, you will get 3 of each.

| Board | File | Price from Aisler (after VAT) |
|-------|------|-------------------|
| Battery Holder | `hardware/PCBs/Battery Holder.fzz` | $30.40 USD |
| Controlboard | `hardware/PCBs/Controlboard.fzz` | $20.78 USD |
| Mainboard | `hardware/PCBs/Mainboard.fzz` | $32.03 USD |
| Motor Controlboard | `hardware/PCBs/Motor Controlboard.fzz` | $40.44 USD |
| Power Supply | `hardware/PCBs/Power Supply.fzz` | $39.44 USD |

### NOTE
Aisler, PCBWay, and JLCPCB all offer assembly services for a fee. This fee usually includes cost of components as well as labor.

While pre-fabricated and assembled boards are not available, it is a goal of the community to make them available for purchase in the future. However, this would require either setting up an online store, on a service such as Etsy, or working with an electronics manufacturer, both of which requires a significant time and financial investment to even consider persuing.

### NOTE THE SECOND
When soldering, especilly with leaded solder, it is imperative to make sure you use a well ventilated area, with ideally some from of fume extraction system.

Lead solder releases fumes containing lead vapor you can easily breath in, and even unleaded solder releases toxic fumes. This is even more present when using rosin core solder. Ventilation is essential.


## ASSEMBLY
### PREP

### Boards

### Shells

### Pre-assembly

### Wiring

### Final Assembly

## TESTING
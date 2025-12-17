import json

DRIVER = None

DISPLAY_TYPE = "7 SEGMENT"

THREAD_OBJ = None

I2C_OBJ = None

INTERNAL_SETTINGS = {}


def init(config: dict, i2c_obj) -> None:
    """Initalize 7 segment display, determine type and load necessary driver"""
    I2C_OBJ = i2c_obj
    results = I2C_OBJ.scan()
    with open("config/7_seg.json", "r") as file:
        INTERNAL_SETTINGS = json.load(file)

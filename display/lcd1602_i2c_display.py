import json
from time import sleep
import _thread

DISPLAY_TYPE = "LCD1602 - I2C"

STATE = {"CAPACITY": 0,
         "MODE":  "SAFE",
         "BATTERY": None,
         "DIRTY": True}

DISPLAY_MODE = 0

LCD_OBJ = None
LCD_CONFIG = None

def init(config, i2c_obj, silent=False, split_thread=True):
    """Initalize 7 segment display, determine type and load necessary driver"""
    global LCD_OBJ, LCD_CONFIG
    I2C_OBJ = i2c_obj
    results = I2C_OBJ.scan()
    addr = None
    with open("config/lcd1602_i2c.json", "r") as file:
        lcd_config = json.load(file)

    LCD_CONFIG = lcd_config

    for each in results:
        if str(each) in lcd_config["supported"]:
            addr = each
            break

    if addr is None:
        raise Exception("Device LCD1602 - I2C not found at any supported address.")

    display = LCD(addr, i2c_obj)
    display.active_high_backlight = lcd_config["backlight_active_high"]
    if not silent:
        display.lcd_display_string("Welcome to TAFY!", line=1, clear=True)
        display.lcd_display_string(config['VERSION'], line=2, clear=False)

    LCD_OBJ = display

    if split_thread:
        return display_main
    return display


def display_main(global_config: dict):
    """This object is the main thread object. It is spawned by the background
       process and directly communicates with the display
    """
    # Sleep for a few seconds to let initalization of the rest of TAFY finish
    global STATE, LCD_OBJ, LCD_CONFIG
    sleep(4)
    LCD_OBJ.lcd_clear()
    if DISPLAY_MODE is None:
        return
    lock = _thread.allocate_lock()
    with lock:
        if STATE["DIRTY"]:
            mode = LCD_CONFIG["display_modes"][DISPLAY_MODE]
            LCD_OBJ.lcd_display_string(f"{mode["1"]}: {STATE[mode["1"]]}", line=1, clear=True)
            LCD_OBJ.lcd_display_string(f"{mode["2"]}: {STATE[mode["2"]]}", line=2, clear=False)
            STATE["DIRTY"] = False


# i2c bus (0 -- original Pi, 1 -- Rev 2 Pi)
I2CBUS = 0

# LCD Address
ADDRESS = 0x27

# import smbus

class i2c_device:
    def __init__(self, addr, i2c_obj):
        self.addr = addr
        self.i2c_bus = i2c_obj
        # self.bus = smbus.SMBus(port)

    # Write a single command
    def write_cmd(self, cmd: bytes):
        if not isinstance(cmd, (bytes, bytearray)):
            raise Exception("cmd must be bytes or bytes array when calling i2c_device.write_cmd()")
        self.i2c_bus.writeto(self.addr, cmd)
        sleep(0.0001)

    # Write a command and argument
    def write_cmd_arg(self, cmd: bytes, data: bytes):
        if not isinstance(cmd, (bytes, bytearray)):
            raise Exception("cmd must be bytes or bytes array when calling i2c_device.write_cmd_arg()")
        if not isinstance(data, (bytes, bytearray)):
            raise Exception("data must be bytes or bytes array when calling i2c_device.write_cmd_arg()")
        self.i2c_bus.writeto(self.addr, cmd + data)
        sleep(0.0001)

    # Write a block of data
    def write_block_data(self, cmd: bytes, data: bytes):
        if not isinstance(cmd, (bytes, bytearray)):
            raise Exception("cmd must be bytes or bytes array when calling i2c_device.write_block_data()")
        if not isinstance(data, (bytes, bytearray)):
            raise Exception("data must be bytes or bytes array when calling i2c_device.write_block_data()")
        self.i2c_bus.writeto(self.addr, cmd + data)

    # Read
    def read_len(self, length: int) -> bytes:
        return self.i2c_bus.readfrom(self.addr, length)


# commands
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# flags for display entry mode
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# flags for display on/off control
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# flags for display/cursor shift
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# flags for function set
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS = 0x00

# flags for backlight control
LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x00

En = 0b00000100 # Enable bit
Rw = 0b00000010 # Read/Write bit
Rs = 0b00000001 # Register select bit

class LCD:
    #initializes objects and lcd
    def __init__(self, addr, i2c_obj):
        self.lcd_device = i2c_device(addr, i2c_obj)

        self.active_high_backlight = True
        self.backlight_mode = True

        self.lcd_write(0x33)
        self.lcd_write(0x32)
        # self.lcd_write(0x03)
        # self.lcd_write(0x02)

        self.lcd_write(LCD_FUNCTIONSET | LCD_2LINE | LCD_5x8DOTS | LCD_4BITMODE)
        self.lcd_write(LCD_DISPLAYCONTROL | LCD_DISPLAYON)
        self.lcd_write(LCD_ENTRYMODESET | LCD_ENTRYLEFT)
        self.lcd_write(LCD_CLEARDISPLAY)

        sleep(0.2)

    def _b(self, v: int) -> bytes:
        return bytes([v & 0xFF])

    # clocks EN to latch command
    def lcd_strobe(self, data):
        self.lcd_device.write_cmd(self._b((data | En | self._get_backlight_bit())))
        sleep(.0005)
        self.lcd_device.write_cmd(self._b(((data & ~En) | self._get_backlight_bit())))
        sleep(.0001)

    def lcd_write_four_bits(self, data):
        self.lcd_device.write_cmd(self._b((data | self._get_backlight_bit())))
        self.lcd_strobe(data)

    # write a command to lcd
    def lcd_write(self, cmd, mode=0):
        self.lcd_write_four_bits(mode | (cmd & 0xF0))
        self.lcd_write_four_bits(mode | ((cmd << 4) & 0xF0))

    # write a character to lcd (or character rom) 0x09: backlight | RS=DR<
    # works!
    def lcd_write_char(self, charvalue, mode=1):
        self.lcd_write_four_bits(mode | (charvalue & 0xF0))
        self.lcd_write_four_bits(mode | ((charvalue << 4) & 0xF0))

    # put string function with optional char positioning
    def lcd_display_string(self, string, line=1, pos=0, clear=True):
        if clear:
            self.lcd_clear()
        if line == 1:
            pos_new = pos
        elif line == 2:
            pos_new = 0x40 + pos
        elif line == 3:
            pos_new = 0x14 + pos
        elif line == 4:
            pos_new = 0x54 + pos

        self.lcd_write(0x80 + pos_new)

        for char in string:
            self.lcd_write(ord(char), Rs)

    def display_string(self, string, line=1, pos=0, clear=True):
        self.lcd_display_string(string, line=line, pos=pos, clear=clear)

    # clear lcd and set to home
    def lcd_clear(self):
        self.lcd_write(LCD_CLEARDISPLAY)
        self.lcd_write(LCD_RETURNHOME)

    # define backlight on/off (lcd.backlight(1); off= lcd.backlight(0)
    def backlight(self, state): # for state, 1 = on, 0 = off
        self.backlight_mode = (state == 1)
        self.lcd_device.write_cmd(self._b(self._get_backlight_bit()))

    def _get_backlight_bit(self) -> hex:
        if self.active_high_backlight:
            if self.backlight_mode:
                return LCD_BACKLIGHT
            return LCD_NOBACKLIGHT
        if self.backlight_mode:
            return LCD_NOBACKLIGHT
        return LCD_BACKLIGHT

    # add custom characters (0 - 7)
    def lcd_load_custom_chars(self, fontdata):
        self.lcd_write(0x40)
        for char in fontdata:
            for line in char:
                self.lcd_write_char(line)

# -*- coding: utf-8 -*-
#
#  dummy_sb.py
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
#

class SmartBusDriver():
    """Define a basic SmartBus Driver. This will behave as both a stub for others to build to from, and as a dummy driver"""
    def __init__(self, addresses, config, locks, comms, id_line):
        """Initialize driver. We'll simply make COMMS and ID_LINE class properties so we can access them in other methods."""
        self.COMMS = comms
        self.ID_LINE = id_line
        self.ADDRESS = addresses


    def run(self, config, locks):
        """This is your chance for your driver to actually do something. This gets called once per loop. Argument one is your access to your config,
        Argument Two is access to your locks. YOU MUST LOCK "i2c_sb" BEFORE ACCESSING THE SMARTBUS I2C BUS AS IF THIS GETS MORE MULTITHREADED, YOUR DRIVER MAY HAVE TO WAIT IT'S TURN.
        """
        pass

    def get_address(self, locks):
        """Any intelligent SmartBus device will live on the SmartBus I2C bus. This means it has an I2C address. If you are making a driver for a smart device, you must return the address currently in use so SmartBus can check if your device is connected occasionally.

        If your device is dumb, just return None.

        Locks are provided in case you need the access the bus for some reason, but you really shouldn't need to.
        """
        return None


def init(addresses, config, locks, comms, id_line):
    """Setup SmartBusDriver and return a class instance for use"""
    sbd = SmartBusDriver(addresses, config, locks, comms, id_line)
    return sbd




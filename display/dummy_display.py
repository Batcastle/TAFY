# -*- coding: utf-8 -*-
#
#  dummy_display.py
#
#  Copyright 2025 Thomas Castleman <batcastle@draugeros.org>
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
"""
This file provides a dummy driver, in case of blasters with no display output

It also serves as a template to start from to write new display drivers
"""

# Always make sure to set a display type string. This is useful for debugging.
DISPLAY_TYPE = "DUMMY"

# This variable stores the thread object, in case the main thread needs to interact with it in some weird way
THREAD_OBJ = None


def init(config):
    """
    Under normal circumstances, this function would serve to initalize any displays, be it over UART, I2C, GPIO, or something else.

    Here, since there is no display to initalize, we do nothing. Config must still be passed to adhear to the display driver ABI.

    It should initalize a second, background process that runs and pushes updates to the display for the main process. There should
    also be a variable shared between the two processes, behind a lock, that is used to send updates to the display. The background process
    should not send data back to the main thread as it will be ignored.

    This function should also avoid actually returning anything, and instead keep it's work internal.
    """
    print("initalizeing dummy display!")
    pass


def write(data):
    """
    Under normal circumstances, this function would serve to push updates to any displays.

    It would, ideally, use a lock to update a variable stored between processes, which allows the background process to receive
    data it would use to update the actual display.
    """
    pass

# -*- coding: utf-8 -*-
#
#  global_base.py
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
"""
This file defines the base that all display drivers need, at minimum
"""
import _thread


class State:
    """Configuration Data Class"""
    def __init__(self) -> None:
        """Initalize data class"""
        self.locks = {"mem": _thread.allocate_lock()}
        self.STATE = {
            "CAPACITY": 0,
            "MODE":     "SAFE",
            "BATTERY":  None,
            "CHARGING": False,
            "UPDATING": False,
            "DIRTY":    True,
            "DISPLAY_MODE": 0
        }
        self.DISPLAY_TYPE = None

    def get(self, key: str):
        """Get a specific key from a STATE, Locking"""
        with self.acquire_lock():
            return self._get(key)

    def _get(self, key: str):
        """Get a specific key from a STATE, NOT locking"""
        if key in self.STATE:
            # Everything in STATE is a primitive, so we can keep this quick
            if isinstance(self.STATE[key], int):
                return int(self.STATE[key])
            elif isinstance(self.STATE[key], float):
                return float(self.STATE[key])
            elif isinstance(self.STATE[key], bool):
                return bool(self.STATE[key])
            elif isinstance(self.STATE[key], str):
                return str(self.STATE[key])
            # We DO NOT handle returning None because if we do not return anything, it returns None for us

    def set(self, key: str, value):
        """Set a new value for a given key in a given config file, Locking"""
        with self.acquire_lock():
            self._set(key, value)

    def _set(self, key: str, value):
        """Set a new value for a given key in a given config file, NOT Locking"""
        if key not in self.STATE:
            raise NameError(f"Key: `{key}' not understood for STATE.")
        self.STATE[key] = value

    def acquire_lock(self):
        """Acquire exclusive lock for bulk operations"""
        return self.locks["mem"]


STATE = State()

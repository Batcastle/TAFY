# -*- coding: utf-8 -*-
#
#  __init__.py
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
"""
This module provides a unifed interface for all configuration interactions in a thread-safe manner
"""
import os
import json
import _thread


class Config:
    """Configuration Data Class"""
    def __init__(self, version: str) -> None:
        """Initalize data class"""
        self.locks = {"mem": _thread.allocate_lock()}
        self.config = {}
        for each in os.listdir("config"):
            if each[-5:] == ".json":
                self.locks[each[:-5]] = _thread.allocate_lock()
                self.load(each[:-5])
        self.VERSION = version

    def load(self, name: str, overwrite=False) -> None:
        """Load configuration of a specific file from storage"""
        if name not in self.locks:
            raise NameError(f"No config file with name: `{name}.json' is known.")
        if name in self.config and not overwrite:
            raise RuntimeError(f"Cannot overwrite copy of {name} in memory without overwrite flag.")
        with self.locks[name]:
            with self.locks["mem"]:
                with open(f"config/{name}.json", "r") as file:
                    self.config[name] = json.load(file)

    def get_section(self, name: str) -> dict:
        """Get contents of a specifc config file"""
        if (name in self.config) and (name in self.locks):
            output = None
            with self.locks["mem"]:
                output = dict(self.config[name])
            return output
        raise NameError(f"Name: `{name}' not understood.")

    def get(self, name: str, key: str):
        """Get a specific key from a specific config file"""
        section = self.get_section(name)
        return section[key]

    def set(self, name: str, key: str, value):
        """Set a new value for a given key in a given config file"""
        if (name not in self.config) or (name not in self.locks):
            raise NameError(f"Name: `{name}' not understood.")
        with self.locks["mem"]:
            if key not in self.config[name]:
                raise NameError(f"Key: `{key}' not understood for Name `{name}'.")
            self.config[name][key] = value

    def dump(self, name: str):
        """Dump settings to disk"""
        if (name not in self.config) or (name not in self.locks):
            raise NameError(f"Name: `{name}' not understood.")
        with self.locks[name]:
            with self.locks["mem"]:
                # If Indention control ever comes to MicroPython,
                # we'll use it to make sure settings are more human-readable
                with open(f"config/{name}.json", "w+") as file:
                    json.dump(self.config[name], file)

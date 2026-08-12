#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  deploy.py
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
TAFY MicroPython deploy script.

Requirements:
    - Python 3
    - pyserial (package: python3-serial on Ubuntu)

Usage:
    ./deploy.py [-p /dev/ttyACM0] [-b 115200] [-m manifest.list] [-o] [-r]

Features:
    - Reads manifest.list for files/directories/globs to deploy
    - Supports entries like "display/*" and "fire_mech/*"
    - Recursively uploads directories
    - Talks to MicroPython over raw REPL
    - Skips files whose content hasn't changed since the last successful
      deploy, tracked via a local ".tafy_deploy_cache.json" next to the
      manifest. No need to prompt or guess — if the hash matches, it's
      identical to what's already on the device.
    - Only checks/creates each remote directory once per run, rather than
      once per file in that directory
    - -o / --overwrite: ignore the cache and force a full re-upload (use
      this after reflashing MicroPython, since the cache can't know the
      device's filesystem was wiped)
    - -r / --run: soft-reset the board after upload to run the code
"""

import argparse
import base64
import hashlib
import json
import os
import sys
import time
import fnmatch
import serial

CTRL_A = b'\x01'  # raw REPL
CTRL_B = b'\x02'  # normal REPL
CTRL_C = b'\x03'  # interrupt
CTRL_D = b'\x04'  # end of script / soft reboot

CACHE_FILENAME = ".tafy_deploy_cache.json"


class MicroPythonDevice:
    def __init__(self, port, baudrate=115200, timeout=1.0):
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        time.sleep(0.2)

    def close(self):
        try:
            self.ser.close()
        except Exception:
            pass

    def _read_all(self):
        """Read whatever is available without blocking too long."""
        time.sleep(0.05)
        out = b""
        while True:
            chunk = self.ser.read(1024)
            if not chunk:
                break
            out += chunk
            if len(chunk) < 1024:
                break
        return out

    def enter_raw_repl(self):
        """Enter raw REPL mode."""
        # Interrupt any running program
        self.ser.write(CTRL_C)
        self.ser.write(CTRL_C)
        self.ser.flush()
        time.sleep(0.2)
        self._read_all()

        # Enter raw REPL
        self.ser.write(CTRL_A)
        self.ser.flush()

        # Wait for 'raw REPL;' banner and '>' prompt (best effort)
        buf = b""
        start = time.time()
        while True:
            chunk = self.ser.read(128)
            if chunk:
                buf += chunk
                if b"raw REPL;" in buf and buf.rstrip().endswith(b">"):
                    break
            if time.time() - start > 3:
                break

    def exit_raw_repl(self):
        """Exit raw REPL back to normal REPL."""
        self.ser.write(CTRL_B)
        self.ser.flush()
        self._read_all()

    def exec_raw(self, code, print_output=False):
        """
        Execute Python code in raw REPL.
        `code` is a str or bytes.
        Returns (stdout, stderr) as bytes (best-effort).
        """
        if isinstance(code, str):
            code = code.encode("utf-8")

        # Clear any pending input
        self._read_all()

        # Send code then Ctrl-D
        self.ser.write(code)
        self.ser.write(CTRL_D)
        self.ser.flush()

        # After Ctrl-D, raw REPL sends:
        #   stdout + \x04 + stderr + \x04
        data = b""
        start = time.time()
        seen_eofs = 0
        while seen_eofs < 2 and (time.time() - start) < 5:
            chunk = self.ser.read(1024)
            if not chunk:
                continue
            data += chunk
            seen_eofs += chunk.count(b"\x04")

        parts = data.split(b"\x04")
        stdout = parts[1] if len(parts) > 1 else b""
        stderr = parts[2] if len(parts) > 2 else b""

        if print_output:
            if stdout:
                sys.stdout.buffer.write(stdout)
            if stderr:
                sys.stderr.buffer.write(stderr)

        return stdout, stderr

    def file_exists(self, remote_path):
        """Return True if remote file exists, False otherwise."""
        path_repr = repr(remote_path)
        code = (
            "import os, sys\n"
            "try:\n"
            f"    _ = os.stat({path_repr})\n"
            "    sys.stdout.write('1')\n"
            "except OSError:\n"
            "    sys.stdout.write('0')\n"
        )
        stdout, _ = self.exec_raw(code)
        if b"1" in stdout:
            return True

    def start_update_mode(self):
        """Put in 'update mode'"""
        self.ser.write(CTRL_C)
        self.ser.write(CTRL_C)
        code = (
            "try:\n"
            "    import main\n"
            "    main.update()\n"
            "except:\n"
            "    from machine import Pin, Timer\n"
            "    led = Pin('LED', Pin.OUT)\n"
            "    tim = Timer()\n"
            "    def tick(timer):\n"
            "        global led\n"
            "        led.toggle()\n"
            "    tim.init(freq=10, mode=Timer.PERIODIC, callback=tick)\n"
        )
        self.exec_raw(code)

    def update_complete(self):
        self.ser.write(CTRL_C)
        self.ser.write(CTRL_C)
        code = (
            "import main\n"
            "main.update(completed=True)\n"
        )
        self.exec_raw(code)

    def make_dirs(self, remote_dir):
        """Recursively create directories on the device (like mkdir -p)."""
        if not remote_dir:
            return
        path_repr = repr(remote_dir)
        code = (
            "import os\n"
            f"path = {path_repr}\n"
            "parts = path.split('/')\n"
            "cur = ''\n"
            "for p in parts:\n"
            "    if not p:\n"
            "        continue\n"
            "    cur = (cur + '/' + p) if cur else p\n"
            "    try:\n"
            "        os.mkdir(cur)\n"
            "    except OSError:\n"
            "        pass\n"
        )
        self.exec_raw(code)

    def write_file(self, remote_path, data_bytes, chunk_size=512):
        """
        Write a file to the device in chunks using base64 encoding.
        Overwrites the file.
        """
        path_repr = repr(remote_path)

        # Truncate/create the file first
        truncate_code = (
            "import os\n"
            f"f = open({path_repr}, 'wb')\n"
            "f.close()\n"
        )
        self.exec_raw(truncate_code)

        # Now append in chunks
        for offset in range(0, len(data_bytes), chunk_size):
            chunk = data_bytes[offset:offset + chunk_size]
            b64 = base64.b64encode(chunk).decode("ascii")

            chunk_code = (
                "import ubinascii\n"
                f"f = open({path_repr}, 'ab')\n"
                f"f.write(ubinascii.a2b_base64('{b64}'))\n"
                "f.close()\n"
            )
            self.exec_raw(chunk_code)


def load_cache(cache_path):
    """
    Load the local deploy cache: a dict mapping remote_path -> sha256 hex
    digest of the host file content as of the last successful upload.
    Returns an empty dict if the cache doesn't exist or can't be read.
    """
    if not os.path.isfile(cache_path):
        return {}
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        print(f"[WARN] Could not read deploy cache at '{cache_path}'; starting fresh.",
              file=sys.stderr)
        return {}


def save_cache(cache_path, cache):
    """Write the deploy cache to disk. Saved after every successful upload
    rather than only at the end, so progress survives a mid-run failure."""
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, sort_keys=True)
    except OSError as exc:
        print(f"[WARN] Could not write deploy cache: {exc}", file=sys.stderr)


def file_hash(data):
    """Return the sha256 hex digest of the given bytes."""
    return hashlib.sha256(data).hexdigest()


def load_manifest(manifest_path):
    """
    Read manifest.list and return a list of (host_path, remote_path) files.
    Supports:
        - files
        - directories
        - dir/ and dir/* patterns (glob-like)
        - !pattern exclusions (gitignore-style, e.g. "!*.md")
    Directories are expanded recursively.
    Exclusion patterns are applied after all entries are expanded, so
    order within the manifest does not matter for exclusions.
    """
    manifest_path = os.path.abspath(manifest_path)
    root = os.path.dirname(manifest_path)
    files = []
    exclusions = []

    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Collect exclusion patterns — applied after full expansion
            if line.startswith("!"):
                exclusions.append(line[1:])
                continue

            entry = line

            # Handle patterns like "display/*" or "display/"
            is_dir_glob = False
            if entry.endswith("/*"):
                entry_dir = entry[:-2]
                is_dir_glob = True
            elif entry.endswith("/"):
                entry_dir = entry[:-1]
                is_dir_glob = True
            else:
                entry_dir = entry

            host_entry_path = os.path.join(root, entry_dir)

            if is_dir_glob or os.path.isdir(host_entry_path):
                # Walk directory recursively
                if not os.path.isdir(host_entry_path):
                    print(f"[WARN] Manifest directory not found: {entry}", file=sys.stderr)
                    continue
                for dirpath, _, filenames in os.walk(host_entry_path):
                    for fname in filenames:
                        host_file = os.path.join(dirpath, fname)
                        rel = os.path.relpath(host_file, root)
                        remote = rel.replace(os.sep, "/")
                        files.append((host_file, remote))
            elif os.path.isfile(host_entry_path):
                remote = entry.replace(os.sep, "/")
                files.append((host_entry_path, remote))
            else:
                print(f"[WARN] Manifest entry not found: {entry}", file=sys.stderr)

    # Apply exclusions. Each pattern is matched against the remote path,
    # which is always forward-slash separated (e.g. "SmartBus/README.md").
    # fnmatch matches against the full path, so "*.md" catches markdown
    # files in any subdirectory. Use "dir/*.md" to scope to a specific dir.
    if exclusions:
        before = len(files)
        files = [
            (host, remote) for host, remote in files
            if not any(fnmatch.fnmatch(remote, pat) for pat in exclusions)
        ]
        excluded = before - len(files)
        if excluded:
            print(f"[INFO] Excluded {excluded} file(s) via manifest exclusion patterns.")

    return files


def main():
    parser = argparse.ArgumentParser(description="Deploy TAFY files to MicroPython over serial.")
    parser.add_argument(
        "-p", "--port",
        help="Serial port (e.g. /dev/ttyACM0). If omitted, /dev/ttyACM0 is assumed."
    )
    parser.add_argument(
        "-b", "--baudrate",
        type=int,
        default=115200,
        help="Baudrate (default: 115200)"
    )
    parser.add_argument(
        "-m", "--manifest",
        default="manifest.list",
        help="Manifest file (default: manifest.list)"
    )
    parser.add_argument(
        "-o", "--overwrite",
        action="store_true",
        help=(
            "Force re-upload of all files, ignoring the local change-cache. "
            "Use this after reflashing MicroPython, since a fresh filesystem "
            "won't match what the cache thinks is already on the device."
        )
    )

    args = parser.parse_args()

    # Default port if not specified
    if args.port is None:
        args.port = "/dev/ttyACM0"
        print("[INFO] No serial port specified; defaulting to /dev/ttyACM0")

    files = load_manifest(args.manifest)
    if not files:
        print("No files to deploy (manifest empty or invalid).", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(files)} file(s) from manifest '{args.manifest}'.")

    cache_path = os.path.join(os.path.dirname(os.path.abspath(args.manifest)),
                               CACHE_FILENAME)
    cache = load_cache(cache_path)

    # Directories confirmed to exist on the device THIS run. Scoped to a
    # single run only — the device filesystem can be wiped between runs
    # (e.g. a fresh MicroPython flash), so this is never persisted to disk.
    created_dirs = set()

    dev = MicroPythonDevice(args.port, baudrate=args.baudrate)

    try:
        print("Entering raw REPL...")
        dev.enter_raw_repl()
        print("Connected. Beginning upload.\n")
        dev.start_update_mode()

        for host_path, remote_path in files:
            with open(host_path, "rb") as f:
                data = f.read()
            digest = file_hash(data)

            if not args.overwrite and cache.get(remote_path) == digest:
                print(f"[SKIP] '{remote_path}' unchanged since last deploy.\n")
                continue

            print(f"[*] Deploying '{host_path}' -> '{remote_path}'")

            # Ensure directories exist on device — but only once per
            # directory per run, rather than once per file.
            remote_dir = remote_path.rsplit("/", 1)[0] if "/" in remote_path else ""
            if remote_dir and remote_dir not in created_dirs:
                print(f"    [*] Ensuring directory '{remote_dir}' exists on device...")
                dev.make_dirs(remote_dir)
                created_dirs.add(remote_dir)

            # Upload
            print(f"    [*] Uploading {len(data)} bytes...")
            dev.write_file(remote_path, data)
            print("    [OK]\n")

            # Persist immediately so a mid-run failure doesn't lose progress
            cache[remote_path] = digest
            save_cache(cache_path, cache)

        print("[INFO] Requesting soft reset on device...")
        dev.exec_raw("import machine\nmachine.soft_reset()\n")

        print("All done.")

    finally:
        print("Exiting raw REPL and closing serial...")
        dev.update_complete()
        try:
            dev.exit_raw_repl()
        except:
            print("[WARNING] Could not close raw REPL! Please unplug and re-plug in your device to reboot it!")
            pass
        dev.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python

# -*- coding: utf-8 -*-
# vim: sw=4:ts=4:si:et:enc=utf-8

# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "progressbar2",
#     "pyserial",
# ]
# ///

# Author: Ivan A-R <ivan@tuxotronic.org>
# Project page: http://tuxotronic.org/wiki/projects/stm32loader
#
# This file is part of stm32loader.
#
# stm32loader is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 3, or (at your option) any later
# version.
#
# stm32loader is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with stm32loader; see the file COPYING3.  If not see
# <http://www.gnu.org/licenses/>.

import argparse
import logging
import time
from enum import IntEnum

import serial
from progressbar import ETA, Bar, Percentage, ProgressBar


# these come from AN2606 Table 226
class ChipID(IntEnum):
    # C0
    STM32C011xx = 0x443
    STM32C031xx = 0x453
    STM32C051xx = 0x44C
    STM32C071xx = 0x493
    STM32C091xx_C092xx = 0x44D
    # C5
    STM32C55xxx_C562xx = 0x44E
    STM32C53xxx_C542xx = 0x44F
    STM32C5A3xx_C59xxx = 0x45A
    # F0
    STM32F05xxx_F030x8 = 0x440
    STM32F03xx4_6 = 0x444
    STM32F030xC_F09xxx = 0x442  # shared PID
    STM32F04xxx_F070x6 = 0x445  # shared PID
    STM32F070xB_F071xx_F072xx = 0x448  # shared PID
    # F1
    STM32F10xxx_Low_density = 0x412
    STM32F10xxx_Medium_density = 0x410
    STM32F10xxx_High_density = 0x414
    STM32F10xxx_Medium_density_value_line = 0x420
    STM32F10xxx_High_density_value_line = 0x428
    STM32F105xx_F107xx = 0x418
    STM32F10xxx_XL_density = 0x430
    # F2
    STM32F2xxxx = 0x411
    # F3
    STM32F373xx_F378xx = 0x432  # shared PID
    STM32F302xB_C_F303xB_C_F358xx = 0x422  # shared PID
    STM32F301xx_F302xx_F318xx = 0x439  # shared PID
    STM32F303x4_6_8_F334xx_F328xx = 0x438
    STM32F302xD_E_F303xD_E_F398xx = 0x446  # shared PID
    # F4
    STM32F40xxx_F41xxx = 0x413
    STM32F42xxx_F43xxx = 0x419
    STM32F401xB_C = 0x423
    STM32F401xD_E = 0x433
    STM32F410xx = 0x458
    STM32F411xx = 0x431
    STM32F412xx = 0x441
    STM32F446xx = 0x421
    STM32F469xx_F479xx = 0x434
    STM32F413xx_F423xx = 0x463
    # F7
    STM32F72xxx_F73xxx = 0x452
    STM32F74xxx_F75xxx = 0x449
    STM32F76xxx_F77xxx = 0x451
    # G0
    STM32G03xxx_G04xxx = 0x466
    STM32G05xxx_G061xx = 0x456
    STM32G07xxx_G08xxx = 0x460
    STM32G0B0xx_G0B1xx_G0C1xx = 0x467  # shared PID
    # G4
    STM32G431xx_G441xx = 0x468
    STM32G47xxx_G48xxx = 0x469
    STM32G491xx_GA1xx = 0x479
    # H5
    STM32H503xx = 0x474
    STM32H562xx_H563xx_H573xx = 0x484
    STM32H523xx_H533xx = 0x478
    STM32H5Ex_H5Fx = 0x47A
    # H7
    STM32H72xxx_H73xxx = 0x483
    STM32H74xxx_H75xxx = 0x450
    STM32H7A3xx_H7B3xx_H7B0xx = 0x480
    STM32H7Rxxx_H7Sxxx = 0x485
    # L0
    STM32L01xxx_L02xxx = 0x457
    STM32L031xx_L041xx = 0x425
    STM32L05xxx_L06xxx = 0x417
    STM32L07xxx_L08xxx = 0x447
    # L1
    STM32L1xxx6_8_B = 0x416
    STM32L1xxx6_8_BA = 0x429
    STM32L1xxxC = 0x427
    STM32L1xxxD = 0x436
    STM32L1xxxE = 0x437
    # L4
    STM32L412xx_L422xx = 0x464
    STM32L43xxx_L44xxx = 0x435
    STM32L45xxx_L46xxx = 0x462
    STM32L47xxx_L48xxx = 0x415
    STM32L496xx_L4A6xx = 0x461
    STM32L4Rxx_L4Sxx = 0x470
    STM32L4P5xx_L4Q5xx = 0x471
    # L5
    STM32L552xx_L562xx = 0x472
    # U0
    STM32U031xx = 0x459
    STM32U073xx_U083xx = 0x489
    # U3
    STM32U375xx_U385xx = 0x454
    STM32U3B5xx_U3C5xx = 0x42A
    # U5
    STM32U535xx_U545xx = 0x455
    STM32U575xx_U585xx = 0x482
    STM32U595xx_U599xx_U5A9xx = 0x481
    STM32U5F7xx_U5F9xx_U5G7xx_U5G9xx = 0x476
    # WB
    STM32WB10xx_WB15xx = 0x494
    STM32WB30xx_WB35xx_WB50xx_WB55xx = 0x495
    # WBA
    STM32WBA2xxx = 0x4B2
    STM32WBA5xxx = 0x492
    STM32WBA62xx_WBA63xx_WBA64xx_WBA65xx = 0x4B0
    # WL
    STM32WLE5xx_WL55xx = 0x497


log = logging.getLogger(__name__)


class CmdException(Exception):
    pass


class CommandInterface:
    extended_erase = 0

    def open(self, aport="/dev/tty.usbserial-ftCYPMYJ", abaudrate=115200):
        self.sp = serial.Serial(
            port=aport,
            baudrate=abaudrate,  # baudrate
            bytesize=8,  # number of databits
            parity=serial.PARITY_EVEN,
            stopbits=1,
            xonxoff=False,  # don't enable software flow control
            rtscts=False,  # don't enable RTS/CTS flow control
            timeout=5,  # set a timeout value, None for waiting forever
        )

    def _wait_for_ask(self, info=""):
        try:
            ask = self.sp.read(1)[0]
        except (IndexError, serial.SerialException):
            raise CmdException("Can't read port or timeout")
        if ask == 0x79:
            return 1
        elif ask == 0x1F:
            raise CmdException("NACK " + info)
        else:
            raise CmdException(f"Unknown response. {info}: {hex(ask)}")

    def reset(self):
        self.sp.dtr = False  # Assert NRST (reset)
        time.sleep(0.1)
        self.sp.dtr = True  # Release NRST
        time.sleep(0.5)

    def initChip(self):
        self.sp.rts = False  # BOOT0 high = bootloader mode (if wired)
        self.sp.reset_input_buffer()

        # Use a short timeout to probe whether the chip is already synced.
        saved_timeout = self.sp.timeout
        self.sp.timeout = 0.5
        self.sp.write(b"\x7f")
        response = self.sp.read(1)
        self.sp.timeout = saved_timeout

        if response == b"\x79":
            # ACK: chip just booted into bootloader and is now synced.
            return 1

        if response == b"\x1f":
            # NACK: chip is synced and already in command-waiting state.
            return 1

        if not response:
            # Timeout: chip received 0x7f as a command byte (it was already
            # synced) and is now waiting for the complement byte.  Send 0x80
            # (= 0x7f ^ 0xFF) to complete the invalid command; the bootloader
            # will NACK it and return to idle, ready for real commands.
            self.sp.write(b"\x80")
            try:
                self._wait_for_ask("re-sync")
            except CmdException as e:
                if "NACK" in str(e):
                    return 1  # Expected: invalid command rejected, now at idle
            raise CmdException("Can't read port or timeout")

        raise CmdException(f"Unexpected sync response: {hex(response[0])}")

    def releaseChip(self):
        self.sp.rts = True
        self.reset()

    def cmdGeneric(self, cmd):
        self.sp.write(bytes([cmd, cmd ^ 0xFF]))
        return self._wait_for_ask(hex(cmd))

    def cmdGet(self):
        if self.cmdGeneric(0x00):
            log.debug("*** Get command")
            length = self.sp.read(1)[0]
            version = self.sp.read(1)[0]
            log.debug(f"Bootloader version: {hex(version)}")
            dat = [hex(b) for b in self.sp.read(length)]
            if "0x44" in dat:
                self.extended_erase = 1
            log.debug("Available commands: " + ", ".join(dat))
            self._wait_for_ask("0x00 end")
            return version
        else:
            raise CmdException("Get (0x00) failed")

    def cmdGetVersion(self):
        if self.cmdGeneric(0x01):
            log.debug("*** GetVersion command")
            version = self.sp.read(1)[0]
            self.sp.read(2)
            self._wait_for_ask("0x01 end")
            log.debug(f"Bootloader version: {hex(version)}")
            return version
        else:
            raise CmdException("GetVersion (0x01) failed")

    def cmdGetID(self):
        if self.cmdGeneric(0x02):
            log.debug("*** GetID command")
            length = self.sp.read(1)[0]
            id_bytes = self.sp.read(length + 1)
            self._wait_for_ask("0x02 end")
            return int.from_bytes(id_bytes, "big")
        else:
            raise CmdException("GetID (0x02) failed")

    def _encode_addr(self, addr):
        byte3 = (addr >> 0) & 0xFF
        byte2 = (addr >> 8) & 0xFF
        byte1 = (addr >> 16) & 0xFF
        byte0 = (addr >> 24) & 0xFF
        crc = byte0 ^ byte1 ^ byte2 ^ byte3
        return bytes([byte0, byte1, byte2, byte3, crc])

    def cmdReadMemory(self, addr, lng):
        assert lng <= 256
        if self.cmdGeneric(0x11):
            log.debug("*** ReadMemory command")
            self.sp.write(self._encode_addr(addr))
            self._wait_for_ask("0x11 address failed")
            N = (lng - 1) & 0xFF
            self.sp.write(bytes([N, N ^ 0xFF]))
            self._wait_for_ask("0x11 length failed")
            return list(self.sp.read(lng))
        else:
            raise CmdException("ReadMemory (0x11) failed")

    def cmdGo(self, addr):
        if self.cmdGeneric(0x21):
            log.debug("*** Go command")
            self.sp.write(self._encode_addr(addr))
            self._wait_for_ask("0x21 go failed")
        else:
            raise CmdException("Go (0x21) failed")

    def cmdWriteMemory(self, addr, data):
        assert len(data) <= 256
        if self.cmdGeneric(0x31):
            log.debug("*** Write memory command")
            self.sp.write(self._encode_addr(addr))
            self._wait_for_ask("0x31 address failed")
            lng = (len(data) - 1) & 0xFF
            log.debug(f"{lng + 1} bytes to write")
            crc = 0xFF
            for c in data:
                crc ^= c
            self.sp.write(bytes([lng]) + bytes(data))
            self.sp.write(bytes([crc]))
            self._wait_for_ask("0x31 programming failed")
            log.debug("Write memory done")
        else:
            raise CmdException("Write memory (0x31) failed")

    def cmdEraseMemory(self, sectors=None):
        if self.extended_erase:
            return self.cmdExtendedEraseMemory()

        if self.cmdGeneric(0x43):
            log.debug("*** Erase memory command")
            if sectors is None:
                # Global erase
                self.sp.write(bytes([0xFF, 0x00]))
            else:
                # Sectors erase
                self.sp.write(bytes([(len(sectors) - 1) & 0xFF]))
                crc = 0xFF
                for c in sectors:
                    crc ^= c
                self.sp.write(bytes(sectors))
                self.sp.write(bytes([crc]))
            self._wait_for_ask("0x43 erasing failed")
            log.debug("Erase memory done")
        else:
            raise CmdException("Erase memory (0x43) failed")

    def cmdExtendedEraseMemory(self):
        if self.cmdGeneric(0x44):
            log.debug("*** Extended Erase memory command")
            # Global mass erase + checksum
            self.sp.write(bytes([0xFF, 0xFF, 0x00]))
            tmp = self.sp.timeout
            self.sp.timeout = 30
            log.info("Extended erase (0x44), this can take ten seconds or more")
            self._wait_for_ask("0x44 erasing failed")
            self.sp.timeout = tmp
            log.debug("Extended Erase memory done")
        else:
            raise CmdException("Extended Erase memory (0x44) failed")

    def cmdWriteProtect(self, sectors):
        if self.cmdGeneric(0x63):
            log.debug("*** Write protect command")
            self.sp.write(bytes([(len(sectors) - 1) & 0xFF]))
            crc = 0xFF
            for c in sectors:
                crc ^= c
            self.sp.write(bytes(sectors))
            self.sp.write(bytes([crc]))
            self._wait_for_ask("0x63 write protect failed")
            log.debug("Write protect done")
        else:
            raise CmdException("Write Protect memory (0x63) failed")

    def cmdWriteUnprotect(self):
        if self.cmdGeneric(0x73):
            log.debug("*** Write Unprotect command")
            self._wait_for_ask("0x73 write unprotect failed")
            self._wait_for_ask("0x73 write unprotect 2 failed")
            log.debug("Write Unprotect done")
        else:
            raise CmdException("Write Unprotect (0x73) failed")

    def cmdReadoutProtect(self):
        if self.cmdGeneric(0x82):
            log.debug("*** Readout protect command")
            self._wait_for_ask("0x82 readout protect failed")
            self._wait_for_ask("0x82 readout protect 2 failed")
            log.debug("Read protect done")
        else:
            raise CmdException("Readout protect (0x82) failed")

    def cmdReadoutUnprotect(self):
        if self.cmdGeneric(0x92):
            log.debug("*** Readout Unprotect command")
            self._wait_for_ask("0x92 readout unprotect failed")
            self._wait_for_ask("0x92 readout unprotect 2 failed")
            log.debug("Read Unprotect done")
        else:
            raise CmdException("Readout unprotect (0x92) failed")

    # Complex commands section

    def readMemory(self, addr, lng):
        data = []
        widgets = ["Reading: ", Percentage(), " ", ETA(), " ", Bar()]
        pbar = ProgressBar(widgets=widgets, maxval=lng, term_width=79).start()

        while lng > 256:
            pbar.update(pbar.max_value - lng)

            data += self.cmdReadMemory(addr, 256)
            addr += 256
            lng -= 256

        pbar.update(pbar.max_value - lng)
        pbar.finish()

        data += self.cmdReadMemory(addr, lng)
        return data

    def writeMemory(self, addr, data):
        lng = len(data)
        widgets = ["Writing: ", Percentage(), " ", ETA(), " ", Bar()]
        pbar = ProgressBar(widgets=widgets, max_value=lng, term_width=79).start()

        offs = 0
        while lng > 256:
            pbar.update(pbar.max_value - lng)  # type: ignore

            self.cmdWriteMemory(addr, data[offs : offs + 256])
            offs += 256
            addr += 256
            lng -= 256

        pbar.update(pbar.max_value - lng)  # type: ignore

        pbar.finish()

        self.cmdWriteMemory(addr, data[offs : offs + lng] + [0xFF] * (256 - lng))

    def __init__(self):
        pass


def auto_int(x):
    return int(x, 0)


def main():
    # Shared arguments for commands that connect to a device
    port_parser = argparse.ArgumentParser(add_help=False)
    port_parser.add_argument("port", help="Serial port (e.g. COM3, /dev/ttyUSB0)")
    port_parser.add_argument(
        "-b",
        "--baud",
        type=int,
        default=115200,
        help="Baud speed (default: %(default)s)",
    )
    port_parser.add_argument(
        "-a",
        "--address",
        type=auto_int,
        default=0x08000000,
        help="Target address (default: 0x08000000)",
    )
    port_parser.add_argument(
        "-g",
        "--go-addr",
        type=auto_int,
        default=-1,
        metavar="ADDR",
        help="Send the bootloader GO command to ADDR after operation",
    )

    parser = argparse.ArgumentParser(
        description="STM32 bootloader utility",
        epilog=(
            "Example: %(prog)s --run write COM3 firmware.bin --erase --verify"
        ),
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")
    parser.add_argument("-V", "--verbose", action="store_true", help="Verbose mode")
    parser.add_argument(
        "--run",
        action="store_true",
        help="Reset or release the chip to run after the operation",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # list: enumerate available serial ports
    subparsers.add_parser("list", help="List available serial ports")

    # info: show bootloader version and chip ID
    subparsers.add_parser(
        "info",
        parents=[port_parser],
        help="Show chip info (bootloader version, chip ID)",
    )

    # erase: mass erase flash
    subparsers.add_parser(
        "erase",
        parents=[port_parser],
        help="Erase flash memory",
    )

    # write: write a binary file to flash
    write_parser = subparsers.add_parser(
        "write",
        parents=[port_parser],
        help="Write binary file to flash",
    )
    write_parser.add_argument("file", help="Binary file to write")
    write_parser.add_argument(
        "-e", "--erase", action="store_true", help="Erase before writing"
    )
    write_parser.add_argument(
        "-v", "--verify", action="store_true", help="Verify after writing"
    )

    # read: read flash to a file
    read_parser = subparsers.add_parser(
        "read",
        parents=[port_parser],
        help="Read flash memory to file",
    )
    read_parser.add_argument("file", help="Output file")
    read_parser.add_argument(
        "-l",
        "--length",
        type=auto_int,
        dest="len",
        required=True,
        help="Number of bytes to read",
    )

    args = parser.parse_args()

    log_level = (
        logging.DEBUG
        if args.verbose
        else logging.WARNING
        if args.quiet
        else logging.INFO
    )
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    if args.command == "list":
        from serial.tools.list_ports import comports

        ports = sorted(comports())
        if ports:
            for p in ports:
                print(f"{p.device}: {p.description}")
        else:
            print("No serial ports found.")
        return

    cmd = CommandInterface()
    cmd.open(args.port, args.baud)
    log.debug(f"Open port {args.port}, baud {args.baud}")
    try:
        try:
            log.debug("Resetting and initializing chip...")
            cmd.initChip()
        except Exception as e:
            log.error(f"Can't init ({e})")
            log.error(
                "Make sure the device is connected, in bootloader mode and not used by another program."
            )
            return

        match args.command:
            case "info":
                log.debug("Getting bootloader version and chip ID...")
                bootversion = cmd.cmdGet()
                log.info(f"Bootloader version {bootversion:X}")
                chip_id = cmd.cmdGetID()
                try:
                    chip_name = ChipID(chip_id).name
                except ValueError:
                    chip_name = "Unknown"
                log.info(f"Chip id: 0x{chip_id:x} ({chip_name})")

            case "erase":
                cmd.cmdEraseMemory()

            case "write":
                with open(args.file, "rb") as f:
                    data = list(f.read())
                if args.erase:
                    cmd.cmdEraseMemory()
                cmd.writeMemory(args.address, data)
                if args.verify:
                    verify = cmd.readMemory(args.address, len(data))
                    if data == verify:
                        print("Verification OK")
                    else:
                        print("Verification FAILED")
                        print(f"{len(data)} vs {len(verify)}")
                        for i in range(len(data)):
                            if data[i] != verify[i]:
                                print(f"{hex(i)}: {hex(data[i])} vs {hex(verify[i])}")

            case "read":
                rdata = cmd.readMemory(args.address, args.len)
                with open(args.file, "wb") as f:
                    f.write(bytes(rdata))

    finally:
        if args.go_addr != -1:
            cmd.cmdGo(args.go_addr)
            # cmdGo already jumped to application, just close the port without reset
            cmd.sp.close()
        elif args.run:
            # --run without --go-addr: exit bootloader mode and reset to run normally
            print("Releasing chip to run...")
            cmd.releaseChip()
        else:
            cmd.sp.close()

    print("Done.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Free Medicine pocket slots in an Origin HeartGold save.

A completely full Medicine pocket (40/40) is the one risky thing left over
from the bag edit, so this drops a few cheap, easy-to-rebuy items from the
newest save partition: Potion, Moomoo Milk, Lava Cookie and Old Gateau.

Usage: free_medicine_slots.py IN.sav OUT.sav
"""
import struct
import sys

from origin_hg_bag_edit import (FOOTER_SIZE, GENERAL_SIZE, PARTITIONS,
                                block_info, crc16_ccitt, remove_item)

CHEAP_MEDICINE = (17, 33, 42, 54)  # Potion, Moomoo Milk, Lava Cookie, Old Gateau


def main(src, dst):
    sav = bytearray(open(src, "rb").read())
    valid = [(count, b) for b in PARTITIONS for count, ok in [block_info(sav, b)] if ok]
    if not valid:
        raise SystemExit("no valid general block found")
    _, base = max(valid)

    for item in CHEAP_MEDICINE:
        remove_item(sav, base, "medicine", item)

    footer = base + GENERAL_SIZE - FOOTER_SIZE
    struct.pack_into("<H", sav, footer + 0xE, crc16_ccitt(sav[base:footer]))
    open(dst, "wb").write(sav)
    print(f"patched general block at {base:#x} -> {dst}")


if __name__ == "__main__":
    main(*sys.argv[1:3])

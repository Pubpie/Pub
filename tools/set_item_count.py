#!/usr/bin/env python3
"""Set the count of one item in the newest partition of an Origin HeartGold save.

The item is added to the pocket if it is missing, and its count is set to
COUNT (also when that is lower than the current count).

Usage: set_item_count.py IN.sav OUT.sav POCKET ITEM_ID COUNT
Example (Rare Candy x999): set_item_count.py in.sav out.sav medicine 50 999
"""
import struct
import sys

from origin_hg_bag_edit import (FOOTER_SIZE, GENERAL_SIZE, PARTITIONS, POCKETS,
                                add_item, block_info, crc16_ccitt)


def main(src, dst, pocket, item, count):
    item, count = int(item, 0), int(count, 0)
    sav = bytearray(open(src, "rb").read())
    valid = [(n, b) for b in PARTITIONS for n, ok in [block_info(sav, b)] if ok]
    if not valid:
        raise SystemExit("no valid general block found")
    _, base = max(valid)

    off, slots = POCKETS[pocket]
    for i in range(slots):
        pos = base + off + 4 * i
        if struct.unpack_from("<H", sav, pos)[0] == item:
            struct.pack_into("<HH", sav, pos, item, count)
            break
    else:
        add_item(sav, base, pocket, item, count)

    footer = base + GENERAL_SIZE - FOOTER_SIZE
    struct.pack_into("<H", sav, footer + 0xE, crc16_ccitt(sav[base:footer]))
    open(dst, "wb").write(sav)
    print(f"{pocket} item {item} x{count} -> {dst}")


if __name__ == "__main__":
    main(*sys.argv[1:6])

#!/usr/bin/env python3
"""Add items to the bag of a Pokemon Origin HeartGold (hg-engine) save file.

Origin HeartGold uses an expanded HGSS save: the general block is 0xF7CC bytes
(vanilla 0xF628) and the TM pocket is enlarged, so the pockets after it move.
Item IDs follow the hg-engine numbering used by this hack (Mints 771-791,
Ability Patch 625).

Usage: origin_hg_bag_edit.py IN.sav OUT.sav
"""
import struct
import sys

GENERAL_SIZE = 0xF7CC
FOOTER_SIZE = 0x10
PARTITIONS = (0x00000, 0x40000)

# (offset in general block, slot count); each slot is u16 item id + u16 count.
POCKETS = {
    "items": (0x644, 165),
    "key": (0x8D8, 50),
    "tm": (0x9A0, 151),
    "mail": (0xBFC, 12),
    "medicine": (0xC2C, 40),
    "berries": (0xCCC, 64),
    "balls": (0xDCC, 24),
    "battle": (0xE2C, 30),
}

ITEM_RARE_CANDY = 50
VITAMINS = {"HP Up": 45, "Protein": 46, "Iron": 47, "Carbos": 48, "Calcium": 49, "Zinc": 52}
ITEM_SPELL_TAG = 247
ITEM_GOLD_BOTTLE_CAP = 617
ITEM_ABILITY_PATCH = 625
MINTS = {
    "Lonely": 771, "Adamant": 772, "Naughty": 773, "Brave": 774, "Bold": 775,
    "Impish": 776, "Lax": 777, "Relaxed": 778, "Modest": 779, "Mild": 780,
    "Rash": 781, "Quiet": 782, "Calm": 783, "Gentle": 784, "Careful": 785,
    "Sassy": 786, "Timid": 787, "Hasty": 788, "Jolly": 789, "Naive": 790,
    "Serious": 791,
}

# The medicine pocket is too small for everything, so drop these cheap
# single-count items (Ice Heal, Fresh Water, Energy Powder, Energy Root,
# Heal Powder, Revival Herb) to make room for all the Mints.
REMOVE = [("medicine", item) for item in (20, 30, 34, 35, 36, 37)]

WANTED = [
    ("items", ITEM_SPELL_TAG, 99),
    ("items", ITEM_GOLD_BOTTLE_CAP, 999),
    ("medicine", ITEM_RARE_CANDY, 999),
] + [("medicine", item, 999) for item in VITAMINS.values()] + [
    ("medicine", ITEM_ABILITY_PATCH, 99),
] + [("medicine", item, 99) for item in MINTS.values()]


def crc16_ccitt(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def block_info(sav, base):
    footer = base + GENERAL_SIZE - FOOTER_SIZE
    count, size, magic = struct.unpack_from("<III", sav, footer)
    crc = struct.unpack_from("<H", sav, footer + 0xE)[0]
    valid = size == GENERAL_SIZE and crc == crc16_ccitt(sav[base:footer])
    return count, valid


def remove_item(sav, base, pocket, item):
    off, slots = POCKETS[pocket]
    kept = []
    for i in range(slots):
        slot = struct.unpack_from("<HH", sav, base + off + 4 * i)
        if slot[0] and slot[0] != item:
            kept.append(slot)
    # Pockets are stored packed, with no gaps between used slots.
    for i in range(slots):
        struct.pack_into("<HH", sav, base + off + 4 * i, *(kept[i] if i < len(kept) else (0, 0)))


def add_item(sav, base, pocket, item, count):
    off, slots = POCKETS[pocket]
    free = None
    for i in range(slots):
        pos = base + off + 4 * i
        cur, n = struct.unpack_from("<HH", sav, pos)
        if cur == item:
            struct.pack_into("<HH", sav, pos, item, max(n, count))
            return
        if cur == 0 and free is None:
            free = pos
    if free is None:
        raise SystemExit(f"{pocket} pocket is full, cannot add item {item}")
    struct.pack_into("<HH", sav, free, item, count)


def main(src, dst):
    sav = bytearray(open(src, "rb").read())
    blocks = [(block_info(sav, b), b) for b in PARTITIONS]
    valid = [(count, b) for (count, ok), b in blocks if ok]
    if not valid:
        raise SystemExit("no valid general block found")
    _, base = max(valid)

    for pocket, item in REMOVE:
        remove_item(sav, base, pocket, item)
    for pocket, item, count in WANTED:
        add_item(sav, base, pocket, item, count)

    footer = base + GENERAL_SIZE - FOOTER_SIZE
    struct.pack_into("<H", sav, footer + 0xE, crc16_ccitt(sav[base:footer]))
    open(dst, "wb").write(sav)
    print(f"patched general block at {base:#x} -> {dst}")


if __name__ == "__main__":
    main(*sys.argv[1:3])

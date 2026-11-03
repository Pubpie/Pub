#!/usr/bin/env python3
"""Turn a melonDS savestate (.mlN) of Origin HeartGold into a .sav file.

The game keeps its whole save data in main RAM while running, so the state
holds progress made after the last in-game save. This copies that live data
(general block + PC storage block) into the save memory found in the
state, writes it to the older of the two save partitions with a higher save
count, and fixes the checksums, the same way an in-game save would.

Usage: melonds_state_to_sav.py STATE.ml1 OUT.sav
"""
import struct
import sys

from extract_melonds_save import FOOTER_MAGIC, GENERAL_FOOTER_MAGIC_OFFSET, SAVE_SIZE, sections
from origin_hg_bag_edit import FOOTER_SIZE, GENERAL_SIZE, PARTITIONS, block_info, crc16_ccitt

MAIN_RAM_SIZE = 0x400000
STORAGE_START = 0xF800  # storage block offset, both in a partition and in RAM
STORAGE_SIZE = 0x18408
# Player location (current map, previous map, warps, spawn point, ...). The
# game updates it in RAM on every map change, but saves the map objects only
# on an in-game save, so mixing a live location with stale map objects gives
# a black screen. Keep the location from the last in-game save instead.
LOCAL_FIELD_DATA = slice(0x1320, 0x13A8)
TRAINER = slice(0x64, 0x78)  # trainer name + IDs, used to find the live block
PLAY_TIME = 0x86


def play_time(buf, off):
    h, m, s = struct.unpack_from("<HBB", buf, off + PLAY_TIME)
    return h * 3600 + m * 60 + s


def main(src, dst):
    state = open(src, "rb").read()
    secs = {tag: (off, length) for tag, off, length in sections(state)}

    off, length = secs[b"NDCS"]
    ndcs = state[off:off + length]
    start = ndcs.find(FOOTER_MAGIC) - GENERAL_FOOTER_MAGIC_OFFSET
    sav = bytearray(ndcs[start:start + SAVE_SIZE])

    blocks = [(block_info(sav, b), b) for b in PARTITIONS]
    newest = max((count, b) for (count, ok), b in blocks if ok)
    count, newest_base = newest
    older_base = next(b for b in PARTITIONS if b != newest_base)

    off, _ = secs[b"NDSG"]
    ram = state[off + 0x10:off + 0x10 + MAIN_RAM_SIZE]

    # The trainer info shows up in several RAM buffers; the live one is the
    # one with the longest play time.
    key = bytes(sav[newest_base + TRAINER.start:newest_base + TRAINER.stop])
    candidates = []
    pos = ram.find(key)
    while pos != -1:
        candidates.append(pos - TRAINER.start)
        pos = ram.find(key, pos + 1)
    if not candidates:
        raise SystemExit("live save data not found in RAM")
    live = max(candidates, key=lambda g: play_time(ram, g))

    for block_start, size in ((0, GENERAL_SIZE), (STORAGE_START, STORAGE_SIZE)):
        data_len = size - FOOTER_SIZE
        dst_off = older_base + block_start
        sav[dst_off:dst_off + data_len] = ram[live + block_start:live + block_start + data_len]
        if block_start == 0:
            sav[dst_off + LOCAL_FIELD_DATA.start:dst_off + LOCAL_FIELD_DATA.stop] = \
                sav[newest_base + LOCAL_FIELD_DATA.start:newest_base + LOCAL_FIELD_DATA.stop]
        # Copy the footer layout from the newest partition, then bump the count.
        footer = dst_off + data_len
        sav[footer:footer + FOOTER_SIZE] = sav[newest_base + block_start + data_len:
                                               newest_base + block_start + size]
        struct.pack_into("<I", sav, footer, count + 1)
        struct.pack_into("<H", sav, footer + 0xE, crc16_ccitt(sav[dst_off:footer]))

    open(dst, "wb").write(sav)
    t = play_time(sav, older_base)
    print(f"live data (play time {t // 3600}:{t // 60 % 60:02}) -> partition {older_base:#x} -> {dst}")


if __name__ == "__main__":
    main(*sys.argv[1:3])

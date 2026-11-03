#!/usr/bin/env python3
"""Pull the 512 KiB cartridge save out of a melonDS savestate (.mlN).

The savestate keeps a copy of the save memory in its "NDCS" section, so this
recovers the last in-game save even when the state itself was taken while
the game was frozen.

Usage: extract_melonds_save.py STATE.ml1 OUT.sav
"""
import struct
import sys

SAVE_SIZE = 0x80000
FOOTER_MAGIC = struct.pack("<I", 0x20060623)
GENERAL_FOOTER_MAGIC_OFFSET = 0xF7C4  # magic inside the first general block


def sections(state):
    if state[:4] != b"MELN":
        raise SystemExit("not a melonDS savestate")
    off = 0x10
    while off + 16 <= len(state):
        tag = state[off:off + 4]
        length = struct.unpack_from("<I", state, off + 4)[0]
        if length < 16:
            break
        yield tag, off, length
        off += length


def main(src, dst):
    state = open(src, "rb").read()
    for tag, off, length in sections(state):
        if tag != b"NDCS":
            continue
        data = state[off:off + length]
        magic = data.find(FOOTER_MAGIC)
        if magic == -1:
            raise SystemExit("no Pokemon save found in the NDCS section")
        start = magic - GENERAL_FOOTER_MAGIC_OFFSET
        open(dst, "wb").write(data[start:start + SAVE_SIZE])
        print(f"wrote {dst}")
        return
    raise SystemExit("savestate has no NDCS section")


if __name__ == "__main__":
    main(*sys.argv[1:3])

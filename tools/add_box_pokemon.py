#!/usr/bin/env python3
"""Put made-to-order Pokemon into a PC box of an Origin HeartGold save.

Each Pokemon is built from one of the player's own caught Pokemon (OT name,
trainer ID, language, met data), then given its species, shiny PID with the
chosen nature, ability, moves, held item, IVs/EVs and level. Origin
HeartGold stores the ability ID as a u16 at 0x42 and its slot (0/1) at 0x15,
unlike vanilla HGSS.

Usage: add_box_pokemon.py IN.sav OUT.sav BOX
  BOX is 1-based; the Pokemon go into the first empty slots of that box.
"""
import random
import struct
import sys

from origin_hg_bag_edit import FOOTER_SIZE, GENERAL_SIZE, PARTITIONS, block_info, crc16_ccitt

STORAGE_START = 0xF800
STORAGE_SIZE = 0x18408
BOX_SIZE = 0x1000
BOX_SLOTS = 30
BOX_MON_SIZE = 136
TRAINER_IDS = 0x74  # TID, SID in the general block

BLOCK_ORDERS = ["ABCD", "ABDC", "ACBD", "ACDB", "ADBC", "ADCB", "BACD", "BADC",
                "BCAD", "BCDA", "BDAC", "BDCA", "CABD", "CADB", "CBAD", "CBDA",
                "CDAB", "CDBA", "DABC", "DACB", "DBAC", "DBCA", "DCAB", "DCBA"]

EXP_AT_100 = {"fast": 800000, "medium_fast": 1000000, "medium_slow": 1059860,
              "slow": 1250000, "erratic": 600000, "fluctuating": 1640000}

NATURES = ["Hardy", "Lonely", "Brave", "Adamant", "Naughty", "Bold", "Docile",
           "Relaxed", "Impish", "Lax", "Timid", "Hasty", "Serious", "Jolly",
           "Naive", "Modest", "Mild", "Quiet", "Bashful", "Rash", "Calm",
           "Gentle", "Sassy", "Careful", "Quirky"]

ITEM_POKE_BALL = 4

# moves: (move id, base PP); stats order HP, Atk, Def, Spe, SpA, SpD
POKEMON = [
    dict(name="Wailord", species=321, growth="fluctuating", gender_ratio=127,
         nature="Modest", ability=41, ability_slot=0,  # Water Veil
         item=297,  # Choice Specs
         moves=[(323, 5), (57, 15), (58, 10), (87, 10)],  # Water Spout, Surf, Ice Beam, Thunder
         evs=[252, 0, 0, 6, 252, 0]),
    dict(name="Relicanth", species=369, growth="slow", gender_ratio=31,
         nature="Adamant", ability=69, ability_slot=1,  # Rock Head
         item=220,  # Choice Band
         moves=[(457, 5), (127, 15), (89, 10), (38, 15)],  # Head Smash, Waterfall, Earthquake, Double-Edge
         evs=[252, 252, 0, 0, 0, 6]),
]


def prng(seed, n):
    for _ in range(n):
        seed = (seed * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
        yield seed >> 16


def xor_words(data, seed):
    words = struct.unpack("<%dH" % (len(data) // 2), data)
    return struct.pack("<%dH" % len(words), *(w ^ k for w, k in zip(words, prng(seed, len(words)))))


def decrypt(raw):
    pid, _, chk = struct.unpack_from("<IHH", raw)
    body = xor_words(raw[8:BOX_MON_SIZE], chk)
    order = BLOCK_ORDERS[((pid & 0x3E000) >> 0xD) % 24]
    blocks = {order[i]: body[32 * i:32 * i + 32] for i in range(4)}
    data = bytearray(raw[:8] + b"".join(blocks[c] for c in "ABCD"))
    ok = sum(struct.unpack_from("<64H", data, 8)) & 0xFFFF == chk
    return data, ok


def encrypt(data):
    pid = struct.unpack_from("<I", data)[0]
    chk = sum(struct.unpack_from("<64H", data, 8)) & 0xFFFF
    struct.pack_into("<H", data, 6, chk)
    order = BLOCK_ORDERS[((pid & 0x3E000) >> 0xD) % 24]
    blocks = {c: data[8 + 32 * i:8 + 32 * i + 32] for i, c in enumerate("ABCD")}
    return bytes(data[:8]) + xor_words(b"".join(blocks[c] for c in order), chk)


def encode_name(name):
    out = []
    for c in name:
        if "A" <= c <= "Z":
            out.append(0x12B + ord(c) - ord("A"))
        elif "a" <= c <= "z":
            out.append(0x145 + ord(c) - ord("a"))
        else:
            raise ValueError(c)
    out.append(0xFFFF)
    return struct.pack("<11H", *(out + [0] * (11 - len(out))))


def shiny_pid(tid, sid, nature, ability_slot, gender_ratio, rng):
    while True:
        lo = rng.getrandbits(16)
        hi = tid ^ sid ^ lo ^ rng.getrandbits(3)
        pid = hi << 16 | lo
        male = (pid & 0xFF) >= gender_ratio
        if pid % 25 == nature and pid & 1 == ability_slot and male:
            return pid


def build(template, tid, sid, spec, rng):
    data = bytearray(template)
    pid = shiny_pid(tid, sid, NATURES.index(spec["nature"]), spec["ability_slot"],
                    spec["gender_ratio"], rng)
    struct.pack_into("<IH", data, 0, pid, 0)
    struct.pack_into("<HHHHI", data, 0x08, spec["species"], spec["item"], tid, sid,
                     EXP_AT_100[spec["growth"]])
    data[0x14] = 255                    # friendship
    data[0x15] = spec["ability_slot"]
    data[0x16] = 0                      # markings
    data[0x18:0x1E] = bytes(spec["evs"])
    data[0x1E:0x28] = bytes(10)         # contest stats, ribbons
    moves = spec["moves"]
    struct.pack_into("<4H", data, 0x28, *(m for m, _ in moves))
    data[0x30:0x34] = bytes(pp * 8 // 5 for _, pp in moves)  # max PP with 3 PP Ups
    data[0x34:0x38] = bytes([3] * 4)
    struct.pack_into("<I", data, 0x38, 0x3FFFFFFF)          # all IVs 31, not egg/nicknamed
    data[0x3C:0x40] = bytes(4)
    data[0x40] = 0                      # male, form 0
    data[0x41] = 0                      # no hidden-ability flag
    struct.pack_into("<H", data, 0x42, spec["ability"])
    data[0x48:0x5E] = encode_name(spec["name"])
    data[0x83] = ITEM_POKE_BALL
    data[0x84] = (data[0x84] & 0x80) | 100  # met level 100, keep OT gender
    data[0x86] = ITEM_POKE_BALL
    return encrypt(data), pid


def main(src, dst, box):
    box = int(box) - 1
    sav = bytearray(open(src, "rb").read())
    valid = [(n, b) for b in PARTITIONS for n, ok in [block_info(sav, b)] if ok]
    _, base = max(valid)
    tid, sid = struct.unpack_from("<HH", sav, base + TRAINER_IDS)
    storage = base + STORAGE_START

    template = None
    for slot in range(18 * BOX_SLOTS):
        off = storage + slot // BOX_SLOTS * BOX_SIZE + slot % BOX_SLOTS * BOX_MON_SIZE
        raw = sav[off:off + BOX_MON_SIZE]
        if raw[:8] == bytes(8):
            continue
        data, ok = decrypt(raw)
        if ok and struct.unpack_from("<HH", data, 0x0C) == (tid, sid):
            template = data
            break
    if template is None:
        raise SystemExit("no Pokemon caught by the player to use as a template")

    free = [i for i in range(BOX_SLOTS)
            if sav[storage + box * BOX_SIZE + i * BOX_MON_SIZE:][:8] == bytes(8)]
    if len(free) < len(POKEMON):
        raise SystemExit(f"box {box + 1} has only {len(free)} free slots")

    rng = random.Random()
    for spec, slot in zip(POKEMON, free):
        raw, pid = build(template, tid, sid, spec, rng)
        off = storage + box * BOX_SIZE + slot * BOX_MON_SIZE
        sav[off:off + BOX_MON_SIZE] = raw
        print(f"{spec['name']}: box {box + 1} slot {slot + 1}, PID {pid:08x}, {spec['nature']}")

    footer = storage + STORAGE_SIZE - FOOTER_SIZE
    struct.pack_into("<H", sav, footer + 0xE, crc16_ccitt(sav[storage:footer]))
    open(dst, "wb").write(sav)


if __name__ == "__main__":
    main(*sys.argv[1:4])

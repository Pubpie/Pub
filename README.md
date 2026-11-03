# Origin HeartGold save edit

- `save/Origin_HeartGold_original.sav` – the original save
- `save/Origin_HeartGold_mint_spelltag_abilitypatch.sav` – the edited save:
  - Items pocket: Spell Tag x99, Gold Bottle Cap x999
  - Medicine pocket: Rare Candy x999, HP Up/Protein/Iron/Carbos/Calcium/Zinc x999
  - Medicine pocket: Ability Patch x99
  - Mints are left out: the game froze with them in the bag, most likely because this
    build of the hack has no Mint items (set `ADD_MINTS = True` in the script to add them)
- `tools/origin_hg_bag_edit.py IN.sav OUT.sav` – the script that makes the edit

The Medicine pocket holds only 40 slots. To change what is added or removed,
edit `WANTED` / `REMOVE` in the script and run it again on the original save.

## Freeze report (savestate `.ml1`)

The frozen melonDS savestate still holds a healthy in-game save (Hall of Fame done,
both partitions pass their checksums, bag and party in memory match the save). The game
froze during the Molly / Entei statue event, while the Medicine pocket was completely full (40/40).

- `save/Origin_HeartGold_latest_from_state.sav` – last in-game save, pulled from the savestate as-is
- `save/Origin_HeartGold_latest_fixed.sav` – same save with 4 free Medicine slots (Potion,
  Moomoo Milk, Lava Cookie and Old Gateau removed)
- `tools/extract_melonds_save.py STATE.ml1 OUT.sav` – pulls the save out of a melonDS savestate
- `tools/free_medicine_slots.py IN.sav OUT.sav` – frees the Medicine slots

## Progress recovered from the savestate's live memory

The savestate's RAM holds about 11 more hours of play than its in-game save (43:47 vs 32:57).

- `save/Origin_HeartGold_43h47m.sav` – **newest**: live progress from the savestate (play time
  43:47, 123 Pokémon in the PC, all checksums valid), with Moomoo Milk, Lava Cookie and Old Gateau
  removed so the Medicine pocket has 3 free slots
- `tools/melonds_state_to_sav.py STATE.ml1 OUT.sav` – builds a .sav from a savestate's live memory

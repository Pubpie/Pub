# Origin HeartGold save edit

- `save/Origin_HeartGold_original.sav` – the original save
- `save/Origin_HeartGold_mint_spelltag_abilitypatch.sav` – the edited save:
  - Items pocket: Spell Tag x99, Gold Bottle Cap x999
  - Medicine pocket: Rare Candy x999, HP Up/Protein/Iron/Carbos/Calcium/Zinc x999
  - Medicine pocket: Ability Patch x99 and 15 Mints x99 (Adamant, Jolly, Modest, Timid,
    Bold, Impish, Calm, Careful, Brave, Quiet, Relaxed, Sassy, Hasty, Naive, Naughty)
- `tools/origin_hg_bag_edit.py IN.sav OUT.sav` – the script that makes the edit

The Medicine pocket holds 40 slots and only 16 were free, so not all 21 Mints fit.
To get different Mints, edit `WANTED` in the script and run it again.

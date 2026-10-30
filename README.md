# Origin HeartGold save edit

- `save/Origin_HeartGold_original.sav` – the original save
- `save/Origin_HeartGold_mint_spelltag_abilitypatch.sav` – the edited save:
  - Items pocket: Spell Tag x99, Gold Bottle Cap x999
  - Medicine pocket: Rare Candy x999, HP Up/Protein/Iron/Carbos/Calcium/Zinc x999
  - Medicine pocket: Ability Patch x99 and all 21 Mints x99
  - Removed from Medicine pocket to make room: Ice Heal, Fresh Water, Energy Powder,
    Energy Root, Heal Powder, Revival Herb (one of each)
- `tools/origin_hg_bag_edit.py IN.sav OUT.sav` – the script that makes the edit

The Medicine pocket holds only 40 slots. To change what is added or removed,
edit `WANTED` / `REMOVE` in the script and run it again on the original save.

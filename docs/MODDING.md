# Modding guide

How to change things in this game, safely. Read the "Rules" first — getting
them wrong is how the party got corrupted earlier.

---

## 1. Rules (the short version)

1. **Edit `map.json` and `scripts.inc`. Never edit `events.inc` or
   `header.inc`** — those are generated from `map.json` at build time.
2. **Never write to a `BoxPokemon` by hand.** It's encrypted, and its checksum
   is verified. Use the game's own `givemon` script command (`ScrCmd_createmon`)
   or `CreateMon()`. If you do edit memory, see `docs/ARCHITECTURE.md`.
3. **Level is not a field you set.** It's derived from EXP
   (`GetLevelFromMonExp`), and every stat is recomputed by `CalculateMonStats`
   from base stats + IVs + EVs + nature. Change those inputs instead.
4. **Stats are already at the cap.** Lv100 + 31 IVs + 252 EVs is the maximum
   the formula can produce. Writing 999 into a stat field does nothing — the
   game recomputes it.
5. **Bag slots:** 30 items / 16 balls / 30 key items. One stack caps at 999
   (`MAX_BAG_ITEM_CAPACITY`).
6. **Money caps at 999,999** (`MAX_MONEY` in `include/money.h`).
7. **Always rebuild and check the build exit code.** `make -j4` then look for
   `EXIT=0` in your log.
8. **Savestates are ROM-build-specific.** After a rebuild, old `.ss1` files may
   not load — start a fresh game and save a new one.

---

## 2. Change or give a moveset

### Give a Pokemon with specific moves

```
givemon SPECIES_MEWTWO_ARMORED, 100, , , NATURE_HARDY, , , 252, 252, 252, 252, 252, 252, 31, 31, 31, 31, 31, 31, MOVE_PSYSTRIKE, MOVE_ICE_BEAM, MOVE_THUNDERBOLT, MOVE_AURA_SPHERE
```

Positional arguments:

| # | Field | What to put |
|---|---|---|
| 1 | species | `SPECIES_*` constant |
| 2 | level | 1–100 |
| 3 | item | held item or blank |
| 4 | ball | ball type or blank |
| 5 | nature | `NATURE_*` (or blank = random) |
| 6 | abilityNum | ability index or blank |
| 7 | gender | or blank |
| 8–13 | EVs (HP, Atk, Def, Spe, SpAtk, SpDef) | 0–252, blank = 0 |
| 14–19 | IVs (same order) | 0–31, blank = random |
| 20–23 | moves | `MOVE_*` constants |

Notes:

* **Leave a move slot blank and pass `MOVE_DEFAULT`** (the macro default) and the
  game fills it from that species' level-up learnset. Omitting all four gives a
  natural moveset.
* Signature moves live in the species' learnset in
  `src/data/pokemon/all_learnables.json`.
* **PP**: `givemon` has no PP parameter. `ScriptGiveMonParameterized`
  (`src/script_pokemon_util.c`) sets `MON_DATA_PP_BONUSES = 0xFF` (three PP Ups
  per slot, +60%) and refreshes current PP, so gifted mons start full.

### Regenerate all the gift movesets (143 mons)

```bash
python3 gen_gift.py     # rewrites the givemon block in scripts.inc
make -j4
```

`gen_gift.py` reads `src/data/moves_info.h` (power, type, category, accuracy),
`src/data/pokemon/all_learnables.json` (learnsets) and the species tables,
then picks signature moves first and the best STAB/coverage after, scoring by
power + STAB + stronger attack category − inaccuracy penalty (×2). Recharge /
two-turn / self-KO moves (Hyper Beam, Giga Impact, Explosion, …) are excluded.

---

## 3. Give items, money, flags

```
giveitem ITEM_MASTER_BALL, 999
giveitem ITEM_FULL_RESTORE, 999
giveitem ITEM_MACH_BIKE, 1
addmoney 999999
setflag FLAG_SYS_POKEDEX_GET
setflag FLAG_SYS_B_DASH        @ running shoes
setflag FLAG_SYS_NATIONAL_DEX
```

Field moves are badge-gated (`src/field_move.c`), so for an all-access start:

```
setflag FLAG_BADGE01_GET   ..  FLAG_BADGE08_GET
giveitem ITEM_HM01, 1      ..  ITEM_HM08, 1
```

Constants: items in `include/constants/items.h`, flags in
`include/constants/flags.h`, money cap in `include/money.h`.

---

## 4. Edit a script / add an event

* Scripts live in `data/maps/<Map>/scripts.inc` and are plain script macros
  (`msgbox`, `lock/faceplayer`, `warp`, `setflag`, `trainerbattle_single`, …).
* Talk to an NPC: give the object event a script label in `map.json`, then
  define it in `scripts.inc`.
* Battles: `trainerbattle_single TRAINER_<NAME>` — trainers are defined in
  `src/data/trainers.h` (and generated tables under `src/data/`).
* Text: `String`/`COMPOUND_STRING` in script text blocks; the charmap is
  `charmap.txt` (`\p` = newline, `\l` = line break).

---

## 5. New or moved map

1. Edit `data/maps/<Map>/map.json` (layout, music, connections, objects, warps).
2. Add or update the layout in `data/layouts/layouts.json` (`width`,
   `height`, `primary_tileset`, `secondary_tileset`).
3. Ensure the map is listed in `data/maps/map_groups.json` under a group, and
   has a `MAP_*` constant in `include/constants/map_groups.h`.
4. Put scripts in `scripts.inc`.
5. Run `python3 tools/map_index.py` to refresh the docs, then `make -j4`.

Generated index: `docs/maps/INDEX.md` (human table) and
`docs/maps/map_index.json` (machine-readable: warps, objects, items, trainers,
given Pokemon per map).

---

## 6. Questions agents (and humans) will ask

**"Where do I go?"** — `docs/maps/INDEX.md` lists every map with its warps,
items and trainers. `docs/maps/map_index.json` is the same data in JSON.

**"How do I give myself a Pokemon?"** — use the `givemon` script command in a
script (see section 2), or the in-game debug menu: hold `S` (R) + `Enter`
(Start) in the overworld.

**"Why is my Pokemon a Bad Egg / an Egg / stats 0?"** — its checksum failed, so
the game rewrote it. See the encryption notes in `docs/ARCHITECTURE.md`:
party `BoxPokemon` is `personality ^ otId`-encrypted, and the checksum at
offset 28 is the sum over the *decrypted* words of `word + (word >> 16)`.

**"Why didn't my save persist?"** — the game never writes `pokeemerald.sav`.
Use the emulator savestate (slot 1) — `python3 ~/pokemon-wot/pokemon.sh save`.

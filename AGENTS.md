# AGENTS.md

Pokemon Wishes of Tomorrow — a pokeemerald **decomp hack** (base:
[pret/pokeemerald](https://github.com/pret/pokeemerald)). A C codebase compiled
to a GBA ROM (`pokeemerald.gba`, 32 MB). Everything you need is in this repo;
this file is the short version. **Read `docs/ARCHITECTURE.md` and
`docs/MODDING.md` for detail.**

## Agent environment

* Working directory of the running game: `~/pokemon-wot`
* Playable build: `~/pokemon-wot/Wishes-Game/pokeemerald.gba`
* Launcher: `~/pokemon-wot/pokemon.sh`
* Display: `:0`, 1920×1080
* The researcher/author does not want binary "checkpoint" saves. The ROM's flash
  save (`pokeemerald.sav`) **has never been written** — progress lives in mGBA
  savestates. See "Persistence".

## Build

```bash
make -j4          # ~2-5 min. Must end with EXIT=0 in your log.
python3 tools/map_index.py    # regenerate docs/maps/INDEX.md + map_index.json
python3 gen_gift.py           # regenerate the gift NPC script
```

Toolchain: `arm-none-eabi-gcc` 13.2, `make`, `python3`. No `node`/`npm` needed.

## Facts you must know (or you will corrupt the game)

1. **Party `BoxPokemon` is encrypted in memory** (`personality ^ otId` over 12
   `u32` at offset 32). The checksum at offset 28 is the sum over the
   **decrypted** words of `word + (word >> 16)`. A wrong checksum makes the game
   mark the mon a **Bad Egg** and rewrite its slot.
2. **Level is not authoritative.** It is derived from EXP
   (`GetLevelFromMonExp`); `CalculateMonStats` recomputes every stat from
   base + IV + EV + nature. Change those inputs, not the stat fields.
3. **Stats are always at the cap when IV=31, EV=252, Lv100.** No higher value
   exists.
4. **`givemon` has no PP parameter.** `ScriptGiveMonParameterized`
   (`src/script_pokemon_util.c`) sets `MON_DATA_PP_BONUSES = 0xFF` and refreshes
   current PP, so gifted mons start full.
5. **Bag limits:** 30 item slots / 16 ball slots / 30 key items; one stack caps
   at 999. **Money caps at 999,999.**
6. **Field moves are badge-gated** (`src/field_move.c`) — Cut needs
   `FLAG_BADGE01_GET`. The gift grants all 8 badges and all 8 HMs.
7. **mGBA's GDB stub freezes the game** while a client is attached. Never run
   `ai_server.py` as a daemon. It also serves exactly one client and wedges.
   If the stub writes are needed, prefer the in-game `givemon` script path.
8. **`givemon` move slots default to `MOVE_DEFAULT`** ("fill from learnset").
   Omitting moves entirely yields a natural moveset.

## Persistence

* Playable directory (ext4, real disk): `~/pokemon-wot/`
* ROM + `.elf` (symbols) + `.sav` + savestate slot 1: `~/pokemon-wot/Wishes-Game/`
* Savestate history: `~/pokemon-wot/states/` (30 kept)
* Mirror copies, auto-written on `save` and every 120 s:
  `/media/mint/WDC_WD10EZRX_932G/pokemon-wot/backups/` (1TB, keep 5) and
  `/media/mint/6CF26779F2674684/pokemon-wot-backups/` (NTFS, keep 5)
* Source tree (this repo): `/media/mint/WDC_WD10EZRX_932G/pokemon-wot/Wishes-Game/`

```bash
cd ~/pokemon-wot
./pokemon.sh start      # launch mGBA + auto-backup loop, load last state
./pokemon.sh save       # save state now (also every 120 s automatically)
./pokemon.sh stop       # save + mirror + quit
./pokemon.sh history    # list saved states
./pokemon.sh status     # processes, state file, whether the save is blank
```

Controls: `X` = A, `Z` = B, `Enter` = Start, `A`/`S` = L/R, `Shift+F1`/`F1` =
save/load state slot 1, `Ctrl+R` reset, **`S` + `Enter`** = overworld debug
menu, `Select` in battle = battle debug menu.

If the screen is black, look at the title bar: **no fps counter = paused**
(mGBA pauses on focus loss; `pauseOnFocusLost=0` is set in
`~/.config/mgba/config.ini`).

## Where things are

| Topic | Read / edit |
|---|---|
| How to mod | `docs/MODDING.md` |
| Engine, build, saves, encryption | `docs/ARCHITECTURE.md` |
| Every map: warps, items, trainers | `docs/maps/INDEX.md` / `docs/maps/map_index.json` |
| Build config | `include/config/*.h`, `include/constants/global.h` |
| Moves data | `src/data/moves_info.h` |
| Learnsets | `src/data/pokemon/all_learnables.json` |
| Species / base stats / flags | `src/data/pokemon/species_info/*.h` |
| DEV gift NPC (143 maxed legendaries) | `data/maps/LittlerootTown_BrendansHouse_2F/scripts.inc` (`PlayersBedroom_EventScript_DevNpc`), regenerate with `gen_gift.py` |
| Wishes of Tomorrow story/canon | `Wishes_of_Tomorrow_Story_Canon.md`, `wishes_of_tomorrow_backlog_handoff.md` |
| Upstream build docs | `README.upstream.md`, `FEATURES.md`, `INSTALL.md` |

## Story progression (authoritative, from the scripts)

1. **Munen Village** (custom start) → **Munen Tunnel**: Nugget, Max Ether,
   TM30 (Shadow Ball), TM24 (Thunderbolt), **Carved Mask** — gated on beating
   the **Tunnel Captain** (`FLAG_POMPEII_GENERAL_RETREATED`). The mask is the
   **Oni Mask** (`FLAG_ONI_MASK_WORN`): while worn, Team Mutrid goons skip you.
2. **Ashlands** (Old Prophet's House): the **Catalpa Bow**, unlocked after the
   Fentanyl quest line.
3. **National Park**: boatman → Tradewind Town; two goons (skipped while masked);
   gravesite — **use the Catalpa Bow from the bag next to the grave** to cross
   into the **Distortion World**. Cross at `VAR_QUEST_FATHERS_WISH == 3` to
   complete the Grandfather's Wish quest.

## Repo conventions

* Edit `map.json` and `scripts.inc`. **Never hand-edit `events.inc` or
  `header.inc`** — they are generated from `map.json`.
* Keep mass changes in a generator (`gen_gift.py`, `tools/map_index.py`) so
  they can be re-run, rather than editing 143 lines by hand.
* One system per file; constants in `include/constants/`, behaviour flags in
  `include/config/`.
* If it does not compile, the change is wrong. Do not special-case around it.

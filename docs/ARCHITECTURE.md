# Architecture

Pokemon Wishes of Tomorrow is a **pokeemerald decomp** (base: pret/pokeemerald).
Everything is C, compiled with `arm-none-eabi-gcc` into a 32 MB GBA ROM.

```
            ┌─────────────────────────── compile ───────────────────────────┐
 make -j4   │ scaninc → preproc → arm-none-eabi-as → arm-none-eabi-ld → gbafix │
            └─────────────────────────────────────────────────────────────────┘
                                 pokeemerald.gba (32 MB)
```

## Build

```bash
make -j4              # debug build (debug menu ON - see below)
make release          # stripped build (debug menu OFF)
```

Key Makefile flags: `GAME_VERSION ?= EMERALD`, `TITLE ?= POKEMON EMER`,
`GAME_CODE ?= BPEE`, `BUILD_NAME ?= emerald`, `MAP_VERSION ?= emerald`.
`DEBUG ?= 0`. A normal `make` compiles with `-DTESTING` (see `build.log`).

Output: `pokeemerald.gba` + `pokeemerald.elf` (symbols) + `pokeemerald.map`
(linker map). The ELF is what `nm` reads to get addresses like `gPlayerParty`.

## Directory map

| Path | What lives there |
|---|---|
| `src/` | ~389 C files - the game. One file per system: `pokemon.c`, `battle_*.c`, `field*.c`, ... |
| `include/` | headers + `include/constants/` and `include/config/` |
| `asm/` + `asm/macros/` | assembler and the script macro library |
| `data/maps/` | **1021 maps** - each `map.json` + `events.inc` + `header.inc` + `scripts.inc` |
| `data/layouts/` | 863 tile layouts (`layouts.json` + per-layout `map.bin`/`border.bin`) |
| `data/pokemon/` | species info, learnsets, experience tables, Pokedex |
| `data/moves_info.h` | move data (power, type, category, accuracy) |
| `src/data/` | misc tables (items, trainers, wild encounters) |
| `graphics/` | sprites, tilesets, palettes |
| `sound/` | audio |
| `tools/` | build tooling + `tools/map_index.py` (produces the docs here) |
| `dev_scripts/` | build helpers |
| `test/` | unit tests |

## Core loops

* **Overworld** — `FieldMain` → `HandleInput` → `UpdateTasks` / `UpdateNPCs`.
* **Battle** — `src/battle_main.c`, `src/battle_script_commands.c`,
  `src/battle_ai*.c`. The battle state machine runs `gBattlescripts[]`
  opcode handlers.
* **Save** — `SaveBlock1` (game), `SaveBlock2` (player/geometry), `SaveBlock3`
  (meta). Pointers live at `gSaveBlock1Ptr` / `gSaveBlock2Ptr` in EWRAM.
* **Pokemon data** — `struct Pokemon` in `include/pokemon.h`:
  `BoxPokemon` (80 bytes, encrypted) + cleartext stats at the tail.

## The encryption you must not break

Party `BoxPokemon` is stored **encrypted** in EWRAM. `GetBoxMonData3`
(`src/pokemon.c:2520`) decrypts on read; `:3001` re-encrypts on write. Key is
`personality ^ otId` applied to 12 `u32` words at `BoxPokemon + 32`.

The stored checksum (`BoxPokemon + 28`) is the sum over the **decrypted**
words of `word + (word >> 16)`, truncated to 16 bits
(`CalculateBoxMonChecksumDecrypt`, `src/pokemon.c:1779`). A wrong checksum
makes the game flag the mon as a **Bad Egg** and rewrite its slot.

Level is *derived* from EXP (`GetLevelFromMonExp`); `CalculateMonStats`
(`src/pokemon.c:1805`) recomputes every stat from base + IV + EV + nature.
So to change a mon for real, change EXP/IVs/EVs and let the game do the maths.

## Flags that change behaviour

| Flag / macro | Effect |
|---|---|
| `DEBUG_OVERWORLD_MENU` | overworld debug menu (hold R + Start) |
| `DEBUG_BATTLE_MENU` | in-battle debug menu (Select) |
| `DISABLED_ON_RELEASE` | TRUE unless `-DRELEASE` is passed |
| `B_FRIENDSHIP_BOOST` | stat boost from friendship (currently FALSE) |
| `FLAG_BADGE01_GET` … `FLAG_BADGE08_GET` | each gates a field move |

## Map system

Each map has `map.json` (name, layout, music, connections, event lists),
`events.inc` (generated object/warp tables — **do not edit by hand**, it is
generated from `map.json`), `header.inc` (also generated) and `scripts.inc`
(the hand-written part).

`data/maps/map_groups.json` groups maps into 76 groups; `include/constants/
map_groups.h` gives each a `MAP_*` constant.

## Where the "interesting" custom content is

| What | Where |
|---|---|
| DEV gift NPC (143 maxed legendaries) | `data/maps/LittlerootTown_BrendansHouse_2F/scripts.inc`, label `PlayersBedroom_EventScript_DevNpc` — regenerate with `gen_gift.py` |
| Munen region (custom) | `MunenVillage`, `MunenTunnel`, `MunenLake`, `MunenLabAct2`, `MunenHomeAct2`, `Munen_village_2` |
| Act 2 National Park | `NationalParkAct2` |
| Armored Mewtwo (form) | `SPECIES_MEWTWO_ARMORED` = 1573, `src/data/pokemon/species_info/gen_1_families.h` |

## Tooling in this repo

| Tool | Purpose |
|---|---|
| `tools/map_index.py` | regenerates `docs/maps/INDEX.md` + `map_index.json` |
| `gen_gift.py` | regenerates the DEV gift NPC script |
| `dev_scripts/` | upstream build helpers |

## Repo conventions

* Edit `map.json` / `scripts.inc`, never the generated `events.inc` /
  `header.inc`.
* Keep mass changes in the generator (`gen_gift.py`) so they can be re-run
  instead of hand-edited.
* The build is the ground truth: if it does not compile, the change is wrong.
* One system per file; new constants go in `include/constants/`.

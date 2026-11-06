# Pokemon Wishes of Tomorrow

A **pokeemerald decomp hack** (base: [pret/pokeemerald](https://github.com/pret/pokeemerald)),
with a custom region, an expanded map set, and a dev gift that hands the player
a full max-stat legendary party.

> **A note on persistence.** The ROM's flash save has never written a byte
> (`pokeemerald.sav` stays blank), so in-game progress is **not** saved by the
> game. Progress is kept in **mGBA savestates** (slot 1), auto-saved every 2
> minutes and mirrored to several drives. See `~/pokemon-wot/README.md` for the
> launcher, and the section "Save format" below.

---

## Quick start

```bash
sudo apt install gcc-arm-none-eabi make pkg-config

make -j4                 # debug build -> pokeemerald.gba
make release             # release build (debug menu off)
```

Then open the ROM in mGBA (or VBA-M):

```bash
mgba-qt pokeemerald.gba
```

In game: **New Game**, then talk to the **DEV NPC** in your bedroom
(upstairs, Littleroot Town). It hands you the maxed party described in
[`docs/MODDING.md`](docs/MODDING.md).

## Playing it

```bash
cd ~/pokemon-wot
./pokemon.sh start      # mGBA + auto-backup loop, loads the last state
./pokemon.sh save       # save a state now (also every 2 min automatically)
./pokemon.sh stop       # save + shut down cleanly
./pokemon.sh history    # list saved states
./pokemon.sh status     # what's running, where the save lives
```

| Keys | Action |
|---|---|
| `Shift+F1` / `F1` | save / load emulator state slot 1 |
| `Ctrl+R` | reset the game |
| `X` `Z` `Enter` | A / B / Start |
| `A` `S` | L / R |
| **`S` + `Enter`** | overworld debug menu (hold R, press Start) |
| `Select` in battle | battle debug menu |

## The gift

One conversation with the DEV NPC gives you:

* **143 species** — every legendary, mythical and Ultra Beast the hack defines
  (6 in the party, 137 in the PC boxes)
* each **Lv100, 31 IVs, 252 EVs in all six stats, neutral nature, max PP**
* **signature moves first** (Psystrike, Dragon Ascent, Aeroblast, Sacred Fire,
  Origin Pulse, Precipice Blades, Roar of Time, Sunsteel Strike, Behemoth Blade…)
  then the strongest STAB/coverage from that species' own learnset
* **999,999 money** (the cap), Master/Ultra/Great/Quick/Dusk/Net/Timer Balls ×999
* Full Restore / Max Potion / Max Revive / Max Elixir / Max Ether / Full Heal ×999
* Pokédex + National Dex + Running Shoes
* **all 8 badges and all 8 HMs** — so Cut, Flash, Rock Smash, Surf, Strength,
  Waterfall, Dive and Fly all work immediately
* **Groudon starts out knowing Cut**

Regenerate it any time: `python3 gen_gift.py && make -j4`.

## The party

| Slot | Pokemon | Moves | Notes |
|---|---|---|---|
| 1 | Armored Mewtwo | Psystrike / Future Sight / Thunderbolt / Ice Beam | fastest in the party |
| 2 | Rayquaza | Dragon Ascent / Extreme Speed / Outrage / Dragon Claw | raw damage pick |
| 3 | Lugia | Aeroblast / Brave Bird / Future Sight / Double-Edge | special wall |
| 4 | Ho-Oh | Sacred Fire / Brave Bird / Flare Blitz / Double-Edge | physical wall |
| 5 | Kyogre | Origin Pulse / Hydro Pump / Thunderbolt / Ice Beam | special attacker |
| 6 | Groudon | Precipice Blades / Earthquake / Eruption / **Cut** | Cut user |

All four of Mewtwo/Rayquaza/Lugia/Ho-Oh tie at **2059 total** on this build
(Lv100, 31 IVs, 252 EVs, Hardy).

## Where to go

Starting map: **Munen Village** (custom Munen region, not the standard Emerald
start).

1. **Munen Tunnel** — Nugget, Max Ether, **TM30 (Shadow Ball)**, **TM24
   (Thunderbolt)**, and the **Carved Mask**. The mask is gated: you must beat the
   **Tunnel Captain** first, which sets `FLAG_POMPEII_GENERAL_RETREATED`. The
   mask is the **Oni Mask** — while worn, Team Mutrid goons don't battle you.
2. **Ashlands** (Old Prophet's House) — the **Catalpa Bow** item ball, unlocked
   after the Fentanyl quest line.
3. **National Park** — boatman to Tradewind Town, two goons (skippable with the
   Oni Mask), a grave watcher, and the **gravesite**: use the Catalpa Bow from
   your bag while standing at the grave to cross into the **Distortion World**
   (the Act 2 story beat). Cross while `VAR_QUEST_FATHERS_WISH == 3` to complete
   the Grandfather's Wish quest.

Full map data for all 1016 maps: [`docs/maps/INDEX.md`](docs/maps/INDEX.md).

## Modifying it

* [`docs/MODDING.md`](docs/MODDING.md) — how to edit movesets, items, scripts,
  flags, maps and the gift; and the "don't break the save" rules.
* [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — build system, core loops,
  the BoxPokemon encryption + checksum, where everything lives.
* [`docs/maps/INDEX.md`](docs/maps/INDEX.md) — generated index of every map,
  its warps, items, trainers and given Pokemon.

**Save format (read this before touching save code).** `pokeemerald.sav` is a
128 KiB flash image that the game never writes. Progress is kept in mGBA
savestates instead. Party `BoxPokemon` is stored **encrypted** (`personality ^
otId` over 12 `u32` at offset 32) and the checksum at offset 28 is the sum over
the *decrypted* words of `word + (word >> 16)` — get either wrong and the game
marks the mon a Bad Egg and rewrites it.

## Configuration

All of this is in `include/config/*.h` and `include/constants/global.h`. The
useful knobs:

| Setting | Where | Effect |
|---|---|---|
| `DEBUG_OVERWORLD_MENU` | `include/config/debug.h` | overworld debug menu (R + Start) |
| `DEBUG_BATTLE_MENU` | `include/config/debug.h` | battle debug menu (Select) |
| `B_FRIENDSHIP_BOOST` | `include/config/battle.h` | friendship stat boost |
| `MAX_PER_STAT_EVS` | `include/constants/pokemon.h` | 252 |
| `MAX_PER_STAT_IVS` | `include/constants/pokemon.h` | 31 |
| `MAX_MONEY` | `include/money.h` | 999,999 |
| `MAX_BAG_ITEM_CAPACITY` | `include/constants/items.h` | 999 per stack |

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Short version: edit `map.json` /
`scripts.inc`, never the generated `events.inc` / `header.inc`; keep mass
changes inside a generator script so they can be re-run; and always run
`make -j4` — a build that doesn't compile is a wrong change.

## Credits

Base decomp: [pret/pokeemerald](https://github.com/pret/pokeemerald) —
see `CREDITS.md` and `FEATURES.md` (the upstream build docs are preserved in
`README.upstream.md`). Hack-specific content by the ROM's author
(`Wishes_of_Tomorrow_Story_Canon.md`, `wishes_of_tomorrow_backlog_handoff.md`).

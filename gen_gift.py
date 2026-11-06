#!/usr/bin/env python3
"""
Generate the DEV gift NPC's givemon list.

For every legendary / mythical / Ultra Beast the hack defines, give it:
  * its signature move(s) where the ROM actually has them (validated by name,
    so a typo is dropped instead of breaking the build)
  * then the strongest STAB and coverage moves from its real learnset
  * Lv100, 31 IVs, 252 EVs everywhere, neutral nature

Writes the block into data/maps/LittlerootTown_BrendansHouse_2F/scripts.inc.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)


def num(expr, default=0):
    """Read a value out of a C expression like 'X >= GEN_6 ? 110 : 120'.

    The modern branch (after '?') is what this build uses, so prefer it.
    """
    if expr is None:
        return default
    m = re.search(r'\?\s*(\d+)\s*:', str(expr))
    if m:
        return int(m.group(1))
    m = re.search(r'(\d+)', str(expr))
    return int(m.group(1)) if m else default


# ---------------------------------------------------------------- move table
mt = open('src/data/moves_info.h', errors='ignore').read()
MOVES = {}
for m in re.finditer(r'\[MOVE_([A-Z0-9_]+)\]\s*=\s*\{', mt):
    name = m.group(1)
    start = m.end(); depth = 1; j = start
    while j < len(mt) and depth:
        c = mt[j]
        if c == '{': depth += 1
        elif c == '}': depth -= 1
        j += 1
    blk = mt[start:j]
    pw = re.search(r'\.power\s*=\s*([^,\n]+)', blk)
    ty = re.search(r'\.type\s*=\s*TYPE_([A-Z0-9_]+)', blk)
    ct = re.search(r'\.category\s*=\s*DAMAGE_CATEGORY_([A-Z]+)', blk)
    ac = re.search(r'\.accuracy\s*=\s*([^,\n]+)', blk)
    MOVES[name] = {
        "power": num(pw.group(1)) if pw else 0,
        "type": ty.group(1) if ty else None,
        "cat": ct.group(1) if ct else "STATUS",
        "acc": num(ac.group(1), 100) if ac else 100,
    }
print(f"moves parsed: {len(MOVES)}")

# ------------------------------------------------------------- signature map
SIGNATURE = {
    # gen 1
    "MEWTWO": ["PSYSTRIKE"], "MEWTWO_ARMORED": ["PSYSTRIKE"],
    "MEW": ["PSYCHIC", "AURA_SPHERE"],
    "ARTICUNO": ["BLIZZARD", "ICE_BEAM"], "ZAPDOS": ["THUNDER", "ZAP_CANNON"],
    "MOLTRES": ["FIRE_BLAST", "OVERHEAT"],
    # gen 2
    "RAIKOU": ["THUNDER", "THUNDERBOLT"], "ENTEI": ["SACRED_FIRE"],
    "SUICUNE": ["HYDRO_PUMP", "ICE_BEAM"], "LUGIA": ["AEROBLAST"],
    "HO_OH": ["SACRED_FIRE", "BRAVE_BIRD"], "CELEBI": ["FUTURE_SIGHT", "LEAF_STORM"],
    # gen 3
    "REGIROCK": ["STONE_EDGE", "ROCK_SLIDE"], "REGICE": ["BLIZZARD", "ICE_BEAM"],
    "REGISTEEL": ["FLASH_CANNON", "IRON_HEAD"],
    "LATIAS": ["MIST_BALL", "PSYCHIC"], "LATIOS": ["LUSTER_PURGE", "DRAGON_CLAW"],
    "KYOGRE": ["ORIGIN_PULSE", "HYDRO_PUMP"], "GROUDON": ["PRECIPICE_BLADES", "EARTHQUAKE"],
    "RAYQUAZA": ["DRAGON_ASCENT", "EXTREME_SPEED"],
    "JIRACHI": ["DOOM_DESIRE", "PSYCHIC"],
    "DEOXYS": ["PSYCHO_BOOST"], "DEOXYS_NORMAL": ["PSYCHO_BOOST"],
    "DEOXYS_ATTACK": ["PSYCHO_BOOST"], "DEOXYS_DEFENSE": ["PSYCHO_BOOST"],
    "DEOXYS_SPEED": ["PSYCHO_BOOST"],
    # gen 4
    "UXIE": ["EXTRASENSORY", "PSYCHIC"], "MESPRIT": ["EXTRASENSORY", "PSYCHIC"],
    "AZELF": ["EXTRASENSORY", "PSYCHIC"],
    "DIALGA": ["ROAR_OF_TIME"], "PALKIA": ["SPACIAL_REND"],
    "GIRATINA": ["SHADOW_FORCE"], "HEATRAN": ["MAGMA_STORM"],
    "REGIGIGAS": ["CRUSH_GRIP", "GIGA_IMPACT"],
    "CRESSELIA": ["MIST_BALL", "PSYCHIC"], "DARKRAI": ["DARK_VOID"],
    "SHAYMIN": ["SEED_FLARE"], "ARCEUS": ["JUDGMENT"],
    "MANAPHY": ["SURF", "ICE_BEAM"], "PHIONE": ["SURF", "ICE_BEAM"],
    # gen 5
    "VICTINI": ["V_CREATE"], "RESHIRAM": ["BLUE_FLARE", "FUSION_FLARE"],
    "ZEKROM": ["BOLT_STRIKE", "FUSION_BOLT"], "KYUREM": ["GLACIATE", "ICE_BEAM"],
    "COBALION": ["SACRED_SWORD", "IRON_HEAD"], "TERRAKION": ["SACRED_SWORD", "STONE_EDGE"],
    "VIRIZION": ["SACRED_SWORD", "LEAF_BLADE"], "KELDEO": ["SECRET_SWORD"],
    "MELOETTA": ["RELIC_SONG", "PSYCHIC"], "GENESECT": ["TECHNO_BLAST"],
    "TORNADUS": ["HURRICANE", "AIR_SLASH"], "THUNDURUS": ["THUNDER", "DISCHARGE"],
    "LANDORUS": ["EARTHQUAKE", "STONE_EDGE"],
    # gen 6
    "XERNEAS": ["GEOMANCY", "MOONBLAST"], "YVELTAL": ["OBLIVION_WING"],
    "ZYGARDE": ["THOUSAND_ARROWS", "THOUSAND_WAVES"],
    "DIANCIE": ["DIAMOND_STORM"], "HOOPA": ["HYPERSPACE_HOLE"],
    "VOLCANION": ["STEAM_ERUPTION"],
    # gen 7
    "SOLGALEO": ["SUNSTEEL_STRIKE"], "LUNALA": ["MOONGEIST_BEAM"],
    "NECROZMA": ["PRISMATIC_LASER", "PHOTON_GEYSER"],
    "TAPU_KOKO": ["NATURES_MADNESS", "THUNDERBOLT"],
    "TAPU_LELE": ["NATURES_MADNESS", "MOONBLAST"],
    "TAPU_BULU": ["NATURES_MADNESS", "WOOD_HAMMER"],
    "TAPU_FINI": ["NATURES_MADNESS", "MOONBLAST"],
    "MARSHADOW": ["SPECTRAL_THIEF"], "ZERAORA": ["PLASMA_FISTS"],
    "MAGEARNA": ["FLEUR_CANNON"], "MELMETAL": ["DOUBLE_IRON_BASH"],
    "MELTAN": ["FLASH_CANNON"],
    # gen 8
    "ZACIAN": ["BEHEMOTH_BLADE"], "ZAMAZENTA": ["BEHEMOTH_BASH"],
    "ETERNATUS": ["DYNAMAX_CANNON"],
    "URSHIFU": ["WICKED_BLOW", "SURGING_STRIKES"], "KUBFU": ["CLOSE_COMBAT"],
    "ZARUDE": ["JUNGLE_HEALING", "DARKEST_LARIAT"],
    "REGIELEKI": ["THUNDER_CAGE", "THUNDERBOLT"], "REGIDRAGO": ["DRAGON_ENERGY"],
    "GLASTRIER": ["GLACIAL_LANCE"], "SPECTRIER": ["ASTRAL_BARRAGE"],
    # gen 9
    "KORAIDON": ["COLLISION_COURSE"], "MIRAIDON": ["ELECTRO_DRIFT"],
    "ENAMORUS": ["SPRINGTIDE_STORM"], "TERAPAGOS": ["TERA_STARSTORM"],
    "OGERPON": ["IVY_CUDGEL"], "WO_CHIEN": ["RUINATION"],
    "CHIEN_PAO": ["RUINATION"], "TING_LU": ["RUINATION"], "CHI_YU": ["RUINATION"],
}
# species name -> signature entry (strip form suffixes when needed)
def sig_for(sp):
    if sp in SIGNATURE:
        return SIGNATURE[sp]
    for suf in ("_INCARNATE", "_THERIAN", "_ORDINARY", "_RESOLUTE", "_ARIA",
                "_PIROUETTE", "_ORIGINAL", "_GMAX", "_SINGLE_STRIKE_GMAX",
                "_RAPID_STRIKE_GMAX", "_DADA", "_TERASTAL", "_STELLAR",
                "_SHADOW", "_ARMORED", "_ORIGIN", "_ALTERED", "_NORMAL",
                "_50", "_10_AURA_BREAK", "_10_POWER_CONSTRUCT",
                "_50_POWER_CONSTRUCT", "_COMPLETE", "_HERO", "_CROWNED",
                "_WHITE", "_BLACK", "_ACTIVE", "_NEUTRAL", "_DUSK_MANE",
                "_DAWN_WINGS", "_ULTRA", "_ETERNAMAX", "_ATTACK",
                "_DEFENSE", "_SPEED", "_MALE", "_FEMALE"):
        if sp.endswith(suf) and sp[:-len(suf)] in SIGNATURE:
            return SIGNATURE[sp[:-len(suf)]]
    return []

# ------------------------------------------------------------- species table
LEARN = json.load(open('src/data/pokemon/all_learnables.json'))


def learnset(sp):
    if sp in LEARN:
        return LEARN[sp]
    for suf in ("_ARMORED", "_ORIGIN", "_ALTERED", "_NORMAL", "_50", "_HERO",
                "_ACTIVE", "_NEUTRAL", "_WHITE", "_BLACK", "_CROWNED",
                "_COMPLETE", "_DUSK_MANE", "_DAWN_WINGS", "_ULTRA",
                "_ETERNAMAX", "_INCARNATE", "_THERIAN", "_ORDINARY",
                "_RESOLUTE", "_ARIA", "_PIROUETTE", "_DADA", "_TERASTAL",
                "_STELLAR", "_SHADOW", "_ATTACK", "_DEFENSE", "_SPEED",
                "_10_AURA_BREAK", "_10_POWER_CONSTRUCT",
                "_50_POWER_CONSTRUCT", "_GMAX"):
        if sp.endswith(suf) and sp[:-len(suf)] in LEARN:
            return LEARN[sp[:-len(suf)]]
    return []


st = ""
for f in glob.glob('src/data/pokemon/species_info/*.h'):
    st += open(f, errors='ignore').read() + "\n"

gift, types, bst, better = [], {}, {}, {}
for m in re.finditer(r'\[SPECIES_([A-Z0-9_]+)\]\s*=\s*\{', st):
    name = m.group(1)
    start = m.end(); depth = 1; j = start
    while j < len(st) and depth:
        c = st[j]
        if c == '{': depth += 1
        elif c == '}': depth -= 1
        j += 1
    blk = st[start:j]
    if '.isMegaEvolution = TRUE' in blk or '.isPrimalReversion = TRUE' in blk:
        continue
    if not any(k in blk for k in ('.isRestrictedLegendary = TRUE',
                                  '.isSubLegendary = TRUE',
                                  '.isMythical = TRUE',
                                  '.isUltraBeast = TRUE')):
        continue
    gift.append(name)
    tm = re.search(r'\.types\s*=\s*MON_TYPES\(([^)]*)\)', blk)
    types[name] = [t.strip().replace('TYPE_', '') for t in tm.group(1).split(',')] if tm else []
    atk = 0
    for f2 in ('baseHP', 'baseAttack', 'baseDefense', 'baseSpeed',
               'baseSpAttack', 'baseSpDefense'):
        mm = re.search(rf'\.{f2}\s*=\s*([^,\n]+)', blk)
        atk += num(mm.group(1)) if mm else 0
    bst[name] = atk
    ma = re.search(r'\.baseAttack\s*=\s*([^,\n]+)', blk)
    ms = re.search(r'\.baseSpAttack\s*=\s*([^,\n]+)', blk)
    better[name] = "PHYSICAL" if num(ma.group(1) if ma else None) >= num(ms.group(1) if ms else None) else "SPECIAL"

gift = list(dict.fromkeys(gift))
PARTY_FIRST = ["MEWTWO_ARMORED", "RAYQUAZA", "LUGIA", "HO_OH", "KYOGRE", "GROUDON"]
gift = ([g for g in PARTY_FIRST if g in gift]
        + [g for g in gift if g not in PARTY_FIRST])

# ------------------------------------------------------- choose four moves
# Never auto-fill with these: recharge / two-turn / self-KO moves are high power
# on paper and terrible in practice.
BLACKLIST = {
    "HYPER_BEAM", "GIGA_IMPACT", "SKY_ATTACK", "SOLAR_BEAM", "RAZOR_WIND",
    "SKULL_BASH", "SELF_DESTRUCT", "EXPLOSION", "MEMENTO", "HEALING_WISH",
    "LAST_RESORT", "DREAM_EATER", "SNORE", "SPIT_UP", "FISSURE", "HORN_DRILL",
    "GUILLOTINE", "SHEER_COLD", "FLY", "DIG", "DIVE", "BOUNCE",
    "PHANTOM_FORCE", "UPROAR", "BELLY_DRUM", "SPLASH", "FOCUS_PUNCH",
}


def pick_moves(sp):
    chosen = []

    def add(mv):
        mv = mv.upper()
        if mv in MOVES and MOVES[mv]["power"] > 0 and mv not in chosen \
                and len(chosen) < 4:
            chosen.append(mv)

    for mv in sig_for(sp):                      # signature first, always honoured
        add(mv)

    used = {}
    for m0 in chosen:
        t0 = MOVES.get(m0, {}).get("type")
        used[t0] = used.get(t0, 0) + 1

    ls = learnset(sp)
    if ls:
        pool = []
        for x in ls:
            nm = x.replace('MOVE_', '')
            d = MOVES.get(nm)
            if not d or d["power"] <= 0 or nm in BLACKLIST:
                continue
            stab = d["type"] in types.get(sp, [])
            same_cat = d["cat"] == better.get(sp)
            # low accuracy is a real cost: Zap Cannon is 120 power and misses half
            score = (d["power"] + (40 if stab else 0) + (30 if same_cat else 0)
                     - max(0, 100 - d.get("acc", 100)) * 2.0)
            pool.append((score, nm, d["type"]))
        pool.sort(reverse=True)
        for _, nm, ty in pool:
            if len(chosen) >= 4:
                break
            if used.get(ty, 0) >= 2:      # never stack more than two of a type
                continue
            before = len(chosen)
            add(nm)
            if len(chosen) > before:
                used[ty] = used.get(ty, 0) + 1
    return chosen

lines = [
    "\t@ ---- DEV GIFT: every legendary / mythical / Ultra Beast in the game ----",
    "\t@ Lv100, 252 EVs in every stat, 31 IVs, nice neutral nature.",
    "\t@ Moves: signature move(s) first, then the strongest STAB/coverage",
    "\t@ from that species' own learnset. First six fill the party, rest go to the PC.",
    "\t@ Field moves: Cut is gated on the Stone Badge (src/field_move.c) and",
    "\t@ Groudon is the only party mon that can learn it, so grant both.",
    "\tsetflag FLAG_BADGE01_GET", "\tsetflag FLAG_BADGE02_GET",
    "\tsetflag FLAG_BADGE03_GET", "\tsetflag FLAG_BADGE04_GET",
    "\tsetflag FLAG_BADGE05_GET", "\tsetflag FLAG_BADGE06_GET",
    "\tsetflag FLAG_BADGE07_GET", "\tsetflag FLAG_BADGE08_GET",
    "\tgiveitem ITEM_HM01, 1", "\tgiveitem ITEM_HM02, 1",
    "\tgiveitem ITEM_HM03, 1", "\tgiveitem ITEM_HM04, 1",
    "\tgiveitem ITEM_HM05, 1", "\tgiveitem ITEM_HM06, 1",
    "\tgiveitem ITEM_HM07, 1", "\tgiveitem ITEM_HM08, 1",
    "\t@ money, pokedex, running shoes, national dex",
    "\taddmoney 999999",
    "\tsetflag FLAG_SYS_POKEDEX_GET",
    "\tsetflag FLAG_SYS_NATIONAL_DEX",
    "\tsetflag FLAG_SYS_B_DASH",
    "\t@ balls (16 pocket slots, 999 per stack is the cap)",
    "\tgiveitem ITEM_MASTER_BALL, 999",
    "\tgiveitem ITEM_ULTRA_BALL, 999",
    "\tgiveitem ITEM_GREAT_BALL, 999",
    "\tgiveitem ITEM_QUICK_BALL, 999",
    "\tgiveitem ITEM_DUSK_BALL, 999",
    "\tgiveitem ITEM_NET_BALL, 999",
    "\tgiveitem ITEM_TIMER_BALL, 999",
    "\t@ healing / utility (30 item slots)",
    "\tgiveitem ITEM_FULL_RESTORE, 999",
    "\tgiveitem ITEM_MAX_POTION, 999",
    "\tgiveitem ITEM_MAX_REVIVE, 999",
    "\tgiveitem ITEM_MAX_ELIXIR, 999",
    "\tgiveitem ITEM_MAX_ETHER, 999",
    "\tgiveitem ITEM_FULL_HEAL, 999",
    "\tgiveitem ITEM_SUPER_REPEL, 999",
    "\t@ travel",
    "\tgiveitem ITEM_MACH_BIKE, 1",
    "\tgiveitem ITEM_SUPER_ROD, 1",
]
preview = []
for sp in gift:
    mvs = pick_moves(sp)
    if sp == "GROUDON" and "CUT" not in mvs:
        if len(mvs) >= 4:
            mvs[-1] = "CUT"
        else:
            mvs.append("CUT")
    tail = (", " + ", ".join(f"MOVE_{m}" for m in mvs)) if mvs else ""
    lines.append(
        f"\tgivemon SPECIES_{sp}, 100, , , NATURE_HARDY, , , "
        f"252, 252, 252, 252, 252, 252, 31, 31, 31, 31, 31, 31{tail}")
    preview.append((sp, mvs))

print(f"species gifted: {len(gift)}")
for sp in ("MEWTWO_ARMORED", "RAYQUAZA", "LUGIA", "HO_OH", "KYOGRE",
           "GROUDON", "DIALGA", "SOLGALEO", "ZACIAN_HERO"):
    for s2, mv in preview:
        if s2 == sp:
            print(f"  {sp:16s} {mv}")
no_moves = [s for s, mv in preview if not mv]
print(f"species with no explicit moves (natural moveset): {len(no_moves)}")

path = 'data/maps/LittlerootTown_BrendansHouse_2F/scripts.inc'
src = open(path).read()
pat = re.compile(r'\t@ ---- DEV GIFT.*?(?=\n\tcompare VAR_RESULT, MON_CANT_GIVE)', re.S)
if not pat.search(src):
    sys.exit("marker block not found")
src = pat.sub("\n".join(lines), src, count=1)
open(path, 'w').write(src)
print("script updated; givemon lines:", src.count("givemon SPECIES_"))

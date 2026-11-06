#!/usr/bin/env python3
"""
tools/map_index.py - generate docs/maps/INDEX.md from the ROM's own map data.

Reads, for every map in data/maps/:
  * data/maps/<Map>/map.json          name, music, type, weather, connections
  * data/layouts/layouts.json          width, height, primary/secondary tilesets
  * data/maps/<Map>/events.inc         object / warp / coord / bg events
  * data/maps/<Map>/scripts.inc        scripts, trainers, items given

Emits a human-table + machine-readable JSON index so an agent (or a person)
can answer "what is in this map / how do I get there" without grepping source.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS = os.path.join(ROOT, "data", "maps")
LAYOUTS = os.path.join(ROOT, "data", "layouts", "layouts.json")
OUT_MD = os.path.join(ROOT, "docs", "maps", "INDEX.md")
OUT_JSON = os.path.join(ROOT, "docs", "maps", "map_index.json")

ITEM_RE = re.compile(r'\b(?:give|find)item\s+(ITEM_[A-Z0-9_]+)')
TRAINER_RE = re.compile(r'\btrainerbattle_\w+\s+(TRAINER_[A-Z0-9_]+)')
WARP_RE = re.compile(r'\bwarp\s+(MAP_[A-Z0-9_]+)')
GIVEMON_RE = re.compile(r'\bgivemon\s+(SPECIES_[A-Z0-9_]+)')


def load_layouts():
    with open(LAYOUTS) as fh:
        raw = json.load(fh)["layouts"]
    out = {}
    for entry in raw:
        if isinstance(entry, dict) and entry.get("id"):
            out[entry["id"]] = entry
    return out


def read_map_json(name):
    path = os.path.join(MAPS, name, "map.json")
    if not os.path.exists(path):
        return {}
    with open(path) as fh:
        return json.load(fh)


def parse_events_inc(name):
    """Pull structured bits out of events.inc (object/warp counts + warps)."""
    path = os.path.join(MAPS, name, "events.inc")
    data = {"objects": [], "warps": [], "coordinates": [], "background": []}
    if not os.path.exists(path):
        return data
    src = open(path, errors="ignore").read()
    for m in re.finditer(r'^\s*object_event\s+(\d+),\s*(\S+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\S+).*?,\s*([A-Z0-9_]+),\s*(\d+),', src, re.M):
        data["objects"].append({
            "id": int(m.group(1)), "gfx": m.group(2),
            "x": int(m.group(3)), "y": int(m.group(4)), "z": int(m.group(5)),
            "script": m.group(7) if m.group(7) not in ("NULL",) else "",
            "flag": int(m.group(8)),
        })
    for m in re.finditer(r'^\s*warp_def\s+(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(MAP_[A-Z0-9_]+)', src, re.M):
        data["warps"].append({
            "x": int(m.group(1)), "y": int(m.group(2)), "w": int(m.group(3)),
            "h": int(m.group(4)), "dest": m.group(5),
        })
    for m in re.finditer(r'^\s*coord_event\s+(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\S+)', src, re.M):
        data["coordinates"].append({
            "scene": m.group(1), "x": int(m.group(2)), "y": int(m.group(3)),
            "w": int(m.group(4)), "h": int(m.group(5)), "script": m.group(6),
        })
    return data


def read_scripts(name):
    path = os.path.join(MAPS, name, "scripts.inc")
    if not os.path.exists(path):
        return ""
    return open(path, errors="ignore").read()


def strip_map_prefix(const):
    return const[4:].title().replace("_", " ")


def main():
    layouts = load_layouts()
    with open(os.path.join(MAPS, "map_groups.json")) as fh:
        groups = json.load(fh)

    group_of = {}
    for gname, members in groups.items():
        if gname == "group_order" or not isinstance(members, list):
            continue
        for member in members:
            group_of[member] = gname.replace("gMapGroup_", "")

    names = sorted(d for d in os.listdir(MAPS)
                   if os.path.isdir(os.path.join(MAPS, d))
                   and d != "g" and not d.startswith("."))

    index = []
    for name in names:
        mj = read_map_json(name)
        lay = layouts.get(mj.get("layout", ""), {}) if mj else {}
        ev = parse_events_inc(name)
        scripts = read_scripts(name)

        items = sorted(set(ITEM_RE.findall(scripts)))
        trainers = sorted(set(TRAINER_RE.findall(scripts)))
        mons = sorted(set(GIVEMON_RE.findall(scripts)))
        warps = ev["warps"]
        conns = []
        for c in (mj.get("connections") or []):
            if isinstance(c, dict):
                conns.append(c.get("direction", "?") + "->" + str(c.get("map", "?")))
            else:
                conns.append(str(c))

        index.append({
            "name": name,
            "group": group_of.get(name, "?"),
            "label": mj.get("name", name),
            "layout": mj.get("layout", ""),
            "width": lay.get("width"),
            "height": lay.get("height"),
            "primary_tileset": lay.get("primary_tileset", ""),
            "secondary_tileset": lay.get("secondary_tileset", ""),
            "music": mj.get("music", ""),
            "map_type": mj.get("map_type", ""),
            "weather": mj.get("weather", ""),
            "connections": conns,
            "warps": [w["dest"] for w in warps],
            "objects": [
                {"id": o["id"], "gfx": o["gfx"], "x": o["x"], "y": o["y"],
                 "script": o["script"]} for o in ev["objects"]
            ],
            "item_count": len(items),
            "items": items,
            "trainers": trainers,
            "given_mons": mons,
            "coord_triggers": len(ev["coordinates"]),
        })

    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_JSON, "w") as fh:
        json.dump(index, fh, indent=1, sort_keys=True)

    with open(OUT_MD, "w") as fh:
        fh.write("# Map Index (generated)\n\n")
        fh.write(f"Generated by `tools/map_index.py`. **{len(index)} maps.**\n\n")
        fh.write("Regenerate with:\n\n```\npython3 tools/map_index.py\n```\n\n")
        fh.write("| Map | Group | Size | Tileset | Warps to | Items | Trainers |\n")
        fh.write("|---|---|---|---|---|---|---|\n")
        for m in index:
            size = f"{m['width']}x{m['height']}" if m["width"] else "?"
            tileset = (m["secondary_tileset"] or m["primary_tileset"] or "?") \
                .replace("GfxTileset_", "").replace("Tileset_", "")
            warps = ", ".join(strip_map_prefix(w) for w in m["warps"][:6])
            if len(m["warps"]) > 6:
                warps += f" +{len(m['warps']) - 6}"
            items = ", ".join(i.replace("ITEM_", "") for i in m["items"][:8])
            if len(m["items"]) > 8:
                items += f" +{len(m['items']) - 8}"
            trainers = ", ".join(t.replace("TRAINER_", "") for t in m["trainers"][:4])
            if len(m["trainers"]) > 4:
                trainers += f" +{len(m['trainers']) - 4}"
            fh.write(f"| {m['name']} | {m['group']} | {size} | {tileset} | "
                     f"{warps} | {items} | {trainers} |\n")

    print(f"maps indexed: {len(index)} -> {OUT_MD}, {OUT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

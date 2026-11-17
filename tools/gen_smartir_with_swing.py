#!/usr/bin/env python3
"""
Generate SmartIR climate JSON with swing_mode support.
Derives all 7 vswing positions algorithmically from base codes.
"""

import json
import base64

# ── Vswing bit patterns (bits 94, 95, 96) ─────────────────────────────────────
VSWING_BITS = {
    "auto": [1, 1, 1],   # auto swing
    "v1":   [0, 1, 1],   # highest
    "v2":   [1, 0, 1],
    "v3":   [0, 0, 1],   # center
    "v4":   [1, 1, 0],
    "v5":   [0, 1, 0],   # lowest
    "none": [1, 0, 0],   # fixed / no swing
}

SHORT = 13
LONG  = 39

def set_vswing(b64_code: str, swing_name: str) -> str:
    raw = bytearray(base64.b64decode(b64_code))
    for i, bit in enumerate(VSWING_BITS[swing_name]):
        raw[4 + 2 * (94 + i) + 1] = LONG if bit else SHORT
    return base64.b64encode(bytes(raw)).decode()


def set_temp(b64_code: str, target_temp: int) -> str:
    """Derive IR code for any temperature (16–30°C) from a base code."""
    raw = bytearray(base64.b64decode(b64_code))
    inv = 32 - target_temp        # inverted field: bits 57–60
    fwd = target_temp - 17        # forward field:  bits 65–68
    for i in range(4):
        raw[4 + 2 * (57 + i) + 1] = LONG if (inv >> i) & 1 else SHORT
        raw[4 + 2 * (65 + i) + 1] = LONG if (fwd >> i) & 1 else SHORT
    return base64.b64encode(bytes(raw)).decode()


# ── Load base codes ────────────────────────────────────────────────────────────
SRC = "codes/learned_ir_codes_full.json"
with open(SRC) as f:
    src = json.load(f)["commands"]

# Fan mode name mapping  (learned → SmartIR label)
FAN_MAP = {
    "auto": "auto",
    "f1":   "level1",
    "f2":   "level2",
    "f3":   "level3",
    "f4":   "level4",
}

SWING_MODES = list(VSWING_BITS.keys())   # ["auto","v1","v2","v3","v4","v5","none"]
TEMPS       = [str(t) for t in range(16, 31)]

# Modes we support and their expected fan combos
MODE_FANS = {
    "cool": ["auto", "f1", "f2", "f3", "f4"],
    "heat": ["auto"],
    "dry":  ["auto"],
}

# ── Resolve base code for any (mode, fan, temp) — derive if not learned ───────
def get_base_code(mode: str, fan: str, temp: int):
    key = f"{mode}_{temp}_{fan}_vauto_hnone"
    if key in src:
        return src[key]
    # Try to find any learned temp for this mode+fan, then derive
    for t in range(16, 31):
        fallback_key = f"{mode}_{t}_{fan}_vauto_hnone"
        if fallback_key in src:
            return set_temp(src[fallback_key], temp)
    return None

# ── Build SmartIR commands ─────────────────────────────────────────────────────
commands: dict = {"off": src["off"]}

for mode, fans in MODE_FANS.items():
    commands[mode] = {}
    for fan in fans:
        smartir_fan = FAN_MAP[fan]
        commands[mode][smartir_fan] = {}
        for swing in SWING_MODES:
            commands[mode][smartir_fan][swing] = {}
            for temp_int in range(16, 31):
                temp = str(temp_int)
                base_code = get_base_code(mode, fan, temp_int)
                if base_code is None:
                    print(f"  ⚠ no base code for {mode}/{fan}/{temp_int}°C, skipping")
                    continue
                commands[mode][smartir_fan][swing][temp] = set_vswing(base_code, swing)

# ── Assemble device JSON ───────────────────────────────────────────────────────
device = {
    "manufacturer":        "Mitsubishi Heavy",
    "supportedModels":     ["SRK25ZSXT-W", "SRK35ZSXT-W"],
    "supportedController": "Broadlink",
    "commandsEncoding":    "Base64",
    "minTemperature":      16,
    "maxTemperature":      30,
    "precision":           1,
    "operationModes":      ["cool", "heat", "dry"],
    "fanModes":            ["auto", "level1", "level2", "level3", "level4"],
    "swingModes":          SWING_MODES,
    "commands":            commands,
}

OUT = "codes/1693_with_swing.json"
with open(OUT, "w") as f:
    json.dump(device, f, indent=2, ensure_ascii=False)

# Summary
total = sum(
    len(commands[m][fn][sw])
    for m in MODE_FANS
    for fn in commands[m]
    for sw in commands[m][fn]
)
print(f"✅ Generated {OUT}")
print(f"   {total} IR codes total")
print(f"   Modes: {list(MODE_FANS.keys())}")
print(f"   Fan modes: {list(FAN_MAP.values())}")
print(f"   Swing modes: {SWING_MODES}")
print(f"   Temperature range: 16–30°C")

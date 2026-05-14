# Mitsubishi Heavy AC IR Protocol

Reverse-engineered IR protocol for **Mitsubishi Heavy Industries** air conditioners with remote **RLA502A700AA**.

Tested on: **SRK ZSXT series** (e.g. SRK25ZSXT-W, SRK35ZSXT-W)

## Compatible Models

| Remote | AC Series |
|--------|-----------|
| RLA502A700AA | SRK ZSXT |
| RKS502A502 / RKS502A503 | SRKM / SRK HBE series (possibly compatible) |

## What's in this repo

| Path | Description |
|------|-------------|
| `codes/learned_raw.json` | Raw IR codes learned directly from remote via Broadlink |
| `codes/learned_ir_codes_full.json` | Full code set (16–30°C), including derived temperatures |
| `tools/ir_learn.py` | Learn IR codes from remote via Home Assistant + Broadlink |
| `tools/ir_learn_hswing.py` | Learn horizontal swing positions |
| `tools/ir_decode.py` | Decode IR signal → human-readable AC state |
| `tools/ir_verify.py` | Send a command and verify AC response |
| `docs/protocol.md` | Full bit-level protocol documentation |

## Requirements

- [Home Assistant](https://www.home-assistant.io/)
- [Broadlink](https://www.home-assistant.io/integrations/broadlink/) integration (e.g. RM4 Pro, RM4 Mini)
- Python 3.8+ with `requests` library

## Quick Start

### 1. Learn your own codes

Edit the `TOKEN`, `HA_URL`, `ENTITY_ID` in the tools, then:

```bash
python3 tools/ir_learn.py          # Learn temperature/mode/fan commands
python3 tools/ir_learn_hswing.py   # Learn horizontal swing positions
```

### 2. Decode what your remote sends

```bash
python3 tools/ir_decode.py
# Press Enter → point remote at Broadlink → see decoded state
```

### 3. Use with SmartIR (Home Assistant)

See `docs/protocol.md` for how to build a SmartIR-compatible JSON from the learned codes.

## Key Findings

The IR packet is **153 bits** long (Broadlink raw format, ~32µs per unit).

| Field | Bit positions | Encoding |
|-------|--------------|----------|
| Mode | 41–44 | see protocol.md |
| Temperature (inverted) | 57–60 | `(32 - temp)` LSB first |
| Temperature | 65–68 | `(temp - 17)` LSB first |
| Fan speed | 73–75 | see protocol.md |
| Vertical swing | 94–96 | see protocol.md |
| Horizontal swing | 0, 105–108 | see protocol.md |

Temperature range: **16°C – 30°C**

Temperatures can be **derived** (not all need to be learned) — only the 4 temperature bits need to change. See `docs/protocol.md`.

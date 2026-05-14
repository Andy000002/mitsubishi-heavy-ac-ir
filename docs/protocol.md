# Mitsubishi Heavy AC IR Protocol — Bit-Level Reference

Remote: **RLA502A700AA**  
AC: **SRK ZSXT series**

---

## Packet Format

- Encoding: **Broadlink** base64 raw IR
- Total bits decoded: **153**
- Short pulse (bit 0): ~416 µs (13 units × 32 µs)
- Long pulse (bit 1): ~1248 µs (39 units × 32 µs)
- Each bit is encoded in the **space** duration of each mark/space pair

### Reading bit values

```python
raw = base64.b64decode(b64_code)
# raw[0..3] = Broadlink header
# payload = raw[4:]
# bit N → space byte at payload index (2*N + 1)
bit_value = 1 if raw[4 + 2*N + 1] > 20 else 0
```

---

## Bit Map

### Mode — bits 41–44

| bits (41, 42, 43, 44) | Mode |
|-----------------------|------|
| 0, 1, 1, 0 | Cool（冷氣）|
| 1, 1, 0, 0 | Heat（暖氣）|
| 1, 0, 1, 0 | Dry（除濕）|
| 0, 0, 1, 1 | Fan only（送風）|

Bits 49–52 are the bitwise complement (used as checksum).

---

### Temperature — bits 57–60 and 65–68

Two 4-bit fields encoding the same temperature differently:

| Field | Bits | Formula | Encoding |
|-------|------|---------|----------|
| Inverted temp | 57–60 | `32 - temp` | LSB first |
| Forward temp | 65–68 | `temp - 17` | LSB first |

**Example: 26°C**
- `32 - 26 = 6` = `0110` → bits 57–60 = `0, 1, 1, 0`
- `26 - 17 = 9` = `1001` → bits 65–68 = `1, 0, 0, 1`

**Range: 16°C – 30°C**

> Temperatures can be **algorithmically derived** from a single learned base code.
> Only bits 57–60 and 65–68 need to change between temperatures.

```python
def generate_temp_code(base_b64, target_temp, short=13, long_=39):
    raw = bytearray(base64.b64decode(base_b64))
    inv = 32 - target_temp
    fwd = target_temp - 17
    for i in range(4):
        raw[4 + 2*(57+i) + 1] = long_ if (inv >> i) & 1 else short
        raw[4 + 2*(65+i) + 1] = long_ if (fwd >> i) & 1 else short
    return base64.b64encode(bytes(raw)).decode()
```

---

### Fan Speed — bits 73–75

| bits (73, 74, 75) | Fan speed |
|-------------------|-----------|
| 1, 1, 1 | Auto |
| 0, 1, 1 | Level 1（最弱）|
| 1, 0, 1 | Level 2 |
| 0, 0, 1 | Level 3 |
| 1, 1, 0 | Level 4（最強）|

Bits 81–83 are the complement.

---

### Vertical Swing — bits 94–96

| bits (94, 95, 96) | Position |
|-------------------|----------|
| 0, 1, 1 | V1（最高 / Highest）|
| 1, 0, 1 | V2 |
| 0, 0, 1 | V3（中間 / Center）|
| 1, 1, 0 | V4 |
| 0, 1, 0 | V5（最低 / Lowest）|
| 1, 1, 1 | Auto swing |
| 1, 0, 0 | None（無指定）|

---

### Horizontal Swing — bits 0, 105–108

This remote has **two independently aimed louver groups** (left and right side).

| bits (0, 105, 106, 107, 108) | Position |
|------------------------------|----------|
| 0, 1, 1, 1, 1 | Left → Right sweep（左右擺）|
| 1, 0, 0, 1, 1 | Center-Center（中中）|
| 1, 0, 1, 0, 1 | Right-Right（右右）|
| 1, 0, 1, 1, 1 | Left-Left（左左）|
| 1, 1, 0, 0, 1 | Right → Left sweep（右左擺）|
| 1, 1, 0, 1, 1 | Left-Center（左中）|
| 1, 1, 1, 0, 1 | Center-Right（中右）|
| 1, 1, 1, 1, 0 | Straight（直線 / None）|
| 1, 1, 1, 1, 1 | Auto-Auto（自動自動）|

---

## How Temperatures Were Derived

Only **6 temperatures were physically learned** (23–28°C).
All others (16–22°C, 29–30°C) were derived by modifying bits 57–60 and 65–68
in the base code.

Verification: derived codes matched all 6 physically-learned codes bit-for-bit
at the relevant positions.

---

## Methodology

1. Learned IR codes via **Home Assistant** `remote.learn_command` service
   with a **Broadlink RM4** device
2. Decoded Broadlink base64 packets to raw pulse/space timings
3. Converted timings to bit stream (threshold: 20 units)
4. Compared codes with single-variable changes to isolate bit fields
5. Verified encoding formulas against all learned codes

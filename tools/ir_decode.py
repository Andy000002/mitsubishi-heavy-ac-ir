#!/usr/bin/env python3
"""
IR 解碼工具
按 Enter → 對著 Broadlink 按遙控器 → 顯示你按的是什麼狀態
"""

import base64, json, time, requests, warnings
warnings.filterwarnings("ignore")

HA_URL = "http://homeassistant.local:8123"
TOKEN = "YOUR_HA_LONG_LIVED_ACCESS_TOKEN"
ENTITY_ID = "remote.YOUR_BROADLINK_ENTITY"
DEVICE = "ac"
TEMP_CMD = "__decode_tmp__"
CODES_FILE = "/config/.storage/broadlink_remote_XXXXXXXXXXXX_codes"

HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# ── 解碼表（從 bit 分析得出）──

MODE_BITS = {41: None, 42: None, 43: None, 44: None}
MODE_MAP = {
    (0,1,1,0): "cool  冷氣",
    (1,1,0,0): "heat  暖氣",
    (1,0,1,0): "dry   除濕",
    (0,0,1,1): "fan   送風",
}

FAN_MAP = {
    (1,1,1): "auto  自動",
    (0,1,1): "f1    最弱",
    (1,0,1): "f2",
    (0,0,1): "f3",
    (1,1,0): "f4    最強",
}

VSWING_MAP = {
    # bits 89,90,91 - 從學習碼推導
}

def get_bit(raw, bit_pos):
    idx = 4 + 2 * bit_pos + 1
    if idx >= len(raw):
        return 0
    return 1 if raw[idx] > 20 else 0

def decode_ir(raw):
    result = {}

    # 關機：off 碼沒有完整的 AC 狀態，長度或特定 bit 會不同
    # 先檢查是不是 off（簡單用 mode bits 都是 0 判斷）
    mode_bits = tuple(get_bit(raw, p) for p in [41,42,43,44])
    mode = MODE_MAP.get(mode_bits)

    if mode is None:
        return {"狀態": "OFF  關機"}

    result["模式"] = mode

    # 溫度：bits 65-68 = (temp-17) LSB first
    fwd = sum(get_bit(raw, 65+i) << i for i in range(4))
    temp = fwd + 17
    if 16 <= temp <= 30:
        result["溫度"] = f"{temp}°C"
    else:
        result["溫度"] = f"? ({fwd})"

    # 風速：bits 73,74,75
    fan_bits = tuple(get_bit(raw, p) for p in [73,74,75])
    result["風速"] = FAN_MAP.get(fan_bits, f"? {fan_bits}")

    # 上下 swing：bits 94,95,96
    vbits = tuple(get_bit(raw, p) for p in [94, 95, 96])
    vswing_map = {
        (0, 1, 1): "v1    第1格（最高）",
        (1, 0, 1): "v2    第2格",
        (0, 0, 1): "v3    第3格（中間）",
        (1, 1, 0): "v4    第4格",
        (0, 1, 0): "v5    第5格（最低）",
        (1, 1, 1): "auto  自動擺風",
        (1, 0, 0): "none  無指定",
    }
    result["上下swing"] = vswing_map.get(vbits, f"? {vbits}")

    # 左右 swing：bits 0, 105, 106, 107, 108
    hbits = tuple(get_bit(raw, p) for p in [0, 105, 106, 107, 108])
    hswing_map = {
        (0, 1, 1, 1, 1): "hlr   左→右擺",
        (1, 0, 0, 1, 1): "hmm   中中",
        (1, 0, 1, 0, 1): "hrr   右右",
        (1, 0, 1, 1, 1): "hll   左左",
        (1, 1, 0, 0, 1): "hrl   右→左擺",
        (1, 1, 0, 1, 1): "hlm   左中",
        (1, 1, 1, 0, 1): "hmr   中右",
        (1, 1, 1, 1, 0): "hnone 直線",
        (1, 1, 1, 1, 1): "hauto 自動自動",
    }
    result["左右swing"] = hswing_map.get(hbits, f"? {hbits}")

    return result


def load_codes():
    try:
        with open(CODES_FILE) as f:
            return json.load(f).get("data", {}).get(DEVICE, {})
    except Exception:
        return {}


def learn_once():
    """學一次 IR，回傳 raw bytes，然後刪掉暫存"""
    prev = load_codes()

    requests.post(f"{HA_URL}/api/services/remote/learn_command",
                  headers=HEADERS,
                  json={"entity_id": ENTITY_ID, "device": DEVICE, "command": TEMP_CMD},
                  timeout=10)

    deadline = time.time() + 15
    while time.time() < deadline:
        codes = load_codes()
        if TEMP_CMD in codes and codes[TEMP_CMD] != prev.get(TEMP_CMD):
            b64 = codes[TEMP_CMD]
            # 刪除暫存碼
            try:
                with open(CODES_FILE) as f:
                    storage = json.load(f)
                storage["data"][DEVICE].pop(TEMP_CMD, None)
                with open(CODES_FILE, "w") as f:
                    json.dump(storage, f, ensure_ascii=False)
            except Exception:
                pass
            return base64.b64decode(b64)
        time.sleep(0.3)
    return None


def main():
    print("=" * 45)
    print("IR 解碼工具")
    print("按 Enter → 對著 Broadlink 按遙控器")
    print("Ctrl+C 離開")
    print("=" * 45)

    r = requests.get(f"{HA_URL}/api/", headers=HEADERS, timeout=5)
    if r.status_code != 200:
        print("❌ 無法連線 HA")
        return
    print("✅ HA 連線正常\n")

    while True:
        try:
            input("按 Enter 後，立刻對 Broadlink 按遙控器...")
        except (EOFError, KeyboardInterrupt):
            print("\n離開")
            break

        print("⏳ 學習中...")
        raw = learn_once()

        if raw is None:
            print("❌ 沒收到 IR 訊號，請重試\n")
            continue

        result = decode_ir(raw)
        print("\n┌─ 解碼結果 ─────────────────")
        for k, v in result.items():
            print(f"│  {k:8}: {v}")
        print("└─────────────────────────────\n")


if __name__ == "__main__":
    main()

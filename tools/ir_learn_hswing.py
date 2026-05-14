#!/usr/bin/env python3
"""
學習左右 swing IR 碼（只需學 9 個位置，用來找 bit 規律）
"""

import json, time, requests, warnings
warnings.filterwarnings("ignore")

HA_URL = "http://homeassistant.local:8123"
TOKEN = "YOUR_HA_LONG_LIVED_ACCESS_TOKEN"
ENTITY_ID = "remote.YOUR_BROADLINK_ENTITY"
DEVICE = "ac"
CODES_FILE = "/config/.storage/broadlink_remote_XXXXXXXXXXXX_codes"

HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# 9 個左右位置（上下固定 vauto，其他固定 cool 26 auto）
COMMANDS = [
    ("cool_26_auto_vauto_hll",   "左左"),
    ("cool_26_auto_vauto_hlm",   "左中"),
    ("cool_26_auto_vauto_hmm",   "中中"),
    ("cool_26_auto_vauto_hmr",   "中右"),
    ("cool_26_auto_vauto_hrr",   "右右"),
    ("cool_26_auto_vauto_hlr",   "左→右擺"),
    ("cool_26_auto_vauto_hrl",   "右→左擺"),
    ("cool_26_auto_vauto_hauto", "自動自動"),
    ("cool_26_auto_vauto_hnone", "直線"),
]

def load_codes():
    try:
        with open(CODES_FILE) as f:
            return json.load(f).get("data", {}).get(DEVICE, {})
    except Exception:
        return {}

def call_learn(cmd):
    resp = requests.post(f"{HA_URL}/api/services/remote/learn_command",
                         headers=HEADERS,
                         json={"entity_id": ENTITY_ID, "device": DEVICE, "command": cmd},
                         timeout=10)
    return resp.status_code == 200

def wait_for_code(cmd, prev, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        codes = load_codes()
        if cmd in codes and codes[cmd] != prev.get(cmd):
            return codes[cmd]
        time.sleep(0.3)
    return None

def main():
    print("=" * 55)
    print("左右 Swing 學習（9 個位置）")
    print("=" * 55)
    print("固定設定：冷氣・26度・自動風・上下自動")
    print("只改左右角度\n")

    results = {}
    for i, (cmd, desc) in enumerate(COMMANDS, 1):
        prev = load_codes()
        print(f"[{i}/9] {desc}")

        if cmd in prev:
            print(f"      ✅ 已有，跳過\n")
            results[cmd] = prev[cmd]
            continue

        input("      → 調好後按 Enter，立刻按遙控器...")
        if not call_learn(cmd):
            print("      ❌ 失敗\n"); continue

        code = wait_for_code(cmd, prev)
        if code:
            print(f"      ✅ 成功！\n")
            results[cmd] = code
        else:
            print(f"      ❌ 超時\n")

    print(f"完成！學到 {len(results)}/9 個左右 swing 碼")
    print("告訴我完成，我幫你分析 bit 並更新解碼器。")

if __name__ == "__main__":
    main()

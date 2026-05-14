#!/usr/bin/env python3
"""
Broadlink IR 學習腳本（含上下7格 swing，左右固定直線）
"""

import json
import time
import requests
import warnings
warnings.filterwarnings("ignore")

# ===== 設定 =====
HA_URL = "http://homeassistant.local:8123"
TOKEN = "YOUR_HA_LONG_LIVED_ACCESS_TOKEN"
ENTITY_ID = "remote.YOUR_BROADLINK_ENTITY"
DEVICE = "ac"
CODES_FILE = "/config/.storage/broadlink_remote_XXXXXXXXXXXX_codes"

# ===== 指令清單 =====
# 左右固定直線（hnone），上下自動擺（vauto）為預設
# 上下 swing 只針對 26 度學各格位置

COMMANDS = [
    # ──────────────────────────────
    # 關機
    # ──────────────────────────────
    ("off",
     "關機"),

    # ──────────────────────────────
    # 溫度組：冷氣・自動風・上下自動・左右直線
    # ──────────────────────────────
    ("cool_23_auto_vauto_hnone",  "冷氣・23度・自動風・上下自動・左右直線"),
    ("cool_24_auto_vauto_hnone",  "冷氣・24度・自動風・上下自動・左右直線"),
    ("cool_25_auto_vauto_hnone",  "冷氣・25度・自動風・上下自動・左右直線"),
    ("cool_26_auto_vauto_hnone",  "冷氣・26度・自動風・上下自動・左右直線"),
    ("cool_27_auto_vauto_hnone",  "冷氣・27度・自動風・上下自動・左右直線"),
    ("cool_28_auto_vauto_hnone",  "冷氣・28度・自動風・上下自動・左右直線"),

    # ──────────────────────────────
    # 風速組：26度・左右直線・上下自動（auto + 4格）
    # ──────────────────────────────
    ("cool_26_f1_vauto_hnone",    "冷氣・26度・風速1（最弱）・上下自動・左右直線"),
    ("cool_26_f2_vauto_hnone",    "冷氣・26度・風速2・上下自動・左右直線"),
    ("cool_26_f3_vauto_hnone",    "冷氣・26度・風速3・上下自動・左右直線"),
    ("cool_26_f4_vauto_hnone",    "冷氣・26度・風速4（最強）・上下自動・左右直線"),

    # ──────────────────────────────
    # 上下 swing 組：26度・自動風・左右直線
    # （切上下角度用，v1=最高 v5=最低）
    # ──────────────────────────────
    ("cool_26_auto_v1_hnone",     "冷氣・26度・自動風・上下第1格（最高）・左右直線"),
    ("cool_26_auto_v2_hnone",     "冷氣・26度・自動風・上下第2格・左右直線"),
    ("cool_26_auto_v3_hnone",     "冷氣・26度・自動風・上下第3格（中間）・左右直線"),
    ("cool_26_auto_v4_hnone",     "冷氣・26度・自動風・上下第4格・左右直線"),
    ("cool_26_auto_v5_hnone",     "冷氣・26度・自動風・上下第5格（最低，朝下）・左右直線"),
    ("cool_26_auto_vswing_hnone", "冷氣・26度・自動風・上下自動擺・左右直線"),
    ("cool_26_auto_vnone_hnone",  "冷氣・26度・自動風・上下無指定・左右直線"),

    # ──────────────────────────────
    # 暖氣：26~28度・自動風・上下自動・左右直線
    # ──────────────────────────────
    ("heat_26_auto_vauto_hnone",  "暖氣・26度・自動風・上下自動・左右直線"),
    ("heat_27_auto_vauto_hnone",  "暖氣・27度・自動風・上下自動・左右直線"),
    ("heat_28_auto_vauto_hnone",  "暖氣・28度・自動風・上下自動・左右直線"),

    # ──────────────────────────────
    # 除濕：26~28度・自動風・上下自動・左右直線
    # ──────────────────────────────
    ("dry_26_auto_vauto_hnone",   "除濕・26度・自動風・上下自動・左右直線"),
    ("dry_27_auto_vauto_hnone",   "除濕・27度・自動風・上下自動・左右直線"),
    ("dry_28_auto_vauto_hnone",   "除濕・28度・自動風・上下自動・左右直線"),

    # ──────────────────────────────
    # 送風
    # ──────────────────────────────
    ("fan_auto_vauto_hnone",      "送風・自動風・上下自動・左右直線"),
]

# ================

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


def load_codes():
    try:
        with open(CODES_FILE) as f:
            return json.load(f).get("data", {}).get(DEVICE, {})
    except Exception:
        return {}


def call_learn(command_name):
    resp = requests.post(
        f"{HA_URL}/api/services/remote/learn_command",
        headers=headers,
        json={
            "entity_id": ENTITY_ID,
            "device": DEVICE,
            "command": command_name,
        },
        timeout=10,
    )
    return resp.status_code == 200


def wait_for_code(command_name, prev_codes, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        codes = load_codes()
        if command_name in codes and codes.get(command_name) != prev_codes.get(command_name):
            return codes[command_name]
        time.sleep(0.5)
    return None


def main():
    print("=" * 60)
    print("Broadlink IR 學習腳本")
    print("左右：固定直線  /  上下：自動 + 7格")
    print("=" * 60)
    print(f"共 {len(COMMANDS)} 個指令\n")
    print("每個指令：調好遙控器 → 按 Enter → 立刻對 Broadlink 按確認\n")

    r = requests.get(f"{HA_URL}/api/", headers=headers, timeout=5)
    if r.status_code != 200:
        print(f"❌ 無法連線 HA")
        return
    print("✅ HA 連線正常\n")

    results = {}

    for i, (cmd_name, description) in enumerate(COMMANDS, 1):
        prev_codes = load_codes()
        print(f"[{i:2d}/{len(COMMANDS)}] {cmd_name}")
        print(f"         {description}")

        if cmd_name in prev_codes:
            print(f"         ✅ 已有，跳過\n")
            results[cmd_name] = prev_codes[cmd_name]
            continue

        input("         → 調好後按 Enter，立刻按遙控器...")

        if not call_learn(cmd_name):
            print("         ❌ 呼叫失敗，跳過\n")
            continue

        print("         ⏳ 學習中...")
        code = wait_for_code(cmd_name, prev_codes, timeout=20)

        if code:
            print(f"         ✅ 成功！\n")
            results[cmd_name] = code
        else:
            print("         ❌ 超時，跳過（可重跑補學）\n")

    print("=" * 60)
    print(f"完成！學到 {len(results)}/{len(COMMANDS)} 個")
    print("=" * 60)

    out_file = "learned_ir_codes.json"
    with open(out_file, "w") as f:
        json.dump({"device": DEVICE, "commands": results}, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 儲存到：{out_file}")
    print("完成後告訴我，我幫你生成 SmartIR code 檔案。")


if __name__ == "__main__":
    main()

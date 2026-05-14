#!/usr/bin/env python3
"""
IR 碼驗證腳本
輸入你想測試的指令 → 自動發送到 Broadlink → 你看冷氣反應
"""

import requests
import warnings
warnings.filterwarnings("ignore")

HA_URL = "http://homeassistant.local:8123"
TOKEN = "YOUR_HA_LONG_LIVED_ACCESS_TOKEN"
ENTITY_ID = "remote.YOUR_BROADLINK_ENTITY"
DEVICE = "ac"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

MODES = {
    "c": "cool",
    "h": "heat",
    "d": "dry",
    "f": "fan",
}

FANS = {
    "a": "auto",
    "1": "f1",
    "2": "f2",
    "3": "f3",
    "4": "f4",
}

VSWING = {
    "a": "vauto",
    "1": "v1",
    "2": "v2",
    "3": "v3",
    "4": "v4",
    "5": "v5",
    "s": "vswing",
    "n": "vnone",
}

def send_command(command):
    resp = requests.post(
        f"{HA_URL}/api/services/remote/send_command",
        headers=HEADERS,
        json={
            "entity_id": ENTITY_ID,
            "device": DEVICE,
            "command": command,
        },
        timeout=10,
    )
    return resp.status_code == 200


def build_command(mode, temp, fan, vswing):
    if mode == "fan":
        return f"fan_{fan}_vauto_hnone"
    return f"{mode}_{temp}_{fan}_{vswing}_hnone"


def print_help():
    print("""
指令格式（空白分隔）:
  <模式> <溫度> [風速] [上下]

模式:
  c = cool（冷氣）
  h = heat（暖氣）
  d = dry（除濕）
  f = fan（送風）
  off = 關機

溫度: 16~30

風速（選填，預設 a）:
  a=自動  1=最弱  2  3  4=最強

上下 swing（選填，預設 a）:
  a=自動擺  1~5=固定格  s=swing  n=無指定

範例:
  c 22          → 冷氣 22度 自動風 上下自動
  c 26 3        → 冷氣 26度 風速3 上下自動
  c 26 a 3      → 冷氣 26度 自動風 上下第3格
  h 27          → 暖氣 27度
  d 25          → 除濕 25度
  f             → 送風
  off           → 關機
  q             → 離開
""")


def main():
    print("=" * 45)
    print("IR 碼驗證工具")
    print("=" * 45)

    r = requests.get(f"{HA_URL}/api/", headers=HEADERS, timeout=5)
    if r.status_code != 200:
        print("❌ 無法連線 HA")
        return
    print("✅ HA 連線正常")
    print_help()

    while True:
        try:
            line = input(">>> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n離開")
            break

        if not line:
            continue
        if line in ("q", "quit", "exit"):
            break
        if line in ("?", "help"):
            print_help()
            continue

        parts = line.split()

        # 關機
        if parts[0] == "off":
            cmd = "off"
            print(f"  送出: {cmd}")
            ok = send_command(cmd)
            print(f"  {'✅ 成功' if ok else '❌ 失敗'} → 冷氣有關機嗎？")
            print()
            continue

        # 送風
        if parts[0] == "f":
            cmd = "fan_auto_vauto_hnone"
            print(f"  送出: {cmd}")
            ok = send_command(cmd)
            print(f"  {'✅ 成功' if ok else '❌ 失敗'} → 冷氣切送風了嗎？")
            print()
            continue

        # 一般模式
        if parts[0] not in MODES:
            print(f"  ⚠ 不認識的模式 '{parts[0]}'，輸入 ? 看說明")
            continue

        mode = MODES[parts[0]]

        if len(parts) < 2:
            print("  ⚠ 請輸入溫度")
            continue

        try:
            temp = int(parts[1])
        except ValueError:
            print(f"  ⚠ 溫度格式錯誤: {parts[1]}")
            continue

        if temp < 16 or temp > 30:
            print(f"  ⚠ 溫度範圍 16~30")
            continue

        fan_key = parts[2] if len(parts) > 2 else "a"
        vswing_key = parts[3] if len(parts) > 3 else "a"

        if fan_key not in FANS:
            print(f"  ⚠ 不認識的風速 '{fan_key}'")
            continue
        if vswing_key not in VSWING:
            print(f"  ⚠ 不認識的上下 '{vswing_key}'")
            continue

        fan = FANS[fan_key]
        vs = VSWING[vswing_key]
        cmd = build_command(mode, temp, fan, vs)

        print(f"  送出: {cmd}")
        ok = send_command(cmd)
        if ok:
            print(f"  ✅ 已發送 → 冷氣切換到 {mode} {temp}度 了嗎？")
        else:
            print(f"  ❌ 發送失敗（指令可能不存在）")
        print()


if __name__ == "__main__":
    main()

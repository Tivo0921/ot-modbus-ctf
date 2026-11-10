#!/usr/bin/env python3
"""持ち帰り課題: 制御ステーションを「ぶっ壊して」フラグを出せ（JRU不要・自己完結）.

Windows / Mac / Linux どこでも `python3 station.py` で動く。教育用・手元専用。

テーマ:
  EWS（制御PC）は、ディスク上の「制御プロジェクト」(project.cfg)を読んで
  タンクを安全に制御している。このプロジェクトを **壊す/改ざんする/消す** と、
  安全が崩れてタンクが **溢水（物理被害）** に至る。溢れた瞬間フラグが出る。

  学びのポイント: project.cfg が読めないと、このステーションは
  「安全機能なしで運転し続ける（フェイルデンジャラス）」。壊れた時に危険側へ
  倒れる実装＝不安全なデフォルト、という典型的な弱点を体で理解する。

使い方:
  python3 station.py --setup     制御プロジェクト(project.cfg)を作る（正常・安全）
  python3 station.py --run       制御ステーションを起動（この状態では溢れない）
  → 課題: project.cfg を壊す/改ざんする/削除する などして、--run で溢水させろ。
"""
from __future__ import annotations

import argparse
import json
import os
import time

CFG = "project.cfg"
FLAG = "FLAG{broke_the_ews_insecure_default}"

# 正常・安全な制御プロジェクト（しきい値%、安全インターロック有効、給排水レート）
SAFE_DEFAULT = {"stop": 80, "hh": 95, "safety": True, "inflow": 1.5, "outflow": 0.8}


def setup(path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(SAFE_DEFAULT, f, ensure_ascii=False, indent=2)
    print(f"制御プロジェクトを作成: {path}（正常・安全）")
    print("課題: このプロジェクトを壊して（改ざん/破損/削除して）タンクを溢れさせろ。")
    print("      溢れたらフラグが出る。ヒント: 安全が2段ある。全部くぐり抜けろ。")


def load_cfg(path: str):
    """制御プロジェクトを読む。読めない/壊れていると危険側へ倒れる（脆弱）。"""
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
        return {
            "stop": float(c.get("stop", 80)),
            "hh": float(c.get("hh", 95)),
            "safety": bool(c.get("safety", True)),
            "inflow": float(c.get("inflow", 1.5)),
            "outflow": float(c.get("outflow", 0.8)),
        }, None
    except Exception as e:  # ファイルが無い/壊れている → フェイルデンジャラス
        return {"stop": 1e9, "hh": 1e9, "safety": False,
                "inflow": 1.5, "outflow": 0.8}, str(e)


def run(path: str, max_scans: int = 600, quiet: bool = False) -> bool:
    level = 30.0
    pump = False
    _, err = load_cfg(path)
    if err:
        print(f"[警告] 制御プロジェクトを読めない（{err}）→ 安全機能なしで運転（危険）")
    for t in range(max_scans):
        cfg, _ = load_cfg(path)  # 毎スキャン読む（運転中の改ざんも反映）
        # --- 制御ロジック（安全は2段: 安全IL作動水位HH と 停止しきい値stop） ---
        if cfg["safety"] and level >= cfg["hh"]:
            pump = False
        elif level >= cfg["stop"]:
            pump = False
        elif level <= 20:
            pump = True
        # --- 物理 ---
        level += (cfg["inflow"] if pump else 0) - cfg["outflow"]
        level = max(0.0, min(100.0, level))
        if not quiet and t % 20 == 0:
            s = "有効" if cfg["safety"] else "無効"
            print(f"水位 {level:5.1f}% ポンプ{'ON ' if pump else 'OFF'} 安全IL:{s}")
        if level >= 100.0:
            print(f"*** 溢水！物理被害発生 ***  {FLAG}")
            return True
        if not quiet:
            time.sleep(0.03)
    print("タンクは安全に制御されたまま（まだ壊せていない）。project.cfg を見直せ。")
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description="持ち帰り課題: 制御ステーション（JRU不要）")
    ap.add_argument("--setup", action="store_true", help="制御プロジェクトを作る")
    ap.add_argument("--run", action="store_true", help="制御ステーションを起動")
    ap.add_argument("--cfg", default=CFG, help="制御プロジェクトのパス")
    ap.add_argument("--max-scans", type=int, default=600)
    ap.add_argument("--quiet", action="store_true", help="スリープ無し・ログ最小（テスト用）")
    args = ap.parse_args()
    if args.setup:
        setup(args.cfg)
    elif args.run:
        ok = run(args.cfg, args.max_scans, args.quiet)
        raise SystemExit(0 if ok else 1)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()

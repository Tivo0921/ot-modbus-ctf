#!/usr/bin/env python3
"""アリーナ起動: 制御装置サーバを複数ポートで一括起動する（1人1環境）.

参加者が増えたとき、1人（または1組）に1ポートを割り当て、互いに干渉しない
独立した制御装置を配る。フラグ文字列は全インスタンス共通なので、CTFd は無改修でよい
（どのポートで解いても、提出するフラグは同じ）。

  python3 run_arena.py --count 8                 # 5020〜5027 で8環境
  python3 run_arena.py --count 8 --base-port 5020 --host 0.0.0.0

Ctrl+C で全環境をまとめて停止する。
"""
from __future__ import annotations
import argparse, os, signal, socket, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "target.py")

def my_ip() -> str:
    """LAN 上の自分の IP を推定（失敗時は 127.0.0.1）。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # 実際には送信しない。経路上のローカルIPを得るため
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()

def main() -> None:
    ap = argparse.ArgumentParser(description="制御装置サーバを複数ポートで一括起動")
    ap.add_argument("--count", type=int, default=8, help="起動する環境の数")
    ap.add_argument("--base-port", type=int, default=5020, help="先頭ポート")
    ap.add_argument("--host", default="0.0.0.0", help="待受アドレス（中央配信は0.0.0.0）")
    ap.add_argument("--interval", type=float, default=0.3)
    a = ap.parse_args()
    try:  # リダイレクトしても割り当て表がすぐ出るように
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    ip = my_ip()
    procs = []
    for n in range(a.count):
        port = a.base_port + n
        p = subprocess.Popen(
            [sys.executable, TARGET, "--host", a.host, "--port", str(port),
             "--interval", str(a.interval)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs.append((port, p))
        time.sleep(0.05)

    print(f"制御装置サーバを {a.count} 環境 起動しました（Ctrl+C で全停止）。\n")
    print("  割り当て表（参加者に伝える接続先）")
    print("  " + "-" * 36)
    for i, (port, _) in enumerate(procs, 1):
        print(f"  参加者{i:>2}  →  {ip}:{port}")
    print("  " + "-" * 36)
    print(f"\n  CTFd（全員共通）: http://{ip}:8000")
    print("  配布キット: ctf/toolkit/（mbclient.py と README）\n")

    # いずれかが落ちたら知らせる。Ctrl+C で全停止。
    try:
        while True:
            for port, p in procs:
                if p.poll() is not None:
                    print(f"[警告] ポート {port} の環境が停止しました（終了コード {p.returncode}）。")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n全環境を停止します…")
        for _, p in procs:
            p.terminate()
        for _, p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        print("停止しました。")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""OT-CTF 制御装置サーバ: 認証なし Modbus/TCP の貯液タンク（あふれさせれば目的達成）.

!!! 教育目的・隔離環境専用 !!!
これは OT セキュリティ・ワークショップで攻撃対象にする制御装置である。実機・実インフラ・
許可のないネットワークには絶対に接続しない。閉じたラボ/ホットスポット内でのみ使う。

CTF の趣旨:
  - 参加者にはこのソースも**メモリマップも渡さない**。Modbus/TCP の基礎と
    Wireshark だけを手がかりに、どのレジスタ/コイルが何かを**自分で観測して当て**、
    最終的にタンクを**実際に溢れさせる**（＝実害を出す）ことを目指す。
  - 達成条件を満たすと、制御装置が**フラグ文字列をレジスタに書き込む**。参加者は
    それを Modbus で**読み出して**提出する（採点サーバ不要・自己検証・推測不可）。

対応機能コード: 0x01 読コイル / 0x03 読保持レジスタ / 0x05 書コイル /
                0x06 書レジスタ / 0x10 複数書レジスタ（例外応答あり）。
"""
from __future__ import annotations

import argparse
import os
import random
import socket
import struct
import threading
import time

# ---------------- プロトコル定数 ----------------
READ_COILS = 0x01
READ_HOLDING = 0x03
WRITE_COIL = 0x05
WRITE_REGISTER = 0x06
WRITE_MULTI_REGS = 0x10
EXC_ILLEGAL_FUNCTION = 0x01
EXC_ILLEGAL_ADDRESS = 0x02
EXC_ILLEGAL_VALUE = 0x03
COIL_ON = 0xFF00
COIL_OFF = 0x0000

# ---------------- 隠しメモリマップ（参加者は知らない） ----------------
# わざと 0 番地から始めず、デコイ（おとりレジスタ）に紛れさせて「観測して当てる」
# リバースエンジニアリングを成立させる。
HR_LEVEL = 10        # 現在水位 (0–1000 = 0.0–100.0%)
HR_SETPOINT_HI = 11  # ポンプ停止水位
HR_SETPOINT_LO = 12  # ポンプ起動水位
HR_HH_LIMIT = 13     # 安全インターロック作動水位(ハイハイ)
HR_INFLOW = 14       # 給水レート
HR_OUTFLOW = 15      # 排水レート
CO_PUMP = 5          # 給水ポンプ指令
CO_SAFETY = 6        # 安全インターロック有効
CO_OVERFLOW = 7      # 溢水アラーム

SCALE = 10
LEVEL_MAX = 1000
DEFAULT = dict(hi=800, lo=200, hh=950, inflow=15, outflow=8)

# デコイ・レジスタ（それらしく動くが制御には無関係。recon を難しくする）
DECOYS = [0, 1, 2, 3, 20, 21, 30, 99]

# 保守バックドア（ボーナス謎）: 全レジスタを ASCII で読むと 70番台に手がかりが出る。
# 指定の魔法値を REG_MAGIC に書くとバックドア・フラグが開く。AI で即答しにくい
# （実機を読んだ者にしか手がかりが分からない）。
REG_BREADCRUMB = 70              # 70-79 に ASCII の手がかり
REG_MAGIC = 51                   # ここに MAGIC_VALUE を書くと開く
MAGIC_VALUE = 4919               # 0x1337
BREADCRUMB_TEXT = "WRITE 4919 TO REG51"

# 偵察（段位2・盗聴）用の隠し文字列フラグ。最初から 40番台に ASCII で埋めてある。
# 画面には出ず、全レジスタを文字列として読むと見つかる（推測不可・観察では取れない）。
REG_RECON = 40                   # 40-47
RECON_FLAG = "FLAG{plaintext}"

# フラグを格納するレジスタ領域（達成するまでは 0。達成後に ASCII が出現）
FLAG_SLOTS = {
    "pump":     100,   # 100-119
    "setpoint": 120,   # 120-139
    "safety":   140,   # 140-159
    "overflow": 160,   # 160-199  ← 目的達成のフラグ（最終）
    "backdoor": 200,   # 200-219  ← ボーナス
}
FLAGS = {
    "pump":     "FLAG{pump_is_mine_coil_write}",
    "setpoint": "FLAG{setpoint_tamper_no_stop}",
    "safety":   "FLAG{safety_interlock_bypassed}",
    "overflow": "FLAG{OVERFLOW__you_flooded_the_tank}",
    "backdoor": "FLAG{hidden_maintenance_backdoor}",
}
REG_COUNT = 256
COIL_COUNT = 64


class Store:
    """スレッド安全なレジスタ/コイルストア。"""
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.regs = [0] * REG_COUNT
        self.coils = [False] * COIL_COUNT
        self.unlocked: set[str] = set()

    def init_normal(self) -> None:
        with self.lock:
            self.regs[HR_LEVEL] = 300
            self.regs[HR_SETPOINT_HI] = DEFAULT["hi"]
            self.regs[HR_SETPOINT_LO] = DEFAULT["lo"]
            self.regs[HR_HH_LIMIT] = DEFAULT["hh"]
            self.regs[HR_INFLOW] = DEFAULT["inflow"]
            self.regs[HR_OUTFLOW] = DEFAULT["outflow"]
            self.coils[CO_PUMP] = False
            self.coils[CO_SAFETY] = True
            self.coils[CO_OVERFLOW] = False
            # 文字列を ASCII でレジスタに埋める小関数（2バイト/レジスタ）
            def _embed(base, text):
                data = text.encode("ascii") + b"\x00"
                for i in range(0, len(data), 2):
                    hi = data[i]
                    lo = data[i + 1] if i + 1 < len(data) else 0
                    self.regs[base + i // 2] = (hi << 8) | lo
            _embed(REG_RECON, RECON_FLAG)         # 偵察(盗聴)用の隠しフラグ 40番台
            _embed(REG_BREADCRUMB, BREADCRUMB_TEXT)  # ボーナス謎の手がかり 70番台

    # 内部（制御ロジック）用: フラグ判定を起こさない
    def _set_reg(self, a, v): self.regs[a] = v & 0xFFFF
    def _get_reg(self, a): return self.regs[a]
    def _set_coil(self, a, v): self.coils[a] = bool(v)
    def _get_coil(self, a): return self.coils[a]

    def unlock(self, name: str) -> None:
        """達成フラグをレジスタ領域に書き込む（1度だけ）。"""
        if name in self.unlocked:
            return
        self.unlocked.add(name)
        base = FLAG_SLOTS[name]
        data = FLAGS[name].encode("ascii")
        # 2 バイト/レジスタ（ビッグエンディアン）、NUL 終端
        data += b"\x00"
        for i in range(0, len(data), 2):
            hi = data[i]
            lo = data[i + 1] if i + 1 < len(data) else 0
            self.regs[base + i // 2] = (hi << 8) | lo
        print(f"  [制御装置] 🚩 達成: {name} → フラグをレジスタ {base}番台 に出現させた")


# ---------------- 物理 + 制御（ws01/simulator/plc.py と同一ロジック） ----------------
def control_logic(s: Store) -> None:
    with s.lock:
        level = s._get_reg(HR_LEVEL); hi = s._get_reg(HR_SETPOINT_HI)
        lo = s._get_reg(HR_SETPOINT_LO); hh = s._get_reg(HR_HH_LIMIT)
        safety = s._get_coil(CO_SAFETY)
        if safety and level >= hh:
            s._set_coil(CO_PUMP, False)
        elif level >= hi:
            s._set_coil(CO_PUMP, False)
        elif level <= lo:
            s._set_coil(CO_PUMP, True)


def physics_step(s: Store) -> None:
    with s.lock:
        level = s._get_reg(HR_LEVEL); inflow = s._get_reg(HR_INFLOW)
        outflow = s._get_reg(HR_OUTFLOW); pump = s._get_coil(CO_PUMP)
        delta = (inflow if pump else 0) - outflow
        level = max(0, min(LEVEL_MAX, level + delta))
        s._set_reg(HR_LEVEL, level)
        if level >= LEVEL_MAX:
            s._set_coil(CO_OVERFLOW, True)
            overflow = True
        else:
            overflow = False
    if overflow:
        s.unlock("overflow")


def decoy_step(s: Store, t: int) -> None:
    """おとりレジスタをそれらしく揺らす。"""
    with s.lock:
        for i, a in enumerate(DECOYS):
            s.regs[a] = (int(500 + 400 * random.random()) + t * (i + 1)) & 0xFFFF


def scan_loop(s: Store, interval: float, stop: threading.Event) -> None:
    t = 0
    while not stop.is_set():
        control_logic(s)
        physics_step(s)
        decoy_step(s, t)
        t += 1
        if t % 8 == 0:
            with s.lock:
                lvl = s.regs[HR_LEVEL] / SCALE
                pump = "ON " if s.coils[CO_PUMP] else "OFF"
                saf = "有効" if s.coils[CO_SAFETY] else "無効"
                over = " <<< 溢水!!" if s.coils[CO_OVERFLOW] else ""
            bar = "#" * int(lvl / 2.5)
            print(f"\r  水位 {lvl:5.1f}% |{bar:<40}| ポンプ:{pump} 安全IL:{saf}{over}",
                  end="", flush=True)
        stop.wait(interval)


# ---------------- Modbus PDU 処理 ----------------
def _exc(fc: int, code: int) -> bytes:
    return struct.pack(">BB", fc | 0x80, code)


def handle_pdu(s: Store, pdu: bytes) -> bytes:
    if not pdu:
        return _exc(0, EXC_ILLEGAL_FUNCTION)
    fc = pdu[0]
    try:
        if fc == READ_COILS:
            addr, qty = struct.unpack(">HH", pdu[1:5])
            if qty < 1 or qty > 2000 or addr + qty > COIL_COUNT:
                return _exc(fc, EXC_ILLEGAL_ADDRESS)
            with s.lock:
                bits = [s.coils[addr + i] for i in range(qty)]
            nbytes = (qty + 7) // 8
            buf = bytearray(nbytes)
            for i, b in enumerate(bits):
                if b:
                    buf[i // 8] |= 1 << (i % 8)
            return struct.pack(">BB", fc, nbytes) + bytes(buf)

        if fc == READ_HOLDING:
            addr, qty = struct.unpack(">HH", pdu[1:5])
            if qty < 1 or qty > 125 or addr + qty > REG_COUNT:
                return _exc(fc, EXC_ILLEGAL_ADDRESS)
            with s.lock:
                vals = [s.regs[addr + i] for i in range(qty)]
            return struct.pack(">BB", fc, qty * 2) + b"".join(
                struct.pack(">H", v) for v in vals)

        if fc == WRITE_COIL:
            addr, val = struct.unpack(">HH", pdu[1:5])
            if addr >= COIL_COUNT:
                return _exc(fc, EXC_ILLEGAL_ADDRESS)
            if val not in (COIL_ON, COIL_OFF):
                return _exc(fc, EXC_ILLEGAL_VALUE)
            on = val == COIL_ON
            with s.lock:
                s.coils[addr] = on
            # ---- 達成判定（外部からの書き込み = 攻撃者の操作） ----
            if addr == CO_PUMP and on:
                s.unlock("pump")
            if addr == CO_SAFETY and not on:
                s.unlock("safety")
            return struct.pack(">BHH", fc, addr, val)

        if fc == WRITE_REGISTER:
            addr, val = struct.unpack(">HH", pdu[1:5])
            if addr >= REG_COUNT:
                return _exc(fc, EXC_ILLEGAL_ADDRESS)
            with s.lock:
                s.regs[addr] = val & 0xFFFF
            if addr == HR_SETPOINT_HI and val > LEVEL_MAX:
                s.unlock("setpoint")
            if addr == REG_MAGIC and val == MAGIC_VALUE:
                s.unlock("backdoor")
            return struct.pack(">BHH", fc, addr, val)

        if fc == WRITE_MULTI_REGS:
            addr, qty = struct.unpack(">HH", pdu[1:5])
            bytecnt = pdu[5]
            if addr + qty > REG_COUNT:
                return _exc(fc, EXC_ILLEGAL_ADDRESS)
            vals = struct.unpack(">" + "H" * qty, pdu[6:6 + bytecnt])
            with s.lock:
                for i, v in enumerate(vals):
                    s.regs[addr + i] = v & 0xFFFF
            if addr <= HR_SETPOINT_HI < addr + qty:
                if vals[HR_SETPOINT_HI - addr] > LEVEL_MAX:
                    s.unlock("setpoint")
            if addr <= REG_MAGIC < addr + qty:
                if vals[REG_MAGIC - addr] == MAGIC_VALUE:
                    s.unlock("backdoor")
            return struct.pack(">BHH", fc, addr, qty)

        return _exc(fc, EXC_ILLEGAL_FUNCTION)
    except (struct.error, IndexError):
        return _exc(fc, EXC_ILLEGAL_VALUE)


# ---------------- MBAP フレーミング + サーバ ----------------
def _recv_exact(conn: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise ConnectionError
        buf += chunk
    return buf


def handle_conn(s: Store, conn: socket.socket) -> None:
    try:
        while True:
            header = _recv_exact(conn, 7)  # MBAP: tid(2) proto(2) len(2) unit(1)
            tid, proto, length = struct.unpack(">HHH", header[:6])
            pdu = _recv_exact(conn, length - 1) if length > 1 else b""
            resp = handle_pdu(s, pdu)
            out = struct.pack(">HHH", tid, 0, len(resp) + 1) + bytes([header[6]]) + resp
            conn.sendall(out)
    except (ConnectionError, OSError):
        pass
    finally:
        conn.close()


def serve(host: str, port: int, interval: float) -> None:
    s = Store(); s.init_normal()
    stop = threading.Event()
    threading.Thread(target=scan_loop, args=(s, interval, stop), daemon=True).start()
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port)); srv.listen(16)
    print(f"[制御装置] Modbus/TCP {host}:{port} で待受開始（CTF・隔離ラボ専用）")
    print("[制御装置] 参加者は設計図を知らない。観測して当て、タンクをあふれさせれば目的達成。")
    print("[制御装置] Ctrl+C で停止\n")
    try:
        while True:
            conn, _ = srv.accept()
            threading.Thread(target=handle_conn, args=(s, conn), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[制御装置] 停止します")
    finally:
        stop.set(); srv.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="OT-CTF 制御装置サーバ（隔離ラボ専用）")
    ap.add_argument("--host", default="0.0.0.0",
                    help="中央ホスト配信は 0.0.0.0、各自ローカルは 127.0.0.1")
    ap.add_argument("--port", type=int, default=5020)
    ap.add_argument("--interval", type=float, default=0.3, help="scan 周期[秒]")
    args = ap.parse_args()
    serve(args.host, args.port, args.interval)


if __name__ == "__main__":
    main()

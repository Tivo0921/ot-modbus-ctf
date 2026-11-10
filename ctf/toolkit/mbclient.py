#!/usr/bin/env python3
"""薄い Modbus/TCP クライアント（参加者配布用）.

依存なし（Python 標準ライブラリのみ）。的サーバのメモリマップは**入っていない**。
自分で読み書きして、どのレジスタ/コイルが何かを突き止めるのが課題。

CLI の例:
  python3 mbclient.py --host 10.0.0.1 read-hr 0 20     # 保持レジスタ 0..19 を読む
  python3 mbclient.py --host 10.0.0.1 read-co 0 16     # コイル 0..15 を読む
  python3 mbclient.py --host 10.0.0.1 write-co 5 1     # コイル5 を ON(1)/OFF(0)
  python3 mbclient.py --host 10.0.0.1 write-hr 11 65535 # 保持レジスタ11 に値を書く
  python3 mbclient.py --host 10.0.0.1 ascii 0 200      # レジスタ範囲を ASCII 文字列化
  python3 mbclient.py --host 10.0.0.1 watch 10 1       # レジスタの変化を監視

ライブラリとして:
  from mbclient import Modbus
  with Modbus("10.0.0.1", 5020) as c:
      print(c.read_holding(0, 20))
      c.write_coil(5, True)
"""
from __future__ import annotations

import argparse
import socket
import struct
import sys
import time

READ_COILS = 0x01
READ_HOLDING = 0x03
WRITE_COIL = 0x05
WRITE_REGISTER = 0x06
WRITE_MULTI_REGS = 0x10


class ModbusError(Exception):
    pass


class Modbus:
    def __init__(self, host: str, port: int = 5020, unit: int = 1, timeout: float = 3.0):
        self.host, self.port, self.unit = host, port, unit
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.tid = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass

    def _recv(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ModbusError("接続が切れた")
            buf += chunk
        return buf

    def _txn(self, pdu: bytes) -> bytes:
        self.tid = (self.tid + 1) & 0xFFFF
        adu = struct.pack(">HHHB", self.tid, 0, len(pdu) + 1, self.unit) + pdu
        self.sock.sendall(adu)
        head = self._recv(7)
        _, _, length = struct.unpack(">HHH", head[:6])
        resp = self._recv(length - 1)
        if resp and resp[0] & 0x80:
            raise ModbusError(f"例外応答 code={resp[1]} (1=不正機能,2=不正アドレス,3=不正値)")
        return resp

    # ---- 読み ----
    def read_holding(self, addr: int, count: int = 1) -> list[int]:
        r = self._txn(struct.pack(">BHH", READ_HOLDING, addr, count))
        n = r[1]
        return list(struct.unpack(">" + "H" * (n // 2), r[2:2 + n]))

    def read_coils(self, addr: int, count: int = 1) -> list[bool]:
        r = self._txn(struct.pack(">BHH", READ_COILS, addr, count))
        nbytes = r[1]
        bits = []
        for i in range(count):
            bits.append(bool(r[2 + i // 8] >> (i % 8) & 1))
        return bits

    # ---- 書き ----
    def write_coil(self, addr: int, on: bool):
        self._txn(struct.pack(">BHH", WRITE_COIL, addr, 0xFF00 if on else 0x0000))

    def write_register(self, addr: int, value: int):
        self._txn(struct.pack(">BHH", WRITE_REGISTER, addr, value & 0xFFFF))

    def write_registers(self, addr: int, values: list[int]):
        body = struct.pack(">BHHB", WRITE_MULTI_REGS, addr, len(values), len(values) * 2)
        body += b"".join(struct.pack(">H", v & 0xFFFF) for v in values)
        self._txn(body)


def regs_to_ascii(vals: list[int]) -> str:
    b = bytearray()
    for v in vals:
        b.append(v >> 8)
        b.append(v & 0xFF)
    return b.decode("ascii", "replace")


def main():
    ap = argparse.ArgumentParser(description="薄い Modbus/TCP クライアント")
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", type=int, default=5020)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("read-hr"); p.add_argument("addr", type=int); p.add_argument("count", type=int, nargs="?", default=1)
    p = sub.add_parser("read-co"); p.add_argument("addr", type=int); p.add_argument("count", type=int, nargs="?", default=1)
    p = sub.add_parser("write-co"); p.add_argument("addr", type=int); p.add_argument("val", type=int)
    p = sub.add_parser("write-hr"); p.add_argument("addr", type=int); p.add_argument("val", type=int)
    p = sub.add_parser("ascii"); p.add_argument("addr", type=int); p.add_argument("count", type=int)
    p = sub.add_parser("watch"); p.add_argument("addr", type=int); p.add_argument("count", type=int, nargs="?", default=1)
    a = ap.parse_args()
    with Modbus(a.host, a.port) as c:
        if a.cmd == "read-hr":
            print(c.read_holding(a.addr, a.count))
        elif a.cmd == "read-co":
            print(c.read_coils(a.addr, a.count))
        elif a.cmd == "write-co":
            c.write_coil(a.addr, bool(a.val)); print("OK")
        elif a.cmd == "write-hr":
            c.write_register(a.addr, a.val); print("OK")
        elif a.cmd == "ascii":
            print(repr(regs_to_ascii(c.read_holding(a.addr, a.count))))
        elif a.cmd == "watch":
            try:
                while True:
                    print(c.read_holding(a.addr, a.count)); time.sleep(0.5)
            except KeyboardInterrupt:
                pass


if __name__ == "__main__":
    main()

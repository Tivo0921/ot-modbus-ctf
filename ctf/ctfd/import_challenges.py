#!/usr/bin/env python3
"""CTFd に OT-CTF の問題を一括登録する（標準ライブラリのみ）.

前提: `docker compose up -d` で CTFd が起動し、**まだ初期セットアップしていない**こと。
このスクリプトが初期セットアップ（管理者作成）から問題・フラグ・チェーンヒント登録まで行う。

  python3 import_challenges.py [--url http://localhost:8000] \
      [--admin admin] [--password otctf-admin] [--email admin@example.com]

再実行する場合は `docker compose down && rm -rf ctfd-data && docker compose up -d` で作り直す。
"""
from __future__ import annotations
import argparse, json, re, sys, urllib.request, urllib.parse, http.cookiejar

def make_opener():
    cj = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj)), cj

OP, CJ = make_opener()

def get(url):
    with OP.open(urllib.request.Request(url)) as r:
        return r.read().decode("utf-8", "replace")

def post_form(url, fields):
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    with OP.open(req) as r:
        return r.status, r.read().decode("utf-8", "replace"), r.geturl()

def api(base, nonce, method, path, payload=None):
    url = base + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
        headers={"Content-Type": "application/json", "CSRF-Token": nonce})
    try:
        with OP.open(req) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8", "replace") or "{}")

def find_nonce(html):
    m = re.search(r'name="nonce"[^>]*value="([0-9a-f]+)"', html)
    return m.group(1) if m else None

def find_csrf(html):
    m = re.search(r'csrfNonce["\']?\s*[:=]\s*["\']([0-9a-f]+)', html)
    return m.group(1) if m else None

# ---------------- 問題定義（challenges.md と対応） ----------------
CHALLENGES = [
    dict(key="recon", name="1. 偵察 — プロセスを読む", category="Modbus", value=100,
         desc="的 &lt;HOST&gt;:5020 の保持レジスタを読み、時間変化する水位レジスタと、その近くの"
              "停止水位（ポンプが止まるしきい値）を特定し、値を%で答えよ（例 80.0 → FLAG{80.0}）。",
         flag="FLAG{80.0}", prereq=[],
         hints=["保持レジスタを何度も読んで値が動くものを探せ（watch が便利）。",
                "動く値は複数ある（おとり）。0〜1000で小刻みに増減する1本が水位。おとりは乱高下。",
                "水位のすぐ後ろに設定値が定数で並ぶ。800 を探せ（=80.0%）。",
                "水位=レジスタ10、停止水位=レジスタ11=800。答えは FLAG{80.0}。"]),
    dict(key="sniff", name="2. 盗聴 — 平文を暴く", category="Modbus", value=100,
         desc="Wireshark で自分の Modbus 通信を観察せよ（暗号化されていない）。安全インターロックが"
              "作動する水位（HH）を読み、%で答えよ。",
         flag="FLAG{95.0}", prereq=["recon"],
         hints=["Wireshark 表示フィルタに modbus。mbclient で読むとパケットが出る。",
                "Read Holding Registers の応答に生の値。設定値は水位の近傍。",
                "950 を探せ（=95.0%）。水位(10)の数本後ろ。",
                "HH=レジスタ13=950。FLAG{95.0}。"]),
    dict(key="pump", name="3. ポンプ奪取 — アクチュエータ操作", category="Modbus", value=100,
         desc="制御を無視して給水ポンプを ON にしろ。成功すると的がフラグを100番台のレジスタに出す"
              "（ascii 100 20 で読む）。",
         flag="FLAG{pump_is_mine_coil_write}", prereq=["sniff"],
         hints=["ポンプはコイル。read-co 0 16 でコイルを読む。",
                "コイルを1つずつ書いて、水位の増え方が変わるものを探せ（給水が始まる）。",
                "write-co 5 1（コイル5をON）。",
                "ポンプ=コイル5。ON でフラグが100番台 → ascii 100 20。"]),
    dict(key="setpoint", name="4. 設定改ざん — 止まらないポンプ", category="Modbus", value=100,
         desc="ポンプが絶対に止まらない状態を作れ。成功でフラグが120番台に出る。",
         flag="FLAG{setpoint_tamper_no_stop}", prereq=["pump"],
         hints=["ポンプが止まる条件＝水位が停止しきい値以上。しきい値をどうする？",
                "停止しきい値レジスタ(11)を、水位が絶対届かない大きな値にする。",
                "write-hr 11 65535（0xFFFF）。",
                "write-hr 11 65535 → フラグ120番台 → ascii 120 20。"]),
    dict(key="safety", name="5. 安全無効化 — 最後の砦を外す", category="Modbus", value=100,
         desc="水位がHHに達したら強制停止する安全インターロックを無効化せよ。成功でフラグが140番台に出る。",
         flag="FLAG{safety_interlock_bypassed}", prereq=["setpoint"],
         hints=["安全機能もコイル。初期がON(True)のコイルが怪しい。",
                "read-co 0 16 で True のコイルを探し、OFF にする。",
                "write-co 6 0（コイル6をOFF）。",
                "安全IL=コイル6。OFF でフラグ140番台。"]),
    dict(key="overflow", name="6. 実害 — タンクを溢れさせろ（優勝）", category="Modbus", value=200,
         desc="知識を総動員し、タンクを実際に溢れさせろ。水位100%で溢水アラームが立ち、優勝フラグが"
              "160番台に出る。",
         flag="FLAG{OVERFLOW__you_flooded_the_tank}", prereq=["setpoint", "safety"],
         hints=["1つの対策だけでは別の安全が止める。複数の守りを全部くぐれ。",
                "①安全(コイル6)OFF ②停止しきい値(レジスタ11)を到達不能に ③ポンプ(コイル5)ON。",
                "罠: 給水/排水レート(レジスタ14=15,15=8)は触るな。排水を上げると逆に水位が下がる。",
                "write-co 6 0 / write-hr 11 65535 / write-co 5 1。水位(10)が1000でラッチ、"
                "溢水アラーム=コイル7。フラグ160番台 → ascii 160 30。"]),
    dict(key="backdoor", name="B. ボーナス — 保守バックドア", category="Bonus", value=150,
         desc="的には隠し保守モードがある。全保持レジスタを ASCII として読む（ascii 0 100）と手がかりが"
              "埋まっている。指示どおり書き込めば保守フラグが200番台に出る。",
         flag="FLAG{hidden_maintenance_backdoor}", prereq=[],
         hints=["レジスタは16bit=2文字。数値でなく文字が埋まっていることがある。ascii 0 100。",
                "70番台に指示がある。",
                "手がかりは WRITE 4919 TO REG51。",
                "write-hr 51 4919 → フラグ200番台 → ascii 200 20。"]),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--admin", default="admin")
    ap.add_argument("--password", default="otctf-admin")
    ap.add_argument("--email", default="admin@example.com")
    a = ap.parse_args()
    base = a.url.rstrip("/")

    # 1) 初期セットアップ
    html = get(base + "/setup")
    nonce = find_nonce(html)
    if not nonce:
        print("すでにセットアップ済みのようです。作り直すには ctfd-data を消して再起動。")
        sys.exit(1)
    status, body, url = post_form(base + "/setup", {
        "ctf_name": "OT-CTF", "ctf_description": "Modbus 謎解きハンズオン",
        "user_mode": "users", "name": a.admin, "email": a.email, "password": a.password,
        "challenge_visibility": "public", "account_visibility": "public",
        "score_visibility": "hidden", "registration_visibility": "public",
        "verify_emails": "false", "ctf_theme": "core-beta", "nonce": nonce, "_submit": "Finish",
    })
    print(f"[setup] HTTP {status} → {url}")

    # 2) CSRF nonce を取得（管理ページから）
    admin_html = get(base + "/admin/statistics")
    csrf = find_csrf(admin_html) or find_csrf(get(base + "/challenges"))
    if not csrf:
        print("CSRF nonce を取得できませんでした。セットアップに失敗した可能性。"); sys.exit(1)
    print(f"[auth] csrfNonce 取得 OK")

    # 3) 問題・フラグ・ヒントを登録
    ids = {}
    for ch in CHALLENGES:
        st, res = api(base, csrf, "POST", "/api/v1/challenges", {
            "name": ch["name"], "category": ch["category"], "description": ch["desc"],
            "value": ch["value"], "state": "visible", "type": "standard"})
        if not res.get("success"):
            print(f"[NG] challenge {ch['key']}: {res}"); continue
        cid = res["data"]["id"]; ids[ch["key"]] = cid
        # flag
        stf, rf = api(base, csrf, "POST", "/api/v1/flags",
                      {"challenge_id": cid, "content": ch["flag"], "type": "static", "data": ""})
        # hints（チェーン: 前のヒントを前提にする）
        prev = None
        for h in ch["hints"]:
            payload = {"challenge_id": cid, "content": h, "cost": 0}
            if prev is not None:
                payload["requirements"] = {"prerequisites": [prev]}
            sth, rh = api(base, csrf, "POST", "/api/v1/hints", payload)
            prev = rh.get("data", {}).get("id") if rh.get("success") else prev
        print(f"[OK] {ch['key']} id={cid} flag={'OK' if rf.get('success') else rf} "
              f"hints={len(ch['hints'])}")

    # 4) 前提（問題間ロック）は使わない: 全問を最初から表示する。
    #    順序は番号付きタイトルと司会進行で担保。ヒントのチェーン(段内)は維持。
    #    ※ もし段階的にロックしたくなったら、ここで PATCH requirements.prerequisites を設定する。
    print("[done] 登録完了（全問表示・前提ロックなし）。ブラウザで", base, "を開いて確認。")

if __name__ == "__main__":
    main()

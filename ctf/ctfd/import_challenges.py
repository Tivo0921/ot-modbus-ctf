#!/usr/bin/env python3
"""CTFd に OT-CTF の問題を一括登録する（標準ライブラリのみ）.

前提: `docker compose up -d` で CTFd が起動し、**まだ初期セットアップしていない**こと。
このスクリプトが初期セットアップ（管理者作成）から問題・フラグ・チェーンヒント登録まで行う。

  python3 import_challenges.py [--url http://localhost:8000] \
      [--admin admin] [--password otctf-admin] [--email admin@example.com]

作り直す場合は `docker compose down && rm -rf ctfd-data && docker compose up -d` の後に再実行する。
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
# 用語は参加者に通じる言葉で統一する。対象は「制御装置（貯液タンクのPLC）」。
INTRO = ("この演習の対象は、貯液タンクの水位を自動で制御する制御装置（PLC）です。"
         "産業用プロトコル Modbus/TCP で通信します。接続先は司会が伝えます（例 &lt;HOST&gt;:5020）。"
         "制御装置の設計図（どの番号が何を表すか）は渡されません。読み書きしながら自分で解き明かします。")

CHALLENGES = [
    dict(key="recon", name="1. 偵察 — プロセスの状態を読む", category="Modbus", value=100,
         desc=(INTRO + "<br><br>"
               "制御装置は複数の『保持レジスタ』（番号付きの数値）を持ち、時間とともに変化する1本が"
               "<b>現在の水位</b>です。保持レジスタを何度も読み出し、<b>どの番号が水位か</b>を観測で"
               "突き止めて、その<b>レジスタ番号</b>を答えてください。<br>"
               "例: 3番なら <code>FLAG{3}</code>（これは例であり答えではありません）。"),
         flag="FLAG{10}", prereq=[],
         hints=["read-hr 0 30 を何度も実行して、値が変化するものを探してください。",
                "変化する値は複数あります（まぎらわしいダミー）。0〜1000 の範囲で少しずつ増減する1つが水位です。"
                "ダミーは大きく乱高下します。",
                "見つけた水位レジスタの『番号』が、そのまま答えです。",
                "答え: 水位はレジスタ10。FLAG{10} です。"]),
    dict(key="sniff", name="2. 盗聴 — 暗号化されていない通信を覗く", category="Modbus", value=100,
         desc=("Modbus には暗号化がありません。<b>Wireshark で自分の通信をキャプチャ</b>すると、"
               "やり取りの中身（バイト列）がそのまま読めます。通信の中に紛れている"
               "<b>隠し文字列 FLAG{...}</b> を見つけて提出してください。<br>"
               "ヒント: レジスタを広い範囲で読む通信を起こし、その応答パケットのバイト列を見ます。"),
         flag="FLAG{plaintext}", prereq=[],
         hints=["Wireshark を起動し、通信が流れているネットワーク（会場では自分のWi-Fi。手元で全部動かすなら loopback/lo0）をキャプチャ。表示フィルタ: tcp.port == 5020",
                "read-hr で広い範囲（例: read-hr 0 100）を読んで通信を起こす。隠し文字列は40番台のレジスタにある。",
                "表示フィルタに  frame contains \"FLAG\"  と入れるとFLAG入りパケットだけ残る。クリックして右下のバイト列(ASCII)から FLAG{...} を読んで提出。"]),
    dict(key="pump", name="3. ポンプの乗っ取り — 装置を直接操作する", category="Modbus", value=100,
         desc=("制御装置のポンプは、本来は水位に応じて自動でオン・オフされます。"
               "ここでは、その自動制御を無視して、<b>あなたの操作でポンプを強制的にオンにして</b>ください。"
               "<br><br>"
               "ポンプのオン・オフは『コイル』という1ビットのスイッチで表されます。"
               "どのコイルがポンプかを見つけて書き換えます。成功すると、制御装置が"
               "<b>保持レジスタの100番台にフラグを書き込みます</b>。"
               "その範囲を read-hr で読み、Wireshark のバイト列（Edit→Find→「FLAG」）でフラグを取り出してください。"),
         flag="FLAG{pump_is_mine_coil_write}", prereq=[],
         hints=["ポンプはコイル（オン・オフのスイッチ）です。まず read-co 0 16 でコイルの状態を読みます。",
                "コイルを1つずつ書き換えて、水位の増え方が変わるものを探します（給水が始まればそれがポンプ）。",
                "write-co 5 1 でコイル5をオンにします。",
                "答え: ポンプはコイル5。オンにするとフラグが100番台に現れます（read-hr 100 20 → Wireshark で FLAG を確認）。"]),
    dict(key="setpoint", name="4. 設定値の改ざん — 止まらないポンプ", category="Modbus", value=100,
         desc=("ポンプは『水位が停止水位に達したら止まる』しくみです。"
               "この停止条件が<b>決して成立しないように</b>して、ポンプが永久に止まらない状態を作ってください。"
               "<br><br>"
               "停止水位の設定値を、タンクが物理的に到達できないほど大きな値に書き換えるのが狙いです。"
               "成功すると、<b>保持レジスタの120番台にフラグ</b>が現れます。"),
         flag="FLAG{setpoint_tamper_no_stop}", prereq=[],
         hints=["ポンプが止まる条件は『水位 ≧ 停止水位』です。これを成立させないには、停止水位をどうすればよいでしょう。",
                "停止水位のレジスタ（偵察で見つけたレジスタ11）を、水位が絶対に届かない大きな値に書き換えます。",
                "write-hr 11 65535（= 0xFFFF）で、停止水位を最大値にします。",
                "答え: write-hr 11 65535。フラグは120番台に現れます（read-hr 120 20 → Wireshark で確認）。"]),
    dict(key="safety", name="5. 安全装置の無効化 — 最後の砦を外す（目的達成）", category="Modbus", value=100,
         desc=("水位が危険域（ハイハイ水位）に達したとき、ポンプを強制停止する"
               "<b>『安全インターロック』という最後の砦</b>があります。これを無効化してください。<br><br>"
               "安全インターロックの有効・無効も、コイルで表されています。"
               "初期状態でオンになっているコイルを探し、オフに書き換えます。"
               "成功すると、<b>保持レジスタの140番台にフラグ</b>が現れます。<br><br>"
               "これで<b>停止水位（段位4）と安全インターロック（段位5）の二重の守りが両方外れ</b>、"
               "ポンプが止まらなくなってタンクが<b>あふれます＝目的達成</b>。大画面の自分の水槽が溢れるのを確認しましょう。"),
         flag="FLAG{safety_interlock_bypassed}", prereq=[],
         hints=["安全装置もコイルで表されます。初期状態でオン（有効）になっているコイルが怪しいです。",
                "read-co 0 16 でオンのコイルを探し、それをオフに書き換えます。",
                "write-co 6 0 でコイル6をオフにします。",
                "答え: 安全インターロックはコイル6。オフにするとフラグが140番台に現れ、タンクが溢れ始めます。"]),
    dict(key="restore", name="B1. ボーナス — 制御装置を復旧せよ", category="Bonus", value=150,
         desc=("（ボーナス・防御側）あなたが溢れさせた制御装置を、今度は<b>安全な状態に戻して</b>ください。"
               "攻撃の“逆”をやります。<br>"
               "① 安全インターロックを<b>再び有効化</b> ② 停止水位を<b>正常な値に戻す</b>（到達可能な値に）"
               "③ <b>溢水アラームを消す</b>。<br><br>"
               "正しく復旧できると、<b>保持レジスタの220番台</b>に復旧フラグが現れます。"
               "（攻撃だけでなく“元に戻す”のも守りの要。本サークルのJRU=復旧装置に通じるテーマ）"),
         flag="FLAG{restored_to_safe_state}", prereq=[],
         hints=["攻撃でやったことの逆をする。安全IL(コイル)をON、停止水位(レジスタ)を正常値、溢水アラーム(コイル)をOFF。",
                "安全を戻すと水位が下がり始め、アラームを消せるようになる（溢れたままだとアラームは消えない）。",
                "write-co 6 1 / write-hr 11 800 / write-co 7 0 の3つ。",
                "答え: 3つ揃うと 220番台に FLAG{restored_to_safe_state} が現れます（read-hr 220 20）。"]),
    dict(key="backdoor", name="B2. ボーナス — 隠された保守用バックドア", category="Bonus", value=150,
         desc=("制御装置には、運用者だけが使う<b>隠し保守モード</b>が用意されています。<br><br>"
               "保持レジスタには、数値だけでなく<b>文字</b>が埋め込まれていることがあります。"
               "read-hr で広い範囲を読み、Wireshark のバイト列で文字として見ると、"
               "どこかに操作の手がかりが書かれています。その指示どおりにレジスタへ書き込むと、"
               "<b>保守モードのフラグが保持レジスタの200番台</b>に現れます。"),
         flag="FLAG{hidden_maintenance_backdoor}", prereq=[],
         hints=["レジスタは16ビット＝2文字分です。数値ではなく文字が埋まっていることがある。read-hr 0 100 を読み、Wireshark のバイト列で文字として見てください。",
                "70番台のレジスタに、操作の指示が文字で書かれています。",
                "手がかりは『WRITE 4919 TO REG51』です。",
                "答え: write-hr 51 4919 を実行すると、フラグが200番台に現れます（read-hr 200 20 → Wireshark で確認）。"]),
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
        print("すでにセットアップ済みのようです。作り直すには ctfd-data を消して再起動してください。")
        sys.exit(1)
    status, body, url = post_form(base + "/setup", {
        "ctf_name": "OT-CTF", "ctf_description": "Modbus ハンズオン",
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
        print("CSRF nonce を取得できませんでした。セットアップに失敗した可能性があります。"); sys.exit(1)
    print("[auth] csrfNonce 取得 OK")

    # 3) 問題・フラグ・ヒントを登録
    ids = {}
    for ch in CHALLENGES:
        st, res = api(base, csrf, "POST", "/api/v1/challenges", {
            "name": ch["name"], "category": ch["category"], "description": ch["desc"],
            "value": ch["value"], "state": "visible", "type": "standard"})
        if not res.get("success"):
            print(f"[NG] challenge {ch['key']}: {res}"); continue
        cid = res["data"]["id"]; ids[ch["key"]] = cid
        stf, rf = api(base, csrf, "POST", "/api/v1/flags",
                      {"challenge_id": cid, "content": ch["flag"], "type": "static", "data": ""})
        prev = None
        for h in ch["hints"]:
            payload = {"challenge_id": cid, "content": h, "cost": 0}
            if prev is not None:
                payload["requirements"] = {"prerequisites": [prev]}
            sth, rh = api(base, csrf, "POST", "/api/v1/hints", payload)
            prev = rh.get("data", {}).get("id") if rh.get("success") else prev
        print(f"[OK] {ch['key']} id={cid} flag={'OK' if rf.get('success') else rf} "
              f"hints={len(ch['hints'])}")

    # 4) 問題間のロックは使わない（全問を最初から表示）。順序は番号と司会進行で担保。
    #    段階的にロックしたい場合は、ここで PATCH requirements.prerequisites を設定する。
    print("[done] 登録完了（全問表示・問題間ロックなし）。ブラウザで", base, "を開いて確認してください。")

if __name__ == "__main__":
    main()

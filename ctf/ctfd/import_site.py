#!/usr/bin/env python3
"""CTFd に参加者向け「はじめに」ページと mbclient.py のダウンロードを登録する.

これで参加者はブラウザ（CTFd）だけで、ツールの入手・使い方・接続先・ルールが揃う。
ファイルの個別配布が不要になる。標準ライブラリのみ。

前提: CTFd が起動し、初期セットアップ済み（import_challenges.py を実行済み）であること。
  python3 import_site.py [--url http://localhost:8000] [--admin admin] [--password otctf-admin]
"""
from __future__ import annotations
import argparse, json, os, re, sys, urllib.request, urllib.parse, http.cookiejar

HERE = os.path.dirname(os.path.abspath(__file__))
MBCLIENT = os.path.normpath(os.path.join(HERE, "..", "toolkit", "mbclient.py"))

cj = http.cookiejar.CookieJar()
OP = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def get(url):
    with OP.open(url) as r: return r.read().decode("utf-8","replace")

def login(base, name, pw):
    html = get(base + "/login")
    nonce = re.search(r'name="nonce"[^>]*value="([0-9a-f]+)"', html).group(1)
    OP.open(urllib.request.Request(base + "/login",
        data=urllib.parse.urlencode({"name":name,"password":pw,"nonce":nonce,"_submit":"Submit"}).encode()))
    h = get(base + "/challenges")
    return re.search(r'csrfNonce["\']?\s*[:=]\s*["\']([0-9a-f]+)', h).group(1)

def api(base, csrf, method, path, payload):
    req = urllib.request.Request(base + path, data=json.dumps(payload).encode(), method=method,
        headers={"Content-Type":"application/json","CSRF-Token":csrf})
    try:
        with OP.open(req) as r: return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")

def upload_file(base, csrf, path, page_id):
    # このCTFdの file type は page / challenge のみ（standalone は無効で配信が500になる）。
    # ページ添付として type=page ＋ page=<id> で上げる。multipart は nonce をフォームにも必要。
    fn = os.path.basename(path)
    with open(path, "rb") as f: content = f.read()
    boundary = "----otctfboundary1234"
    def part(name, value):
        return (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n').encode()
    body  = part("nonce", csrf) + part("type", "page") + part("page", str(page_id))
    body += (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{fn}"\r\n'
             f'Content-Type: text/x-python\r\n\r\n').encode() + content + b"\r\n"
    body += f'--{boundary}--\r\n'.encode()
    req = urllib.request.Request(base + "/api/v1/files", data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "CSRF-Token": csrf})
    with OP.open(req) as r:
        res = json.loads(r.read().decode())
    return res["data"][0]["location"]

def build_content(dl_url, code):
    return f"""# OT-CTF へようこそ

この演習の対象は、**貯液タンクの水位を自動で制御する制御装置（PLC）**です。
産業用プロトコル **Modbus/TCP** で通信します。**設計図（どの番号が何か）は教えません。**
自分で読み書きして突き止め、最後はタンクをあふれさせるのが目標です。

- 制御装置の接続先: **`<司会が伝えるIP>:5020`**
- 問題とフラグ提出: この CTFd（上のメニューの Challenges）

## 配布ツール: mbclient.py

依存なし（Python 標準ライブラリのみ）の薄い Modbus/TCP クライアントです。
番号を指定して制御装置のレジスタ・コイルを読み書きします。**メモリマップは入っていません。**

**▶ [mbclient.py をダウンロード]({dl_url})**（右クリックで保存、または開いて保存）

### 使い方
```
python3 mbclient.py --host <IP> read-hr 0 30     # 保持レジスタ 0〜29 を読む
python3 mbclient.py --host <IP> read-co 0 16     # コイル 0〜15 を読む
python3 mbclient.py --host <IP> write-co 5 1     # コイル5 を ON(1)/OFF(0)
python3 mbclient.py --host <IP> write-hr 11 65535 # 保持レジスタ11 に値を書く
python3 mbclient.py --host <IP> ascii 0 100      # レジスタ範囲を文字列化
python3 mbclient.py --host <IP> watch 10 1       # 値の変化を監視
```

| コマンド | 意味 |
|---|---|
| `read-hr <番号> <個数>` | 保持レジスタを読む（16bit 数値） |
| `read-co <番号> <個数>` | コイルを読む（ON/OFF） |
| `write-co <番号> <0/1>` | コイルを書く（ポンプ・安全装置） |
| `write-hr <番号> <値>` | レジスタを書く（設定値の改ざん） |
| `ascii <番号> <個数>` | レジスタを文字列化（隠しメッセージ探し） |
| `watch <番号> <個数>` | 変化を 0.5 秒ごとに監視 |

## Wireshark で平文を見る
1. Wireshark を起動し、自分のネットワーク（手元だけなら loopback）をキャプチャ。
2. 表示フィルタに **`modbus`**。
3. `mbclient.py` で読み書きすると、やり取りが**平文**で見えます（認証が無いことを確認）。

## ルール
- **本編（レジスタの意味を推定してあふれさせる部分）は AI 禁止**。自分で読み解くのが目的です。
  Wireshark や Modbus 全般の調べ物に AI を使うのは構いません。
- 詰まったら遠慮なく**司会にヒント**を求めてください。
- **隔離ネットワーク専用**。渡された制御装置以外には接続しないこと。

---
<details><summary>ダウンロードが使えないとき: mbclient.py の中身（コピーして保存）</summary>

```python
{code}
```
</details>
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--admin", default="admin")
    ap.add_argument("--password", default="otctf-admin")
    ap.add_argument("--route", default="start")
    a = ap.parse_args()
    base = a.url.rstrip("/")
    csrf = login(base, a.admin, a.password)
    print("[auth] OK")
    # 1) 先にページを作る（ファイルを type=page で紐づけるため id が要る）
    st, res = api(base, csrf, "POST", "/api/v1/pages",
        {"title":"はじめに","route":a.route,"content":"(準備中)",
         "draft":False,"hidden":False,"auth_required":False,"format":"markdown"})
    if not res.get("success"):
        print(f"[page] 作成失敗（route 重複なら作り直してください）: {res}"); sys.exit(1)
    pid = res["data"]["id"]; print(f"[page] 作成 id={pid}")
    # 2) mbclient.py をそのページの添付として上げる
    loc = upload_file(base, csrf, MBCLIENT, pid)
    dl = f"/files/{loc}"; print(f"[file] mbclient.py → {dl}")
    # 3) 本文を流し込む（ダウンロードリンク＋説明＋コピー用コード）
    code = open(MBCLIENT, encoding="utf-8").read()
    st, res = api(base, csrf, "PATCH", f"/api/v1/pages/{pid}", {"content": build_content(dl, code)})
    print(f"[page] 本文設定 {'OK' if res.get('success') else res} → {base}/{a.route}")

if __name__ == "__main__":
    main()

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

def api(base, csrf, method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(base + path, data=data, method=method,
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

## 接続先（まずここを確認）

- 制御装置: **`<司会が伝えるIP>:<司会が伝えるポート>`**
  - **ポートは参加者ごとに違います**（5020, 5021, 5022 … のどれか）。司会が「あなたは◯◯番」と伝えます。
  - コマンドには **必ず `--port <自分の番号>` を付けます**。
- 問題とフラグ提出: この CTFd（上のメニューの **Challenges**）

## レジスタとコイル（2種類のデータ）

制御装置の中身は、**番号のついた2種類の入れ物**でできています。読み書きはどちらも番号で指定します。

- **保持レジスタ (holding register)**: **16ビットの数値**を1つ入れる箱（0〜65535）。
  水位・設定値・流量などの「数値」はここ。**文字が埋め込まれていることもあります**。→ `read-hr` / `write-hr`
- **コイル (coil)**: **ON/OFF の1ビット**のスイッチ。ポンプの起動、安全装置の有効/無効などの「入／切」はここ。→ `read-co` / `write-co`

攻撃に成功すると、制御装置が**保持レジスタの高い番号（100番台など）に文字列（フラグ）を書き込みます**。
「レジスタに数値や文字が現れる」のを読み取って探す、という感覚です。

## フラグの形式と提出

- フラグは **`FLAG{{...}}`** の形です。装置内で見つけた文字列を、そのまま各問題の入力欄に貼って提出します。
- **1問目（偵察）だけは例外**です。装置の中に文字列はありません。答えは「水位レジスタの**番号**」で、
  それを自分で **`FLAG{{番号}}`** の形にして提出します（例: 番号が 7 なら `FLAG{{7}}`）。

## 配布ツール: mbclient.py

依存なし（Python 標準ライブラリのみ）の薄い Modbus/TCP クライアントです。
番号を指定して制御装置のレジスタ・コイルを読み書きします。**メモリマップは入っていません。**

**▶ [mbclient.py をダウンロード]({dl_url})**（右クリックで保存、または開いて保存）
ダウンロードフォルダに入ったら、そのフォルダへ `cd` してから実行します（インストール不要）。

### 使い方

- **番号は 0 から始まります**（0, 1, 2 …）。例えば `read-hr 0 30` は **0〜29番**の30個を読みます。
- **引数の順番**（重要）:
  - `read-hr / read-co` … **1個目＝開始番号、2個目＝読む個数**
  - `write-hr` … **1個目＝レジスタ番号、2個目＝書き込む値**
  - `write-co` … **1個目＝コイル番号、2個目＝1(ON)/0(OFF)**

```
# <IP> と <ポート> は司会が伝えた値に置き換える
python3 mbclient.py --host <IP> --port <ポート> read-hr 0 30    # 0〜29番を読む
python3 mbclient.py --host <IP> --port <ポート> read-hr 100 20  # 100番から20個（開始が0以外の例）
python3 mbclient.py --host <IP> --port <ポート> read-co 0 16    # コイル 0〜15番
python3 mbclient.py --host <IP> --port <ポート> write-co 5 1    # コイル5番 を ON(1)/OFF(0)
python3 mbclient.py --host <IP> --port <ポート> write-hr 11 65535 # レジスタ11番 に 65535
```
（`--port` は全員付けます。Windows ネイティブ実行では `python3` が `python` のことがあります。）

値の変化（水位など）は `read-hr` を**何度も実行**して観察します。

| コマンド | 意味 |
|---|---|
| `read-hr <開始番号> <個数>` | 保持レジスタを読む（16bit 数値） |
| `read-co <開始番号> <個数>` | コイルを読む（ON/OFF） |
| `write-co <番号> <0/1>` | コイルを書く（ポンプ・安全装置） |
| `write-hr <番号> <値>` | レジスタを書く（設定値の改ざん） |

## まず全体を眺める（探り方）

どの番号が何かは教えません。次の手順で自分で突き止めます。

- **コイル**（ON/OFFのスイッチ。1本=1ビット）は数が少ない → `read-co 0 16` で全体を見る。
- **保持レジスタ**（16ビットの数値）は多い → まず `read-hr 0 50` でシステム部あたりを眺める。
- コツ1: **何度も読んで変化する値**を探す（＝動いているプロセス量）。止まって見える値は設定値や別物。
- コツ2: **コイルを1つずつ書き換えて**、水位の動きがどう変わるか観察する（どれがポンプ/安全かが分かる）。
- 攻撃に成功すると、**もっと高い番号**（100番台など）に文字列が現れます。そこを読むとフラグです。

## Wireshark で平文を見る
1. Wireshark を起動し、**通信が流れているインタフェースを選ぶ**:
   - 会場では **自分の Wi-Fi**（有線なら Ethernet）＝ `192.168.x.x` のIPを持つアダプタ。
   - 迷ったら、各アダプタ名の右の**波形が動く**方（`read-hr` 実行時にピクッと動く）を選ぶ。
   - WSL の人は Windows 版 Wireshark で**物理 Wi-Fi/Ethernet**（無ければ `vEthernet (WSL)`）。
   - （Mac1台で全部動かす検証時のみ loopback / lo0）
2. 表示フィルタに **`tcp.port == <自分のポート>`**（例: `tcp.port == 5020`）。
   ポートが標準(502)でないので、右クリック→Decode As→MODBUS で解釈も可（バイト列ペインだけでも中身は読めます）。
3. `mbclient.py` で読み書きすると、やり取りが**平文**で見えます（認証が無いことを確認）。
4. `read-hr 0 100` で広い範囲を読む通信を起こし、表示フィルタに **`frame contains "FLAG"`** と入れると、
   隠し文字列入りのパケットだけに絞れます。クリックして右下のバイト列(ASCII)から読み取れます。

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
    if res.get("success"):
        pid = res["data"]["id"]; print(f"[page] 作成 id={pid}")
    else:
        # route 重複 → 既存ページを探して更新（再実行で本文を差し替えられる）
        _, pages = api(base, csrf, "GET", "/api/v1/pages")
        pid = next((p["id"] for p in pages.get("data", []) if p.get("route") == a.route), None)
        if pid is None:
            print(f"[page] 作成失敗かつ既存も見つからず: {res}"); sys.exit(1)
        print(f"[page] 既存を更新 id={pid}")
    # 2) mbclient.py をそのページの添付として上げる
    loc = upload_file(base, csrf, MBCLIENT, pid)
    dl = f"/files/{loc}"; print(f"[file] mbclient.py → {dl}")
    # 3) 本文を流し込む（ダウンロードリンク＋説明＋コピー用コード）
    code = open(MBCLIENT, encoding="utf-8").read()
    st, res = api(base, csrf, "PATCH", f"/api/v1/pages/{pid}", {"content": build_content(dl, code)})
    print(f"[page] 本文設定 {'OK' if res.get('success') else res} → {base}/{a.route}")

if __name__ == "__main__":
    main()

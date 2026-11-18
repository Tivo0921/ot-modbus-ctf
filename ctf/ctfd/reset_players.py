#!/usr/bin/env python3
"""CTFd の参加者アカウントと得点だけを消す（管理者・問題・はじめにページは残す）。

デモ→本番の間に実行する想定。標準ライブラリのみ。安全のため --yes 必須。

  python3 reset_players.py          # 確認のみ（何も消えない）
  python3 reset_players.py --yes    # 実行

【重要】CTFd 標準の「accounts」一括リセット(/admin/reset)は *管理者アカウントごと*
削除し、初期セットアップ画面に戻してしまう。だからここでは使わない。この版は
参加者ユーザーを 1 人ずつ API で削除する（その人の提出/得点も一緒に消える）。
管理者(type=admin)は必ず残す。
"""
from __future__ import annotations
import argparse, re, sys, json, urllib.request, urllib.parse, http.cookiejar, urllib.error

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--admin", default="admin")
    ap.add_argument("--password", default="otctf-admin")
    ap.add_argument("--yes", action="store_true", help="付けると実際に削除する")
    a = ap.parse_args()
    base = a.url.rstrip("/")

    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    g = lambda u: op.open(u).read().decode("utf-8", "replace")

    html = g(base + "/login")
    nonce = re.search(r'name="nonce"[^>]*value="([0-9a-f]+)"', html).group(1)
    op.open(urllib.request.Request(base + "/login", data=urllib.parse.urlencode(
        {"name": a.admin, "password": a.password, "nonce": nonce, "_submit": "Submit"}).encode()))
    csrf = re.search(r'csrfNonce["\']?\s*[:=]\s*["\']([0-9a-f]+)', g(base + "/challenges")).group(1)

    def users():
        return json.loads(g(base + "/api/v1/users?per_page=100")).get("data", [])

    # CTFd 仕様で /api/v1/users は管理者を一覧に返さない。よって players に管理者は入らず、
    # 削除対象になり得ない（管理者は必ず残る）。type チェックは二重の安全策。
    players = [u for u in users() if u.get("type") != "admin"]
    print(f"参加者（消す対象）: {[(u['id'], u['name']) for u in players] or '（なし）'}")
    print("※ 管理者アカウントはこの一覧に出ません（CTFd仕様）。削除対象にならず、必ず残ります。")

    if not a.yes:
        print("\n[確認のみ] 実際に消すには  python3 reset_players.py --yes")
        print("消えるもの: 参加者アカウント＋その得点。 残るもの: 管理者・問題・はじめにページ。")
        return

    for u in players:
        req = urllib.request.Request(f"{base}/api/v1/users/{u['id']}", method="DELETE",
            headers={"CSRF-Token": csrf, "Content-Type": "application/json"})
        try:
            with op.open(req) as r:
                print(f"  削除 id={u['id']} {u['name']} -> {r.status}")
        except urllib.error.HTTPError as e:
            print(f"  削除失敗 id={u['id']} {u['name']} -> HTTP {e.code}")

    rest = [u for u in users() if u.get("type") != "admin"]
    print("実行後の参加者:", [(u['id'], u['name']) for u in rest] or "（なし＝クリア完了）")
    print("管理者・問題・はじめにページは残っています。本番は参加者が再登録してください。")

if __name__ == "__main__":
    main()

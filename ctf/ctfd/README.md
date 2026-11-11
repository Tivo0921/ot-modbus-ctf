# CTFd セットアップ（Mac = アリーナホスト）

4人・協力・競争なしの「謎解き公演」用。CTFd はチャレンジ提示・フラグ提出・ヒント開放を担当する。
制御装置（タンク）本体は `../target.py`。

## 当日の構成

```
                 隔離LAN / ホットスポット
 参加者PC ×4 ──┬── http://<MacのIP>:8000   （CTFd: 問題・フラグ提出）
  Wireshark   └── <MacのIP>:5020 Modbus/TCP （制御装置 target.py: 攻撃対象の実体）
  mbclient.py
                 ↑ どちらも Mac で動かす
```

## 1. 制御装置サーバを起動（別ターミナル）

```bash
cd ot-demo-3d
# 中央配信: 全インターフェースで待受（隔離LAN前提）
python3 ctf/target.py --host 0.0.0.0 --port 5020
```

### 1人1環境にする場合（参加者が多いとき）
ポートを分けて複数の独立環境を一括起動できる。各環境は互いに干渉しない。

```bash
python3 ctf/run_arena.py --count 8          # 5020〜5027 で8環境。割り当て表を表示
# Ctrl+C で全環境を停止
```

- フラグ文字列は全環境で共通なので、**CTFd は無改修**（どのポートで解いても同じフラグを提出）。
  その分、フラグを人に教えると解かずに提出できてしまう点だけ注意（協力前提なら問題なし）。
- macOS ファイアウォールは、個別ポートではなく `python3` の受信を許可すれば全ポートに効く
  （または演習中だけ一時オフ）。

## 2. CTFd を起動

```bash
cd ot-demo-3d/ctf/ctfd
docker compose up -d          # 初回はイメージ取得済みなら即起動
# → http://localhost:8000 を開き初期セットアップ（管理者作成）
docker compose logs -f ctfd   # 様子を見るとき
docker compose down           # 片付け（データは ./ctfd-data に残る）
```

初期セットアップ画面で「大会名」「管理者アカウント」を作る。終わったら管理画面へ。

## 3. チャレンジ登録（自動／手動）

**自動（推奨）**: 初期セットアップ〜問題・フラグ・チェーンヒント登録まで一括。
CTFd を `up -d` した直後（**まだ /setup していない状態**）に:

```bash
python3 import_challenges.py          # --url http://localhost:8000 が既定
# 管理者 admin / otctf-admin、全7問（6本編＋ボーナス）を全表示・ロックなしで登録
python3 import_site.py                # 「はじめに」ページ＋mbclient.pyダウンロードを登録
# → 参加者はブラウザ(CTFd)だけで、ツール入手・使い方・接続先・ルールが揃う（ファイル配布不要）
```

作り直すとき: `docker compose down && rm -rf ctfd-data && docker compose up -d` の後に
`import_challenges.py` → `import_site.py` の順で再実行。

**手動**: `challenges.md` の各問を **Admin > Challenges > + Create** から入力（説明・フラグ・
ヒント4段）。自動登録が使えないときの保険。

> 登録済みの内容は `http://localhost:8000` を開けば参加者視点で確認できる。
> ヒントは段内チェーン（H1開くとH2…）、問題間の前提ロックは無し（番号＋司会で順序担保）。

## 4. 協力・公演モードの設定

- **Admin > Config > Visibility > Scoreboard: Hidden**（順位を消す）。
- ヒントは全部 **コスト0**。
- Prerequisites で 1→…→6 をゆるく線形に（6 は 4・5 を前提）。
- アカウントは **全員で1つ共有**でよい（競争しないため）。

## 5. 参加者への配布

- `../toolkit/`（薄い Modbus クライアント＋Wireshark 手引き。**target.py とマップは渡さない**）。
- 接続先: CTFd=`http://<MacのIP>:8000`、的=`<MacのIP>:5020`。
- `<MacのIP>` は `ipconfig getifaddr en0`（Wi-Fi）か `en1` で確認。

## 事前チェック（前夜〜当日朝）

- [ ] `docker compose up -d` で CTFd が `http://localhost:8000` で開く
- [ ] `python3 ../target.py` が起動し、`python3 ../selftest.py` が PASS
- [ ] 隔離LAN/ホットスポットで参加者PCから Mac の 8000/5020 に到達できる
- [ ] 6問を登録しフラグ提出が通る（自分で一周）

## 注意

- 隔離ネット専用。学内・会場網には接続しない。
- `SECRET_KEY` は `docker-compose.yml` で変更推奨（ローカル・使い捨てなら必須ではない）。
- `ctfd-data/` は git 管理外（`.gitignore`）。

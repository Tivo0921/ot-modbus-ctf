# CTFd セットアップ（Mac = アリーナホスト）

4人・協力・競争なしの「謎解き公演」用。CTFd はチャレンジ提示・フラグ提出・ヒント開放を担当する。
的（タンク）本体は `../target.py`。

## 当日の構成

```
                 隔離LAN / ホットスポット
 参加者PC ×4 ──┬── http://<MacのIP>:8000   （CTFd: 問題・フラグ提出）
  Wireshark   └── <MacのIP>:5020 Modbus/TCP （的 target.py: 攻撃対象の実体）
  mbclient.py
                 ↑ どちらも Mac で動かす
```

## 1. 的を起動（別ターミナル）

```bash
cd ot-demo-3d
# 中央配信: 全インターフェースで待受（隔離LAN前提）
python3 ctf/target.py --host 0.0.0.0 --port 5020
```

## 2. CTFd を起動

```bash
cd ot-demo-3d/ctf/ctfd
docker compose up -d          # 初回はイメージ取得済みなら即起動
# → http://localhost:8000 を開き初期セットアップ（管理者作成）
docker compose logs -f ctfd   # 様子を見るとき
docker compose down           # 片付け（データは ./ctfd-data に残る）
```

初期セットアップ画面で「大会名」「管理者アカウント」を作る。終わったら管理画面へ。

## 3. チャレンジ登録

`challenges.md` の 6 問を管理画面 **Admin > Challenges > + Create** から手入力する
（説明・フラグ・ヒント2段・前提をそのまま）。所要 15 分ほど。

> 速くやるなら ctfcli（`pip install ctfcli`）で challenge.yml を流し込む手もあるが、
> 6問なら手入力が確実。

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

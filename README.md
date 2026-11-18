# OT-CTF — 制御装置をハックしてタンクをあふれさせろ

産業用プロトコル **Modbus/TCP** は通信が平文で、認証もありません。
この CTF は、**それによって OT 機器（工場やインフラの制御装置）に対して何ができてしまうのか**を、
実際に手を動かして学ぶための教材です。**自分の PC 1台だけ**で最後まで遊べます。

対象は**貯液タンクの水位を自動制御する制御装置（PLC）**をソフトウェアで再現したものです。
設計図なしで通信を覗き、装置を乗っ取り、最後はタンクをあふれさせるのが目標です。
（OTセキュリティ研究会 第1回ワークショップで出題した問題を、自宅で遊べるようにしたものです）

## ⚠️ 最初に読むこと

- **`ctf/` 以下のソースコードやその他の資料（`docs/`, `ctf/_facilitator/` など）は見ないでください。答えが全部書いてあります。**
  答えは全部 **Wireshark** で見つけられるようになっています。読むのはこの README だけにしてください。
- 制御装置は**自分の PC の中だけ（`127.0.0.1`）で起動**してください。学内ネットワーク等に公開しないこと。
- 教育目的の演習です。ここで学んだ操作を**実在の機器や他人のネットワークに向けない**でください。

## 必要なもの

- **Python 3**（追加ライブラリ不要。Windows では `python3` の代わりに `python` のことがあります）
- **Wireshark**（Windows はインストール時に **Npcap** も入れ、「loopback を取れるようにする」オプションを有効に）
- ターミナル 2〜3 枚

## 準備（3ステップ）

```bash
# リポジトリを取得
git clone <このリポジトリのURL>
cd ws1-ctf

# 1) ターミナルA: 制御装置を起動（自分の PC 内だけで待ち受け）。起動したら放置
python3 ctf/target.py --host 127.0.0.1 --port 5020

# 2) ターミナルB: 攻撃用ツールのフォルダへ移動し、接続確認
cd ctf/toolkit
python3 mbclient.py --host 127.0.0.1 --port 5020 read-hr 0 30
```

数字が30個並べば準備完了です。

**（任意）3) ターミナルC: タンクを3Dで見る** — 当日の大画面と同じ表示です。溢れる瞬間が見えます。

```bash
python3 wall/wall.py --count 1 --serve-port 8090
# ブラウザで http://localhost:8090 を開く
```

## 道具の使い方

### レジスタとコイル

制御装置の中身は、**番号のついた2種類の入れ物**でできています。

- **保持レジスタ**: **16ビットの数値**を1つ入れる箱（0〜65535）。水位・設定値などの数値。**文字が埋まっていることも**。
- **コイル**: **ON/OFF の1ビット**。ポンプの起動、安全装置の有効/無効など。

### mbclient.py（読み書きツール）

**番号は 0 から**です（`read-hr 0 30` ＝ 0〜29番の30個）。

```bash
python3 mbclient.py --host 127.0.0.1 --port 5020 read-hr 0 30     # 保持レジスタ 0〜29 を読む
python3 mbclient.py --host 127.0.0.1 --port 5020 read-hr 100 20   # 100番から20個読む
python3 mbclient.py --host 127.0.0.1 --port 5020 read-co 0 16     # コイル 0〜15 を読む
python3 mbclient.py --host 127.0.0.1 --port 5020 write-co 3 1     # コイル3 を ON(1) / OFF(0)
python3 mbclient.py --host 127.0.0.1 --port 5020 write-hr 20 500  # レジスタ20 に 500 を書く
```
（上の番号・値は使い方の例で、答えとは関係ありません）

| コマンド | 意味 |
|---|---|
| `read-hr <開始番号> <個数>` | 保持レジスタを読む |
| `read-co <開始番号> <個数>` | コイルを読む |
| `write-hr <番号> <値>` | レジスタに値を書く |
| `write-co <番号> <0/1>` | コイルを ON/OFF する |

### Wireshark（平文の通信を見る）

1. Wireshark を起動し、**loopback** のインタフェースを選ぶ
   （Mac: `Loopback: lo0` / Windows: `Adapter for loopback traffic capture` / Linux: `lo`）。
2. 表示フィルタに **`tcp.port == 5020`** と入れる。
3. `mbclient.py` で読み書きすると、やり取りが**暗号化されずに**そのまま見えます。
4. 表示フィルタを **`frame contains "FLAG"`** にすると、フラグ入りのパケットだけに絞れます。
   クリックして右下のバイト列（ASCII表示）から `FLAG{...}` を読み取ります。

## 探り方のコツ

設計図（どの番号が何か）は教えません。観察して自分で突き止めます。

- **何度も読んで、変化する値**を探す（＝動いているプロセス量）。止まって見える値は設定値など。
- **コイルを1つずつ書き換えて**、水位の動きがどう変わるか観察する。
- 攻撃に成功すると、**もっと高い番号**（100番台など）に文字列（フラグ）が現れます。

## ルール

- 問題は **段位1〜5（本編）＋ボーナス2問**。段位5で**タンクが溢れたら本編クリア**です。
- フラグは `FLAG{...}` の形です。**装置から `FLAG{...}` が出てきたら、その問題はクリア**です（当日は CTFd に提出しましたが、自宅版では提出はありません）。
- 例外は段位1だけで、答えの「番号」を自分で `FLAG{番号}` にします。正解はヒントの最後で確認できます。
- 本編の「どのレジスタ/コイルが何か」の推理には **AI を使わないでください**（AI に任せると約12秒で終わってしまい、学ぶところが無くなります）。Wireshark や Modbus の一般的な調べ物に使うのは OK。
- 詰まったら下の**ヒントを H1 から順に**開いてください。当日も司会がヒントを出しながら進めました。
- 装置の状態をリセットしたいときは、ターミナルA を `Ctrl+C` で止めて起動し直します。

## 問題

### 段位1. 偵察 — プロセスを読む（機密性）
制御装置には複数の保持レジスタがある。**時間とともに変化する1本が水位**。
どの番号が水位かを観測で突き止め、その **レジスタ番号** を `FLAG{番号}` の形で答えよ（例: 3番なら `FLAG{3}`。これは例で、答えではない）。

<details><summary>H1</summary><code>read-hr 0 30</code> を<b>何度も実行</b>して、<b>値が動くもの</b>を探せ。</details>
<details><summary>H2</summary>動く値は複数ある（<b>ダミー</b>が混じる）。その中で <b>0〜1000 の範囲で小刻みに増減</b>する1本が水位。ダミーは大きく乱高下するので見分けられる。</details>
<details><summary>H3</summary>見つけた水位レジスタの<b>番号</b>がそのまま答え。</details>
<details><summary>H4（答え）</summary>水位＝<b>レジスタ10</b>。<code>FLAG{10}</code>。</details>

### 段位2. 盗聴 — 平文を暴く（機密性）
Modbus には暗号化が無い。**Wireshark で自分の通信をキャプチャ**し、やり取りに紛れている **隠し文字列 `FLAG{...}`** を見つけよ。

<details><summary>H1</summary>Wireshark で loopback をキャプチャし、表示フィルタ <code>tcp.port == 5020</code>。</details>
<details><summary>H2</summary><code>read-hr 0 100</code> で広い範囲を読む通信を起こす（隠し文字列は<b>40番台</b>のレジスタ）。</details>
<details><summary>H3</summary>表示フィルタに <code>frame contains "FLAG"</code>。パケットをクリックして右下の ASCII から読む。</details>

### 段位3. ポンプ奪取 — アクチュエータ操作（完全性）
制御を無視して、**給水ポンプを君の意志で ON** にしろ。成功するとフラグが **100番台のレジスタ**に出る（`read-hr 100 20` を Wireshark で見る）。

<details><summary>H1</summary>ポンプは<b>コイル</b>（ON/OFF）。まず <code>read-co 0 16</code> でコイルを読む。</details>
<details><summary>H2</summary>コイルを<b>1つずつ書いて</b>、水位の増え方が変わるものを探せ（給水が始まる＝そのコイルがポンプ）。</details>
<details><summary>H3</summary><code>write-co 5 1</code>（コイル5をON）。</details>
<details><summary>H4（ほぼ答え）</summary>ポンプ＝<b>コイル5</b>。ON にするとフラグが100番台に出る → <code>read-hr 100 20</code> → Wireshark で確認。</details>

### 段位4. 設定改ざん — 止まらないポンプ（完全性）
ポンプが **絶対に止まらない** 状態を作れ。成功でフラグが **120番台** に出る。

<details><summary>H1</summary>ポンプが止まる条件＝「水位が<b>停止しきい値</b>以上」。止まらなくするには、しきい値をどうする？</details>
<details><summary>H2</summary>停止しきい値のレジスタは水位レジスタのすぐ近く。それを、水位が<b>絶対に届かない大きな値</b>にする。</details>
<details><summary>H3</summary><code>write-hr 11 65535</code>（0xFFFF）。</details>
<details><summary>H4（ほぼ答え）</summary><code>write-hr 11 65535</code> → フラグ120番台 → <code>read-hr 120 20</code> → Wireshark で確認。</details>

### 段位5. 安全無効化 — 最後の砦を外す（★本編クリア）
水位が上限に達したらポンプを強制停止する **安全インターロック** を **無効化** せよ。成功でフラグが **140番台** に出る。
段位4（停止水位）と段位5（安全インターロック）の二重の守りが両方外れると、**タンクが溢れる**。

<details><summary>H1</summary>安全機能も<b>コイル</b>。初期状態が <b>ON</b> になっているコイルが怪しい。</details>
<details><summary>H2</summary><code>read-co 0 16</code> で ON のコイルを探し、<b>OFF</b> にする。</details>
<details><summary>H3</summary><code>write-co 6 0</code>（コイル6をOFF）。</details>
<details><summary>H4（ほぼ答え）</summary>安全インターロック＝<b>コイル6</b>。OFF にするとフラグ140番台。溢水する。</details>

### B1. ボーナス — 制御装置を復旧せよ（防御側）
溢れさせた装置を**安全な状態に戻せ**。揃うと **220番台** に復旧フラグが出る。攻撃するだけでなく「元に戻す」のも守りの仕事。

<details><summary>H1</summary>攻撃の逆をやる。安全インターロック（コイル）を ON、停止水位（レジスタ）を正常値、溢水アラーム（コイル）を OFF。</details>
<details><summary>H2</summary>安全を戻すと水位が下がり、アラームを消せる（溢れたままだと消えない）。</details>
<details><summary>H3</summary><code>write-co 6 1</code> / <code>write-hr 11 800</code> / <code>write-co 7 0</code>。</details>
<details><summary>H4</summary>揃うと220番台にフラグ（<code>read-hr 220 20</code>）。</details>

### B2. ボーナス — 保守バックドア
制御装置には運用者用の **隠し保守モード** がある。**レジスタを文字として読む**と、どこかに手がかりが埋まっている。指示どおりに書き込めば保守フラグが **200番台** に出る。

<details><summary>H1</summary>レジスタは16bit＝2文字。<b>数値ではなく文字</b>が埋まっていることがある。<code>read-hr 0 100</code> → Wireshark のバイト列で文字として読む。</details>
<details><summary>H2</summary><b>70番台</b>に指示が埋まっている。</details>
<details><summary>H3</summary>手がかりは「WRITE 4919 TO REG51」。</details>
<details><summary>H4（ほぼ答え）</summary><code>write-hr 51 4919</code> → フラグ200番台 → <code>read-hr 200 20</code> → Wireshark で確認。</details>

## 持ち帰り課題（おまけ）

制御PCのディスク上の設定ファイルを壊してタンクを溢れさせる別の課題です。→ [`ctf/takehome/README.md`](ctf/takehome/README.md)
（この README だけは読んで OK。`station.py` の中身は見ないでください）

## この CTF で学べること

Modbus には3つの構造的な欠陥があります（当日のスライドより）。

- **認証なし**: 相手が誰かを確かめない。到達できれば誰でも書ける。
- **暗号化なし**: 通信は平文。覗けば値も命令も丸見え。
- **改ざん検知なし**: 正しい命令かを検証しない。偽の命令も実行する。

その結果、攻撃者は次のことができます。

| できること | 内容 | 対応する問題 |
|---|---|---|
| 読める（機密性の侵害） | 水位も設定値も丸見え | 段位1・2 |
| 書ける（完全性の侵害） | 設定値の書き換え、安全装置の無効化 → 溢水 | 段位3・4・5 |
| 落とせる（可用性の侵害） | 不正な値や大量接続で動作を乱す | （この CTF では扱わない） |

実際の現場では、ネットワーク分離・認証付きプロトコル・ソフトに依存しない独立した安全装置・復旧手段を重ねる**多層防御**で守ります。

---
主催者向けの資料（CTFd の立て方・当日の運用）は [`docs/organizer.md`](docs/organizer.md) にあります（**ネタバレを含みます**）。

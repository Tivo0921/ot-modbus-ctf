# 参加者キット — OT-CTF

的（制御装置のタンク）は Modbus/TCP で話す。**メモリマップは教えない**。
自分で読み書きして、どのレジスタ/コイルが何かを突き止め、最後はタンクを溢れさせろ。

- 的: `<HOST>:5020`（司会が伝える）
- CTFd（問題とフラグ提出）: `http://<HOST>:8000`

## 1. まず繋ぐ

```bash
python3 mbclient.py --host <HOST> read-hr 0 30     # 保持レジスタ 0..29
python3 mbclient.py --host <HOST> read-co 0 16     # コイル 0..15
```

主なコマンド:

| コマンド | 意味 |
|----------|------|
| `read-hr <addr> <count>` | 保持レジスタを読む（16bit 値） |
| `read-co <addr> <count>` | コイルを読む（ON/OFF） |
| `write-co <addr> <0/1>` | コイルを書く（ポンプや安全機能はここ） |
| `write-hr <addr> <val>` | 保持レジスタを書く（設定値の改ざんはここ） |
| `ascii <addr> <count>` | レジスタ範囲を ASCII 文字列に変換（隠しメッセージ探しに） |
| `watch <addr> <count>` | レジスタの変化を 0.5 秒ごとに監視 |

ライブラリとしても使える:
```python
from mbclient import Modbus, regs_to_ascii
with Modbus("<HOST>", 5020) as c:
    print(c.read_holding(0, 30))
    c.write_coil(5, True)
    c.write_register(11, 65535)
```

## 2. Wireshark で「平文」を見る

Modbus は暗号化されていない。通信を覗けば値も命令も丸見え。

1. Wireshark を起動し、自分のネットワークインタフェース（または loopback）をキャプチャ。
2. 表示フィルタに **`modbus`** と入力。
3. 自分が `mbclient.py` で読み書きすると、パケットが現れる。
   - **Read Holding Registers** の応答に、レジスタの**生の値**が見える。
   - **Write Single Coil / Register** に、書いた**アドレスと値**が平文で見える。
4. 「どこに認証があるか？」を探してみよ（＝無い）。

## 3. 進め方のコツ（マップは自分で作る）

- **何度も読んで、変化する値を探す** → それが現在の水位。周りに設定値が並ぶ。
- **コイルを1つずつ書いて、水位の動きがどう変わるか**観察 → ポンプ／安全機能を特定。
- 攻撃に成功すると、的が**フラグをレジスタに出す**。`ascii` で読んで CTFd に提出。

## 注意

- **隔離ネット専用**。渡された的以外には絶対に向けない。学内・会場網に接続しない。
- これは OT セキュリティ教育のための、閉じた環境での演習。

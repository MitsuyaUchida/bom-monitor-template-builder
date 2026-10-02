# Build Command

`build` は `cab-excel` と `design-excel` を内部 API として再利用し、CAB から完成設計書 Excel までを 1 コマンドで実行する上位コマンドです。

テンプレートはレイアウト・書式・固定帳票構造のソースとして使い、監視設定データそのものは再利用しません。managed monitor region は毎回初期化し、今回 CAB から生成した内部モデルだけで再構築します。

## 正式な入力形式

正式仕様は `--input` です。

```bash
.venv/bin/bom-monitor-builder build \
  --input "import/cab/0307_sqlserver2022_windows.cab"
```

## 実行内容

1. CAB を解析する
2. 中間 Excel を生成する
3. 解析結果と CAB 名から profile を解決する
4. profile から template を解決する。解決順は `--template` → `profile.template.path` → profile 固有 template → generated template
5. テンプレートの managed monitor region を初期化する
6. CAB から生成した内部モデルだけで監視設定表を再構築する
7. output 名を解決する
8. 設計書 Excel を生成する
9. validation を実行する

## オプション

- `--input`: 入力 CAB
- `--output`: 完成設計書の出力先
- `--profile`: 明示 profile。指定時は自動判定を行わない
- `--template`: 明示 template。指定時は profile 既定 template より優先
- `--work-dir`: 中間 Excel の作業ディレクトリ
- `--overwrite`: 自動採番せず、解決済み output を上書き
- `--dry-run`: CAB 解析、profile 判定、template 解決、モデル生成までを行い、完成設計書は書き出さない
- `--keep-intermediate`: 中間 Excel を保持する
- `--validate-only`: build が解決した profile/template と中間 Excel を使い、既存 output だけを再検証する
- `--dump-model`: 既存 `design-excel` と同じマスク済み内部モデル JSON を出力する
- `--verbose`: 判定根拠と validation check を詳細表示する

## 自動判定

自動判定は次の順で情報を使います。

1. CAB 解析で得たグループ名、監視名、監視種別、ObjectName、ValueName
2. CAB ファイル名
3. profile の `detection` セクション

profile 候補が複数同点の場合は失敗します。

```text
Profile detection is ambiguous.
```

一致候補が 0 件の場合も失敗します。

```text
No matching profile was found.
```

どちらの場合も生成済みの中間 Excel パスを表示します。

## output 名の決定

優先順位:

1. CLI `--output`
2. 入力 CAB 名ベース
3. profile `output.default_filename`

通常時の標準出力は `output/<cab_stem>.xlsx` です。

例:

```text
standard.cab
-> output/standard.xlsx

0307_sqlserver2022_windows.cab
-> output/0307_sqlserver2022_windows.xlsx

Arcserve_UDP_9_10.CAB
-> output/Arcserve_UDP_9_10.xlsx
```

ファイル名に含める CAB stem は、最低限次の文字を `_` に置換します。

```text
/\:*?"<>|
```

日本語、英数字、ハイフン、アンダースコア、スペース、括弧は可能な限り保持します。

### 自動採番

通常実行では既存ファイルを暗黙に上書きしません。

```text
output/standard.xlsx
output/standard_001.xlsx
output/standard_002.xlsx
...
```

採番は 3 桁ゼロ埋めです。`--output output/custom.xlsx` のように明示指定した場合も、`--overwrite` なしで既存ファイルがあれば `output/custom_001.xlsx` を選びます。

### `--overwrite`

`--overwrite` を指定した場合だけ、解決済みの base path をそのまま上書きします。

- `build --input ... --overwrite`
  `output/<cab_stem>.xlsx` を上書きします。`_001` 以降は対象にしません。
- `build --input ... --output output/custom.xlsx --overwrite`
  `output/custom.xlsx` を上書きします。

### dry-run

`--dry-run` はファイルを書き出しませんが、実際に採用される予定の出力先を `Planned output:` として表示します。

### validate-only

`--validate-only` では新しい出力先を採番しません。

- `--output` 指定あり: そのファイルを検証します
- `--output` 指定なし: CAB 名ベースで既存ファイルを探し、`standard.xlsx`, `standard_001.xlsx`, `standard_002.xlsx` のような候補のうち最新番号を検証します

## 中間 Excel の扱い

- `--work-dir` 指定時: そのディレクトリに生成する
- `--keep-intermediate` 指定時: 既定で `input/` に保持する
- どちらも未指定時: 一時ディレクトリに生成し、成功時に削除する
- 失敗時は原因確認のため中間 Excel を残す

## validate-only の意味

`build --validate-only` は次を意味します。

1. CAB を再解析する
2. profile/template/output を解決する
3. 中間 Excel から既存 output の期待値を再構成する
4. output workbook を再検証する

既存 output が存在しない場合は失敗します。

## 成功時の表示

成功時は、実際に生成または検証した output を表示します。`--dry-run` 時は `Planned output:`、通常時と `--validate-only` 時は `Output:` を表示します。

# Operation Guide

## 目的

この文書は、運用担当者が BOM 監視設定の CAB 解析、設計書生成、差分確認、回帰試験を実施するための標準手順をまとめたものです。

本プロジェクトの最重要ルールは次のとおりです。

- 新しい監視種別を追加する場合、原則としてコア Python を変更しない
- まず `YAMLプロファイル / テンプレートExcel / 統合テスト` で対応する
- YAML だけで対応できない場合、その要件が他の監視種別でも利用できる汎用要件かを確認する
- 汎用要件の場合のみコアへ追加する
- 特定監視種別だけに必要な処理をコアへ直接ハードコードしない
- 監視種別固有処理が複雑な場合はプラグイン化を検討する

## 前提条件

- OS: Ubuntu 24.04 以降を想定
- Python 仮想環境 `.venv` が作成済み
- `pip install -e .` 済み、または `.venv/bin/bom-monitor-builder` を直接使う
- `openpyxl` がインストール済み
- 作業ディレクトリはリポジトリ直下

## 仮想環境の有効化

```bash
source .venv/bin/activate
```

初回セットアップ:

```bash
./scripts/setup.sh
source .venv/bin/activate
```

## ディレクトリ構成

通常運用で使うディレクトリ:

```text
import/cab/      CAB入力
input/           cab-excel が生成した解析Excel
reference/       人が作成した正解設計書
templates/       design-excel が使う生成用テンプレート
profiles/        YAMLプロファイル
output/          生成Excel、dump-model JSON
tests/           統合テスト、単体テスト
docs/            手順書、仕様書、完了記録
src/             実装本体
```

## CABファイルの配置

CAB は `import/cab/` に配置します。

例:

```text
import/cab/0307_sqlserver2022_windows.cab
```

日本語名でも動作しますが、Linux 上では英数字名を推奨します。

## reference設計書の配置

人が作成した完成形の正解設計書は `reference/` に配置します。

例:

```text
reference/sqlserver2022_windows_design.xlsx
```

## CAB解析方法

```bash
.venv/bin/bom-monitor-builder cab-excel \
  "import/cab/0307_sqlserver2022_windows.cab" \
  --output "input/0307_sqlserver2022_windows.xlsx" \
  --overwrite
```

確認項目:

- Excel が正常に開ける
- シート構成
- グループ数
- 監視件数
- 監視種別
- 詳細シートとの結合キー候補
- interval / warning / critical / enabled / comment

## `design-excel` による変換方法

```bash
.venv/bin/bom-monitor-builder design-excel \
  --input "input/0307_sqlserver2022_windows.xlsx" \
  --profile "profiles/sqlserver2022_windows.yml" \
  --template "templates/sqlserver2022_windows_design.xlsx" \
  --output "output/sqlserver2022_windows_design.xlsx" \
  --overwrite
```

## YAMLプロファイルの指定方法

`--profile` に YAML を指定します。

例:

```bash
--profile "profiles/sqlserver2022_windows.yml"
```

既存の実ファイル検証済みプロファイル:

- `profiles/aws_cost.yml`
- `profiles/arcserve_udp9.yml`
- `profiles/hyperv_apexone.yml`
- `profiles/sqlserver2022_windows.yml`

## テンプレートの指定方法

通常は `reference/` の正解設計書を `templates/` にコピーして使います。

```bash
cp reference/sqlserver2022_windows_design.xlsx templates/sqlserver2022_windows_design.xlsx
```

CLI では `--template` で明示指定できます。

```bash
--template "templates/sqlserver2022_windows_design.xlsx"
```

## output の確認方法

主な生成物:

- `output/<name>.xlsx`
- `output/<name>_model.json`

確認項目:

- 生成ファイルが存在する
- Excel が開ける
- 監視件数が期待値どおり
- 正解設計書との比較結果

## `--dry-run`

書き込みを行わず、解析とマッピングだけ確認します。

```bash
.venv/bin/bom-monitor-builder design-excel \
  --input "input/0307_sqlserver2022_windows.xlsx" \
  --profile "profiles/sqlserver2022_windows.yml" \
  --dry-run
```

用途:

- YAML の見出し定義確認
- monitor_count / group_count 確認
- テンプレートを書き換えずに事前確認

## `--dump-model`

共通内部モデルを JSON 出力します。

```bash
.venv/bin/bom-monitor-builder design-excel \
  --input "input/0307_sqlserver2022_windows.xlsx" \
  --profile "profiles/sqlserver2022_windows.yml" \
  --dump-model "output/sqlserver2022_windows_model.json" \
  --dry-run
```

確認項目:

- `groups / monitors / metadata / extensions`
- 機密情報マスク
- `input_unchanged`
- `template_unchanged`

## `--validate-only`

既に生成済みの設計書を再検証します。

```bash
.venv/bin/bom-monitor-builder design-excel \
  --input "input/0307_sqlserver2022_windows.xlsx" \
  --profile "profiles/sqlserver2022_windows.yml" \
  --template "templates/sqlserver2022_windows_design.xlsx" \
  --output "output/sqlserver2022_windows_design.xlsx" \
  --validate-only
```

最低限確認される項目:

- sheet order
- sheet visibility
- template formatting
- input workbook readable
- mapped values
- secret masking

## pytest

全体テスト:

```bash
.venv/bin/python -m pytest
```

新しい監視種別追加時は、対象統合テストだけで終わらせず、最後に全体 pytest を実行してください。

## reference と output の比較

最終的な目標は `diff_count=0` です。

比較対象:

- シート名
- シート順
- 表示/非表示
- 結合セル
- 行高
- 列幅
- 固定文言
- 監視設定値

簡易比較例:

```bash
.venv/bin/python - <<'PY'
from openpyxl import load_workbook
ref = load_workbook('reference/sqlserver2022_windows_design.xlsx', data_only=False)
out = load_workbook('output/sqlserver2022_windows_design.xlsx', data_only=False)
diffs = []
for sheet in ref.sheetnames:
    rws = ref[sheet]
    ows = out[sheet]
    for row in range(1, max(rws.max_row, ows.max_row) + 1):
        for col in range(1, max(rws.max_column, ows.max_column) + 1):
            if rws.cell(row, col).value != ows.cell(row, col).value:
                diffs.append((sheet, row, col, rws.cell(row, col).value, ows.cell(row, col).value))
print("diff_count", len(diffs))
PY
```

## 入力ファイル不変確認

`design-excel` の戻り値に `input_unchanged` が含まれます。

期待値:

```text
input_unchanged = true
```

## テンプレート不変確認

`design-excel` の戻り値に `template_unchanged` が含まれます。

期待値:

```text
template_unchanged = true
```

## 機密情報マスク確認

注意対象:

- CAB
- 解析 Excel
- reference
- templates
- output
- dump-model JSON
- ログ

対象語の例:

- `password`
- `pswd`
- `user`
- `username`
- `secret`
- `token`
- `access-key`
- `secret-key`
- `client-secret`
- `connection string`

確認ポイント:

- `dump-model` JSON に平文が残っていない
- `Options` などの CLI 形式文字列がマスクされている
- テンプレート固定の平文を許可セルで管理している
- 許可セルに入力由来の機密値を上書きしていない

## エラー発生時の確認方法

確認順序:

1. 入力 CAB が正しいか
2. `cab-excel` の解析 Excel が正常に生成されているか
3. `監視項目一覧` の見出し名が YAML の `aliases` と合っているか
4. `monitor_id` 重複があるのに単一キー前提になっていないか
5. `reference/` と `templates/` の取り違えがないか
6. `--dry-run --dump-model` で monitor_count / group_count が合っているか
7. `--validate-only` の失敗セルを確認する
8. `reference` と `output` を比較し、差分が YAML で直せるか確認する

典型的な原因:

- 見出し別名不足
- `group_id + monitor_id` の複合キー未考慮
- テンプレート行数不足
- `row_rules` の条件順序ミス
- しきい値表現の調整不足

## 新しい監視種別を追加する手順

1. CAB を用意する
2. 人が作成した正解設計書を用意する
3. CAB を `cab-excel` で解析する
4. 解析 Excel を確認する
5. 正解設計書を解析する
6. 新しい YAML プロファイルを作成する
7. `reference` から `templates` へテンプレートを配置する
8. `--dump-model --dry-run` を実行する
9. `design-excel` で実変換する
10. `--validate-only` を実行する
11. `reference` と `output` を比較する
12. `diff_count=0` を目標に YAML を調整する
13. 統合テストを追加する
14. 全体 pytest を実行する
15. AWS / Arcserve / SQL Server / Hyper-V-Apex One の既存回帰を確認する

## 既存監視種別を変更する手順

1. 対象プロファイルとテンプレートを特定する
2. 変更前に `reference` と `output` の現状を保存する
3. まず YAML 調整で対応可能か確認する
4. 必要ならテンプレートを見直す
5. `--dry-run --dump-model`
6. 実変換
7. `--validate-only`
8. 対象統合テスト
9. 全体 pytest
10. AWS / Arcserve / SQL Server / Hyper-V-Apex One の回帰確認

## 回帰試験

最低限の回帰対象:

- `tests/integration/test_design_excel_arcserve_udp9.py`
- `tests/integration/test_design_excel_sqlserver2022_windows.py`
- `tests/integration/test_design_excel_hyperv_apexone.py`
- `tests/integration/test_design_excel_cli.py`
- `tests/integration/test_design_excel_generic_profile.py`
- 全体 `pytest`

実行例:

```bash
.venv/bin/python -m pytest
```

## バックアップ

作業前に次を保持してください。

- 元 CAB
- 人が作成した正解設計書
- 変更前 YAML
- 変更前テンプレート
- 比較対象 output

推奨:

- `reference/` は原本として維持
- 生成作業には `templates/` を使う

## Git で管理すべきファイル

- `src/`
- `profiles/`
- `tests/`
- `docs/`
- `reference/` のうち共有可能な正解設計書
- `templates/` のうち共有可能な生成テンプレート
- サンプル入力や共有可能な解析 Excel

## Git で管理しない方がよい生成物・機密ファイル

- 一時的な `output/` 生成物
- ローカル比較用の差分ファイル
- 機密情報を含む可能性のある CAB
- 機密情報を含む可能性のある reference / templates / input / output
- 個別案件の dump-model JSON
- ログ

運用上、共有してよいかを判断できないファイルは、原則コミットしないでください。

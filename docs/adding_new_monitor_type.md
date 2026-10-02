# Adding a New Monitor Type

この文書は、新しい監視種別を `design-excel` に追加する標準手順をまとめたものです。

初期開発完了時点の最重要ルールは次のとおりです。

- 新しい監視種別を追加する場合、原則としてコア Python を変更しない
- まず `YAMLプロファイル / テンプレートExcel / 統合テスト` で対応する
- YAML だけで対応できない場合、その要件が他の監視種別でも利用できる汎用要件かを確認する
- 汎用要件の場合のみコアへ追加する
- 特定監視種別だけに必要な処理をコアへ直接ハードコードしない
- 監視種別固有処理が複雑な場合はプラグイン化を検討する

## 標準フロー

1. CAB を `import/cab/` に配置する
2. `cab-excel` を単独実行する
3. 解析 Excel を確認する
4. 既存 profile との誤判定・競合理由を確認する
5. 新しい YAML profile を作成する
6. `detection` ルールを作成する
7. `--dump-model --dry-run` を実行する
8. 完成形テンプレートの有無を確認する
9. テンプレートがあれば `mapping/layout/format` を調整する
10. `build` の自動判定を確認する
11. 統合テストを追加する
12. 全体 pytest を実行する
13. AWS / Arcserve / SQL Server / Hyper-V-Apex One / standard.cab の既存回帰を確認する
14. template を持たない profile では `template.generate_if_missing: true` または `output.generated_template.enabled: true` を設定し、generated template の列定義が必要なら `output.generated_template.columns` で上書きする

新しい CAB を既存 profile へ無理に当てはめないでください。未知 CAB は新しい監視種別として登録するのが標準です。

## 事前準備

通常は次の配置を使います。

```text
import/cab/<input>.cab
input/<parsed>.xlsx
profiles/<type>.yml
output/<design>.xlsx
output/<type>_model.json
tests/integration/test_<type>_profile.py
```

## 1. CABを解析する

例:

```bash
.venv/bin/bom-monitor-builder cab-excel \
  "import/cab/sample.cab" \
  --output "input/sample.xlsx" \
  --overwrite
```

確認項目:

- シート構成
- グループ数
- 監視件数
- 監視種別ごとの件数
- 監視名
- 監視 ID 重複の有無
- 詳細シートとの結合キー候補
- interval / warning / critical / enabled / comment

`monitor_id` 重複がある場合は、単一キー前提で進めないでください。`group_id + monitor_id` を基本にします。

NEC ESMPRO23 のように template 未登録の案件では、この段階で少なくとも次を確認します。

- シート構成
- グループ数
- 監視件数
- 監視種別別件数
- グループ名
- 監視名
- 実行オブジェクト
- 値名
- 固有シグナル候補

例:

- グループ名: `NEC ESMPRO/ServerAgent Service Ver2.3 監視`
- 監視名: `Alert Manager Main Service 監視`
- 実行オブジェクト: `AlertManagerMainService`, `ESMCommonService`

## 2. 正解設計書を解析する

少なくとも次を確認します。

- シート名
- シート順
- 表示/非表示
- 結合セル
- 名前付き範囲
- 行高
- 列幅
- フォント
- 塗りつぶし
- 罫線
- 配置
- 表示形式
- 数式
- 印刷設定
- ウィンドウ枠固定
- 入力規則
- 条件付き書式
- `監視設定` の開始行
- 再利用すべきテンプレート行
- 固定文言
- 値が入る列

## 3. テンプレートを配置する

正解設計書を `templates/` にコピーして生成用テンプレートにします。

```bash
cp reference/sample_design.xlsx templates/sample_design.xlsx
```

テンプレート原本は変更しないでください。

テンプレートが存在しない場合は、他製品テンプレートを流用しないでください。その場合の完了条件は次です。

- CAB 解析成功
- profile 追加
- detection 追加
- `build` 自動判定成功
- `design-excel --dry-run --dump-model` 成功

## 4. YAMLプロファイルを作成する

最低限、次を定義します。

- 入力シート候補
- 見出し別名
- 詳細シート候補
- 結合キー
- 既定値
- 値置換
- 条件付き行マッピング
- 出力列マッピング
- 固定セル
- 検証条件
- 機密マスク条件
- テンプレート固定平文の許可セル

まずは `profiles/aws_cost.yml`、`profiles/arcserve_udp9.yml`、`profiles/sqlserver2022_windows.yml`、`profiles/nec_esmpro23.yml` を参考にしてください。

`detection` は一般語ではなく製品固有シグナルを使います。NEC ESMPRO23 では次が有効でした。

- `filename_patterns`: `NEC_ESMPRO23`, `NEC ESMPRO2.3`
- `group_name_patterns`: `NEC ESMPRO/ServerAgent Service Ver2.3`
- `monitor_name_patterns`: `Alert Manager Main Service`, `ESMCommonService`, `ESMNVMeMonitor`

## 5. dry-run と dump-model で確認する

```bash
.venv/bin/bom-monitor-builder design-excel \
  --input "input/sample.xlsx" \
  --profile "profiles/sample.yml" \
  --dump-model "output/sample_model.json" \
  --dry-run
```

確認項目:

- `monitor_count`
- `group_count`
- `groups / monitors / metadata / extensions` の形式
- 機密情報マスク
- `input_unchanged`
- `template_unchanged`

template 未登録 profile では `template_path: null` と `template_unchanged: null` を許容します。

## 6. 実変換する

```bash
.venv/bin/bom-monitor-builder design-excel \
  --input "input/sample.xlsx" \
  --profile "profiles/sample.yml" \
  --template "templates/sample_design.xlsx" \
  --output "output/sample_design.xlsx" \
  --overwrite
```

template 未登録 profile はこの段階で停止してよく、他製品 template を使ってはいけません。

## 7. validate-only を実行する

```bash
.venv/bin/bom-monitor-builder design-excel \
  --input "input/sample.xlsx" \
  --profile "profiles/sample.yml" \
  --template "templates/sample_design.xlsx" \
  --output "output/sample_design.xlsx" \
  --validate-only
```

少なくとも次を確認します。

- sheet order
- sheet visibility
- template formatting
- input workbook readable
- mapped values
- secret masking

## 8. reference と output を比較する

目標は `diff_count=0` です。

比較対象:

- シート名
- シート順
- 表示/非表示
- 結合セル
- 行高
- 列幅
- 固定文言
- 監視設定値
- チェックシート

差分が出た場合の優先順:

1. YAML で直せるか確認する
2. テンプレートの置き方で直せるか確認する
3. 汎用要件かどうかを整理する
4. 汎用要件の場合のみコア変更を検討する

## 9. 統合テストを追加する

ファイル名の例:

```text
tests/integration/test_design_excel_<type>.py
```

最低限:

- CAB解析成功
- 解析 Excel 可読
- group_count
- monitor_count
- 監視種別
- 詳細結合
- `--dump-model --dry-run`
- 機密マスク
- 実変換成功
- `--validate-only`
- reference 比較
- input 不変
- template 不変

template 未登録 profile では次を最低限とします。

- CAB 解析成功
- `group_count`
- `monitor_count`
- monitor type 取得
- `build` 自動判定成功
- `--dump-model --dry-run`
- 機密マスク
- input 不変

## 10. 全体回帰を実行する

```bash
.venv/bin/python -m pytest
```

加えて、必要に応じて実変換も再確認します。

- AWS コスト監視
- Arcserve UDP 9.0
- SQL Server 2022（Windows版）
- Hyper-V / Apex One

## コア変更を検討してよい条件

次を整理できる場合だけ検討してください。

1. YAML では表現できない入力構造
2. YAML では表現できない変換規則
3. 他監視種別でも再利用できる
4. 回帰テストを追加できる
5. 既存監視種別への悪影響がない

該当しない場合はコアへ入れず、将来のプラグイン候補として扱ってください。

## 機密情報の扱い

次には認証情報が含まれる可能性があります。

- CAB
- 解析 Excel
- reference
- templates
- output
- dump-model JSON
- ログ

対象語の例:

- `user`
- `username`
- `password`
- `pass`
- `pswd`
- `secret`
- `token`
- `access-key`
- `secret-key`
- `client-secret`
- `connection string`

テンプレートに意図的に平文が残る場合でも、入力由来の値で上書きしていないことを確認してください。

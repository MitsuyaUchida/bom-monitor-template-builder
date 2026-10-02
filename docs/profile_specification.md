# Profile Specification

`design-excel` は YAML プロファイルを使って、入力解析、値変換、出力位置、検証条件、機密保護条件を定義します。

`build` を使う場合は、同じ YAML に profile 自動判定用の `detection` ルールも定義できます。

初期開発完了時点で、AWS コスト監視、Arcserve UDP 9.0、SQL Server 2022（Windows版）がこの方式で実ファイル変換済みです。

## 必須セクション

```yaml
profile:
detection:
template:
source:
transform:
output:
validation:
security:
```

## 全体例

```yaml
profile:
  id: sqlserver2022_windows
  name: SQL Server 2022 Windows
  version: 1

detection:
  filename_patterns: ["SQL Server 2022", "sqlserver2022"]
  group_name_patterns: ["SQL Server 2022 サービス監視"]
  monitor_name_patterns: ["MSSQLSERVER", "SQLSERVERAGENT"]
  monitor_type_patterns: ["Service", "EventlogWSA", "Perf"]
  priority: 100

template:
  path: templates/sqlserver2022_windows_design.xlsx

source:
  header_search_rows: 10
  sheets:
    groups:
      candidates: ["監視グループ一覧"]
    monitors:
      candidates: ["監視項目一覧"]
    details:
      candidates: ["監視項目詳細"]
      required: false
  fields:
    group_id:
      sections: ["groups"]
      aliases: ["グループフォルダー", "グループID"]
    group_name:
      sections: ["groups", "monitors"]
      aliases: ["グループ名"]
    monitor_id:
      sections: ["monitors"]
      aliases: ["監視ファイル", "監視ID"]
  keys:
    monitor: ["group_id", "monitor_id"]

transform:
  replacements: {}
  defaults: {}
  derived_fields: {}
  row_rules: []
  normalizers:
    monitor_id: ["strip_extension", "trim"]
  plugins: []

output:
  default_filename: sqlserver2022_windows_design.xlsx
  monitor_table:
    table: monitor_settings
    clear_existing_data: true
    trim_unused_rows: true
    managed_columns:
      group_id: B
      group_name: C
      monitor_id: D
      monitor_name: E
      interval: F
      enabled: G
      average_count: H
      warning_condition: I
      critical_condition: J
      remarks: K
    layout:
      group_merge:
        enabled: false
        columns: [B, C]
      style_sources:
        group_first: 5
        group_middle: 6
        group_last: 9
        single_row_group: 43
        table_last: 43
    format:
      alignment:
        B: {horizontal: center, vertical: top, wrap_text: true}
        C: {horizontal: center, vertical: top}
  tables:
    monitor_settings:
      sheet: "監視設定"
      start_row: 5
      template_row: 5
      clear_existing_rows: false
      reuse_existing_rows: true
      columns:
        B: group_id
        C: group_name
        D: monitor_id
  cells: {}
  preserve:
    workbook_structure: true

validation:
  required_fields: ["group_id", "monitor_id"]
  unique_fields: []
  expected_sheets: ["環境", "監視設定"]

security:
  secret_patterns: ["user", "password", "secret", "token"]
  sanitize_template_strings: false
  allow_plaintext_cells: ["環境!A4"]
  output_policy: mask
```

## `profile`

- `id`: 内部モデル `extensions.<id>` のキーになる識別子
- `name`: 表示用名称
- `version`: プロファイル定義バージョン

## `template`

- `path`: 生成に使うテンプレート Excel
- CLI の `--template` 指定がある場合はそれを優先

テンプレートは通常 `reference/` の正解設計書をコピーして `templates/` に配置します。

テンプレートはレイアウト・書式・固定帳票構造のソースです。監視設定データはテンプレート既存値を再利用せず、CAB から生成した内部モデルだけで毎回再構築します。

template 未登録の profile は `path: null` または未設定相当を許容します。この場合:

- `design-excel --dry-run --dump-model` は実行可能
- `build --dry-run --dump-model` は実行可能
- 実 workbook 生成と `--validate-only` は停止する
- `build` は template が未登録でも、profile 側で generated template を有効化していれば汎用 template を自動生成して継続する

## `detection`

`build` の profile 自動判定で使用します。既存 profile には省略できます。

- `filename_patterns`: CAB ファイル名や stem に対する部分一致
- `group_name_patterns`: 解析済みグループ名への部分一致
- `monitor_name_patterns`: 監視名、ObjectName、ValueName への部分一致
- `monitor_type_patterns`: 監視種別への部分一致
- `priority`: 一致済み候補どうしの優先度

### 判定スコア

- `filename_patterns`: 1 件一致ごとに加点
- `group_name_patterns`: 1 件一致ごとに加点
- `monitor_name_patterns`: 1 件一致ごとに加点
- `monitor_type_patterns`: 1 件一致ごとに加点
- `priority`: 何かが一致した候補に対してだけ加点

一致が 0 件の profile は候補になりません。

`monitor_type_patterns` は一般語だけで高得点になりやすいため、`filename_patterns` / `group_name_patterns` / `monitor_name_patterns` の製品固有語を必ず併用してください。NEC ESMPRO23 追加時は `Service` / `EventlogWSA` だけで `sqlserver2022_windows` と `arcserve_udp9` が同点になりました。

実装上も、`monitor_type_patterns` だけが一致した profile は候補にしません。少なくとも `filename_patterns` / `group_name_patterns` / `monitor_name_patterns` のいずれか 1 件は一致させてください。

### 曖昧判定

最高スコア候補が複数ある場合、`build` は自動選択せず失敗します。

```text
Profile detection is ambiguous.
```

### 明示指定優先

`build --profile ...` を指定した場合、自動判定は行いません。

## `source`

### `header_search_rows`

- 見出し行を探索する最大行数

### `sheets`

- `groups.candidates`: グループ一覧シート候補
- `monitors.candidates`: 監視一覧シート候補
- `details.candidates`: 詳細シート候補
- `details.required`: 詳細シートが必須かどうか

### `fields`

論理項目名ごとに、どのセクションでどの見出しを受け付けるかを定義します。

- `sections`: `groups` または `monitors`
- `aliases`: 見出し別名

主な論理項目:

- `group_id`
- `group_name`
- `enabled`
- `comment`
- `monitor_id`
- `monitor_name`
- `monitor_type`
- `interval`
- `warning_condition`
- `critical_condition`

### `keys`

- 現実装では詳細結合の複合キー設計を補足するために使う位置づけ
- 実運用では `monitor_id` 重複に備えて `group_id + monitor_id` を基本とする

## `transform`

### `defaults`

- 行に既定値を補う
- 例: `average_count: "-"`, `remarks: null`

### `replacements`

- 単純な値置換
- 例: `5 ContYellow -> 連続した 5 回目の注意から`

### `derived_fields`

- `{{ field_name }}` 形式のテンプレート展開
- 例: `remarks: "サービス名：{{ ObjectName }}"`

### `row_rules`

- 条件付き行マッピング
- `when` 条件一致時に `set` を適用
- 監視種別ごとの細かな表示調整、特定行だけの固定値補正、グループ見出し行以外の空欄化に使う

例:

```yaml
row_rules:
  - when:
      group_id: GRP03
      monitor_id: MON20
    set:
      interval: 5分
      warning_condition: 5 /sec 以上
      critical_condition: 10 /sec 以上
```

### `normalizers`

安全な正規化関数を項目ごとに順序指定します。

利用可能:

- `trim`
- `normalize_spaces`
- `strip_extension`
- `normalize_boolean`
- `normalize_interval`
- `normalize_threshold`
- `mask_secret`

### `plugins`

- 将来の許可制プラグイン用
- 初期開発完了時点では未使用

## `output`

- `default_filename`: `build` で `--output` 未指定時に使う既定ファイル名
- `monitor_table`: managed monitor region 定義。writer はここを初期化して、CAB 由来データだけで監視設定表を再構築する

### `monitor_table`

- `table`: 対象 `tables.<name>` の名前。省略時は各 table へ共通適用
- `clear_existing_data`: 既存の監視設定値、コメント、ハイパーリンクを managed region から消す
- `trim_unused_rows`: CAB 件数より後ろに残る managed region の旧値を空欄化する
- `managed_columns`: `論理項目名: 列記号`
- `layout`: 行タイプ判定、group merge、style source 行などの帳票構造ルール
- `format`: alignment、border、row height、column width などの managed region 書式ルール

`monitor_table` が未定義でも、現実装は `tables.<name>.columns` から managed columns を補完して後方互換で動作します。

### `monitor_table.layout`

- `group_merge.enabled`: 同一グループを縦結合するか
- `group_merge.columns`: merge 対象列
- `style_sources`: `group_first` / `group_middle` / `group_last` / `single_row_group` / `table_last` ごとの基準行

writer は各出力行を row context として扱い、行タイプごとに style source 行を選んで style を再適用します。

### `monitor_table.format`

- `alignment.<column>`: `horizontal` / `vertical` / `wrap_text` / `indent`
- `borders.<row_type>`: `left` / `right` / `top` / `bottom`
- `borders.columns.<column>`: 列単位の border 上書き
- `row_height.default`: 基本行高
- `row_height.thresholds`: 折り返し列の文字数しきい値と高さ
- `row_height.fallback`: しきい値超過時の高さ
- `column_widths.<column>`: 列幅の明示上書き

### `tables.<name>`

- `sheet`: 出力シート名
- `start_row`: データ開始行
- `template_row`: 書式複製または基準行
- `clear_existing_rows`: 既存行クリア用途の予約フラグ
- `reuse_existing_rows`: テンプレートに十分な行数がある場合、それをそのまま再利用
- `columns`: `列記号: 論理項目名`

### `cells.<name>`

- 単一セル出力
- 例: タイトル、文書名、固定ラベル

### `preserve`

- `workbook_structure: true` を基本とする

## `validation`

- `required_fields`: 主要必須項目
- `unique_fields`: 一意制約を求める項目
- `expected_sheets`: 期待シート順

`design-excel --validate-only` および `build --validate-only` 実行時は次を検証します。

- sheet order
- sheet visibility
- template formatting
- input workbook readable
- mapped values
- monitor count
- group count
- no stale monitor rows
- no stale template data
- secret masking

## `security`

- `secret_patterns`: マスク対象キーワード
- `sanitize_template_strings`: テンプレート固定文字列まで一括マスクするか
- `allow_plaintext_cells`: テンプレート由来の平文を保持してよいセル
- `output_policy`: 現時点では `mask`

対応している主な秘密形式:

- `-user value`
- `-user=value`
- `--password value`
- `--password=value`
- `-pw:secret`

## 運用ルール

- 新しい監視種別を追加する場合、まず YAML とテンプレートで対応する
- 特定監視種別だけの文字列やセル位置を Python コアへ直接埋め込まない
- YAML で表現できない場合、その要件が他監視種別にも使える汎用要件かを確認する
- 汎用要件の場合のみコアへ追加する
- 監視種別固有処理が複雑な場合は将来のプラグイン化を検討する

具体的な追加手順は [adding_new_monitor_type.md](adding_new_monitor_type.md) を参照してください。

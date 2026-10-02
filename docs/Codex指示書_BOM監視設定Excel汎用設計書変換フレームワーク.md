# Codex 指示書：BOM監視設定Excelから各種監視設計書を生成する汎用変換フレームワーク

## 1. 目的

BOM監視設定の解析ツールが生成したExcelを入力し、監視種別ごとに用意された社内向け設計書テンプレートへ変換する、再利用可能なPythonフレームワークを作成する。

初期実装では、次の変換を正常に実行できることを必須とする。

```text
0104_AWS月コスト監視.xlsx
    ↓
AWSコスト監視設計書.xlsx
```

ただし、実装をAWS月コスト監視専用にはしないこと。将来、SQL Server、Hyper-V、Windowsサービス、イベントログ、Azure、Linux、IISなどの異なる監視設定を追加する際、Python本体を原則変更せず、次の追加だけで対応できる構成にする。

- 変換プロファイルYAMLの追加
- 設計書テンプレートExcelの追加
- 特殊な変換が必要な場合のみ、限定的な変換プラグインの追加

## 2. 開発時の参照ファイル

```text
input/0104_AWS月コスト監視.xlsx
reference/AWSコスト監視設計書.xlsx
```

2ファイルを実際に読み込み、シート構成、セル値、結合セル、書式、非表示状態、列幅、行高、数式、印刷設定を比較した上で実装すること。

## 3. 最重要設計方針

### 3.1 3層に分離する

処理を次の3層へ明確に分離する。

1. **入力解析層**
   - BOM解析Excelを読み取る。
   - シートや列の物理位置に依存しすぎず、見出し名を検索して値を取得する。
   - 取得結果を共通の内部データモデルへ変換する。

2. **変換・マッピング層**
   - YAMLプロファイルに基づき、内部データを設計書用データへ変換する。
   - 表記正規化、固定値、既定値、名称置換、値変換、条件分岐を担当する。

3. **テンプレート出力層**
   - 指定された設計書テンプレートを複製する。
   - YAMLで指定されたセル、表、名前付き範囲などへ値を書き込む。
   - テンプレートの書式や非表示シートを保持する。

入力解析コードとテンプレート出力コードを直接結合しないこと。

### 3.2 セル番地のハードコードを最小化する

入力Excelの読み取りは、原則として次の見出し名を検索して列を特定する。

```text
グループフォルダー
グループ名
監視ファイル
監視名
監視タイプ
有効
監視間隔
注意判定
危険判定
コメント
```

特定のセル番地しか存在しない箇所はYAMLで指定可能にし、Pythonコードへ直接埋め込まないこと。

### 3.3 AWS専用語をコアへ入れない

コアモジュール内では、次のようなAWS専用名称をクラス名や必須項目名として使用しないこと。

```text
AWSCostMonitor
AWSAccessKey
CostExplorer
```

AWS固有処理はプロファイルまたはプラグインへ分離する。

## 4. 推奨ディレクトリ構成

```text
bom-monitor-template-builder/
├── pyproject.toml
├── README.md
├── src/
│   └── bom_design_converter/
│       ├── __init__.py
│       ├── cli.py
│       ├── models.py
│       ├── exceptions.py
│       ├── logging_config.py
│       ├── parser/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── bom_workbook_parser.py
│       │   └── header_finder.py
│       ├── mapping/
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   ├── normalizers.py
│       │   ├── expressions.py
│       │   └── profile_loader.py
│       ├── writer/
│       │   ├── __init__.py
│       │   ├── template_writer.py
│       │   ├── style_copy.py
│       │   └── workbook_validator.py
│       ├── plugins/
│       │   ├── __init__.py
│       │   └── aws_cost.py
│       └── security/
│           ├── __init__.py
│           └── secret_masker.py
├── profiles/
│   └── aws_cost.yml
├── templates/
│   └── AWSコスト監視設計書.xlsx
├── input/
│   └── 0104_AWS月コスト監視.xlsx
├── output/
├── tests/
│   ├── test_parser.py
│   ├── test_mapping_engine.py
│   ├── test_template_writer.py
│   ├── test_security.py
│   └── test_aws_cost_integration.py
└── docs/
    ├── profile_specification.md
    └── adding_new_monitor_type.md
```

既存プロジェクトに同等の構成がある場合は、その規約に合わせて統合してよい。

## 5. 共通内部データモデル

`dataclasses`または`pydantic`を使い、最低限次のモデルを用意する。

```python
WorkbookModel
MonitorGroup
MonitorItem
MonitorDetail
ActionSetting
EnvironmentSetting
```

### 5.1 MonitorGroup

最低限、次の論理項目を持つ。

```text
group_id
group_name
enabled
comment
source_row
```

### 5.2 MonitorItem

最低限、次の論理項目を持つ。

```text
group_id
group_name
monitor_id
monitor_name
monitor_type
enabled
interval
warning_condition
critical_condition
comment
details
source_sheet
source_row
```

### 5.3 生データも保持する

未知の項目を捨てず、次のような辞書として保持する。

```python
raw_values: dict[str, Any]
```

これにより、将来プロファイル側から新しい入力列を参照できるようにする。

## 6. 入力解析仕様

### 6.1 対象シートの検出

AWSサンプルでは、次のシートを利用する。

```text
監視グループ一覧
監視項目一覧
監視項目詳細
```

ただし、シート名はプロファイルで候補を複数指定可能にする。

例：

```yaml
source:
  sheets:
    groups:
      candidates: ["監視グループ一覧", "グループ一覧"]
    monitors:
      candidates: ["監視項目一覧", "監視一覧"]
    details:
      candidates: ["監視項目詳細", "監視詳細"]
      required: false
```

### 6.2 見出し行の検出

- 先頭から指定行数までを検索する。
- 必須見出しの一致数が最も多い行を見出し行と判断する。
- 完全一致を優先し、前後空白、改行、全角半角空白を正規化して比較する。
- 同点または判定不能時は、曖昧なまま処理せず、候補行を含む明確なエラーを出す。

### 6.3 列名の別名対応

YAMLで論理項目ごとに見出し候補を指定する。

```yaml
source:
  fields:
    monitor_id:
      aliases: ["監視ファイル", "監視ID", "MonitorID"]
    monitor_name:
      aliases: ["監視名", "名称"]
```

### 6.4 複数監視項目

- 監視項目が1件でも複数件でも処理できること。
- 複数グループに対応すること。
- 空行、注記行、合計行を誤って監視項目として取得しないこと。
- 一意キーはプロファイルで指定可能にする。

## 7. 変換プロファイルYAML仕様

初期プロファイルとして次を作成する。

```text
profiles/aws_cost.yml
```

YAMLには最低限、次のセクションを持たせる。

```yaml
profile:
  id: aws_cost
  name: AWS月コスト監視
  version: 1

template:
  path: templates/AWSコスト監視設計書.xlsx

source:
  sheets: {}
  fields: {}
  keys: {}

transform:
  replacements: {}
  defaults: {}
  normalizers: {}
  plugins: []

output:
  sheets: {}
  tables: {}
  cells: {}
  preserve: {}

validation:
  required_fields: []
  unique_fields: []
  expected_sheets: []

security:
  secret_patterns: []
  output_policy: mask
```

### 7.1 固定値と既定値

Pythonへ固定値を埋め込まず、次のようにYAMLへ定義する。

```yaml
transform:
  defaults:
    average_count: "-"
    action_id: "act01"
    enabled_true: "有効"
    enabled_false: "無効"
```

### 7.2 値置換

```yaml
transform:
  replacements:
    group_name:
      "旧グループ名": "AWSコスト監視"
```

### 7.3 正規化関数

プロファイルから、登録済みの安全な正規化関数だけを呼び出せるようにする。

例：

```yaml
transform:
  normalizers:
    monitor_id: [strip_extension, trim]
    warning_condition: [normalize_spaces, normalize_threshold]
    critical_condition: [normalize_spaces, normalize_threshold]
```

最低限、次を実装する。

```text
trim
normalize_spaces
strip_extension
normalize_boolean
normalize_interval
normalize_threshold
mask_secret
```

任意PythonコードをYAMLから`eval`する実装は禁止する。

## 8. テンプレート出力仕様

### 8.1 テンプレートを複製して編集する

- テンプレートファイル自体を変更しない。
- 出力先へ複製してから編集する。
- 入力ファイルも変更しない。

### 8.2 維持対象

最低限、次を保持する。

```text
シート順
シート表示・非表示状態
セル結合
フォント
塗りつぶし
罫線
配置
表示形式
数式
行高
列幅
ウィンドウ枠固定
オートフィルター
印刷範囲
印刷方向
改ページ
ページ設定
```

### 8.3 出力位置をYAML化する

AWSサンプルの「監視設定」シートは、4行目以降へ監視項目を出力する。これをPythonへ直書きせず、プロファイルへ定義する。

例：

```yaml
output:
  tables:
    monitor_settings:
      sheet: "監視設定"
      start_row: 4
      template_row: 4
      clear_existing_rows: true
      columns:
        B: group_id
        C: group_name
        D: monitor_id
        E: monitor_name
        F: interval
        G: enabled
        H: average_count
        I: warning_condition
        J: critical_condition
        K: comment
        L: remarks
        M: action_id
        N: action_name
        O: comment_status
        P: target_status
        Q: frequency
        R: action_remarks
```

### 8.4 行追加

- 監視項目数に応じて行を追加する。
- `template_row`の書式、罫線、配置、数式、行高を複製する。
- 結合セルの範囲を壊さない。
- 既存のデータ行を削除またはクリアする方式はYAMLで指定できるようにする。
- 既存のフッター、注記、印刷範囲を必要に応じて下へ移動する。

### 8.5 セル単位の出力

表形式以外の項目もYAMLで設定可能にする。

```yaml
output:
  cells:
    document_title:
      sheet: "監視設定"
      cell: "A1"
      value: "0999_Windows その他：0104_AWSコスト監視"
```

将来的には名前付き範囲も指定可能にする。

## 9. AWS月コスト監視プロファイルの初期変換仕様

初期サンプルでは、次を実現する。

### 9.1 監視グループ

| 論理項目 | 入力候補 |
|---|---|
| `group_id` | `グループフォルダー` |
| `group_name` | `グループ名` |
| `enabled` | `有効` |
| `comment` | `コメント` |

### 9.2 監視項目

| 論理項目 | 入力候補 |
|---|---|
| `group_name` | `グループ名` |
| `monitor_id` | `監視ファイル`の拡張子を除いた値 |
| `monitor_name` | `監視名` |
| `monitor_type` | `監視タイプ` |
| `enabled` | `有効` |
| `interval` | `監視間隔` |
| `warning_condition` | `注意判定` |
| `critical_condition` | `危険判定` |
| `comment` | `コメント` |

### 9.3 詳細情報

`監視項目詳細`が存在する場合は、監視IDなどのキーで結合し、次を`details`または`raw_values`へ格納する。

```text
ObjectName
ValueName
Options
RetryInterval
Timeout
注意比較方法
注意しきい値
危険比較方法
危険しきい値
コメント
```

入力に一覧値と詳細値の両方がある場合、優先順位をYAMLで設定可能にする。

## 10. 機密情報の扱い

### 10.1 出力禁止またはマスク対象

最低限、次の語を含む値を機密候補として扱う。

```text
password
passwd
secret
secret_access_key
access_key
api_key
token
credential
ユーザー名
パスワード
アクセスキー
シークレットキー
```

### 10.2 必須要件

- ソースコードへ認証情報をハードコードしない。
- Git管理対象のプロファイルへ実値を記載しない。
- ログへ実値を出さない。
- 例外メッセージへ実値を出さない。
- 設計書へ転記する場合は既定でプレースホルダーまたはマスク値にする。
- `Options`などの自由形式文字列内に含まれる機密値も可能な範囲で検出・マスクする。

## 11. CLI仕様

コマンド名は既存CLIへ統合するか、次のようなサブコマンドを追加する。

```bash
bom-monitor-builder design-excel \
  --input "input/0104_AWS月コスト監視.xlsx" \
  --profile "profiles/aws_cost.yml" \
  --output "output/AWSコスト監視設計書.xlsx" \
  --overwrite
```

最低限、次のオプションを実装する。

| オプション | 必須 | 内容 |
|---|---:|---|
| `--input` | 必須 | BOM解析Excel |
| `--profile` | 必須 | 変換プロファイルYAML |
| `--output` | 必須 | 出力Excel |
| `--template` | 任意 | YAMLのテンプレートを一時的に上書き |
| `--overwrite` | 任意 | 出力先上書き |
| `--dry-run` | 任意 | 解析・検証のみでExcelを生成しない |
| `--validate-only` | 任意 | 入力、プロファイル、テンプレートの整合性だけ検証 |
| `--verbose` | 任意 | 詳細ログ |
| `--dump-model` | 任意 | 機密値をマスクした内部モデルをJSON出力 |

### 11.1 終了コード

```text
0: 成功
1: 一般エラー
2: 入力ファイル不正
3: プロファイル不正
4: テンプレート不正
5: マッピングエラー
6: 出力検証エラー
```

## 12. エラー処理

次のような曖昧なエラーは禁止する。

```text
KeyError
NoneType has no attribute...
```

利用者が修正できる内容を含めて出力する。

例：

```text
入力シート「監視項目一覧」で必須項目「監視名」が見つかりません。
検出した見出し: グループ名, 監視ファイル, 有効, 監視間隔
プロファイル profiles/aws_cost.yml の source.fields.monitor_name.aliases を確認してください。
```

## 13. 検証機能

生成後に出力ファイルを再度読み込み、最低限次を検証する。

- Excelファイルを正常に再読込できる。
- 期待するシートが存在する。
- シート順がテンプレートと一致する。
- 非表示シートの状態がテンプレートと一致する。
- 必須セルおよび必須表に値が入っている。
- 出力した監視項目数が入力解析結果と一致する。
- 監視IDの重複がない。
- 数式が文字列へ置換されていない。
- 結合セルが破損していない。
- 入力ファイルとテンプレートファイルのハッシュが処理前後で一致する。
- 機密情報がログ、JSON、出力Excelへ意図せず含まれていない。

`--dry-run`時には、次のような要約を表示する。

```text
プロファイル: aws_cost v1
検出グループ数: 1
検出監視項目数: 1
出力対象シート: 監視設定
警告: 0
エラー: 0
```

## 14. テスト要件

`pytest`を使用する。

### 14.1 単体テスト

最低限、次をテストする。

- 見出し行検出
- 列別名の解決
- 空白、改行、全角空白の正規化
- 拡張子除去
- しきい値表記の正規化
- 真偽値の正規化
- 監視詳細の結合
- テンプレート行の書式コピー
- 非表示シート保持
- 機密値マスク
- プロファイル不正時のエラー

### 14.2 結合テスト

実ファイルを用いて次を実行する。

```text
0104_AWS月コスト監視.xlsx
AWSコスト監視設計書.xlsx
```

期待する出力を生成し、主要セル、シート状態、監視件数、書式維持を検証する。

### 14.3 汎用性テスト

AWSとは異なる最小テスト用プロファイルと簡易テンプレートをテスト内で生成し、Pythonコアを変更せずに別形式へ変換できることを確認する。

例：

```text
Windowsサービス監視の仮想入力
    ↓
簡易サービス監視設計書
```

## 15. 新しい監視種別の追加手順

`docs/adding_new_monitor_type.md`を作成し、次を記載する。

1. 元Excelの確認方法
2. テンプレートExcelの配置方法
3. プロファイルYAMLの作成方法
4. 入力見出しの別名定義方法
5. 出力表の列マッピング方法
6. 固定値、既定値、置換ルールの指定方法
7. 標準正規化関数の利用方法
8. プラグインが必要になる条件
9. テスト追加方法
10. 実行コマンド

新しい監視種別を追加する通常手順では、コアPythonを変更しないことを明記する。

## 16. プラグイン方針

標準YAMLだけでは表現できない処理に限りプラグインを使用する。

### 16.1 使用例

- 複数項目を組み合わせた特殊な文章生成
- 独自形式の条件式解析
- 複雑な詳細シートの結合

### 16.2 禁止事項

- 単純な列名変更だけでプラグインを作らない。
- プラグインから任意のファイル削除や外部コマンド実行を行わない。
- YAMLに任意のモジュールパスを書くだけで無制限にimportできる設計にしない。
- 許可済みプラグインIDと実装の対応表をコード側で管理する。

## 17. ログ

- 標準では処理概要のみを出す。
- `--verbose`でシート検出、見出し検出、件数、マッピング結果を出す。
- セルの全内容を無差別にログ出力しない。
- 機密情報は必ずマスクする。
- ログには入力、テンプレート、出力のパスを表示してよいが、認証情報は表示しない。

## 18. 依存関係

原則として次を使用する。

```text
Python 3.12以上
openpyxl
PyYAML
pydantic または dataclasses
pytest
```

既存プロジェクトの対応Pythonバージョンがある場合はそれを優先する。

## 19. 成果物

最低限、次を作成する。

```text
汎用変換フレームワーク本体
CLI
profiles/aws_cost.yml
初期AWSテンプレート配置
単体テスト
結合テスト
README.md
docs/profile_specification.md
docs/adding_new_monitor_type.md
```

加えて、実際に次の出力を生成する。

```text
output/AWSコスト監視設計書.xlsx
```

## 20. 完了条件

以下をすべて満たした時点で完了とする。

1. AWS月コスト監視の実ファイル変換が成功する。
2. 出力Excelが破損せず開ける。
3. テンプレートのレイアウト、書式、非表示シートが維持される。
4. 入力から監視設定値が正しく反映される。
5. 入力ファイルとテンプレートファイルが変更されない。
6. AWS固有ロジックがコアへ密結合していない。
7. 別監視種別をYAMLとテンプレート追加だけで変換できるテストが成功する。
8. 機密情報がコード、ログ、テストデータ、出力へ不用意に露出しない。
9. 全pytestが成功する。
10. READMEの手順だけで第三者が実行できる。

## 21. 実装時の優先順位

1. 実ファイルを使ったAWS月コスト監視変換を完成させる。
2. その実装を入力解析、マッピング、出力へ分離する。
3. AWS固有値をYAMLへ移す。
4. 別形式のテスト用プロファイルを追加して汎用性を証明する。
5. ドキュメントとエラー処理を整備する。

最初から過度に抽象化して実ファイル変換が動かない状態にしないこと。一方で、AWS専用スクリプトを作成してから放置せず、完了条件として必ず汎用構造と別形式テストまで実装すること。

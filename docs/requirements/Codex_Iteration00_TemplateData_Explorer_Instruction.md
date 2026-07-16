# Codex実装指示書 - Iteration 0 : TemplateData Explorer

## 目的

BOM for Windows の **TemplateData**
ディレクトリ全体の構造を把握するための探索機能を実装する。

### 今回は実装しない

-   CAB展開
-   CAB解析
-   HTML解析
-   AutoTemplate.yml の意味解析
-   知識ベース生成
-   監視候補抽出

------------------------------------------------------------------------

# 実装内容

## CLI

新しいCLIグループ `template` を追加する。

``` bash
bom-monitor-builder template scan
```

オプション:

``` bash
--source
```

既定値:

``` text
import/TemplateData
```

------------------------------------------------------------------------

## 取得する情報

TemplateData を再帰的に走査し、以下を取得する。

-   ディレクトリ一覧
-   ファイル一覧
-   拡張子
-   ファイルサイズ
-   更新日時
-   SHA-256
-   日本語ファイル名
-   最大階層
-   カテゴリー数
-   CAB数
-   HTML数
-   YAML数
-   画像数
-   その他ファイル数

------------------------------------------------------------------------

## AutoTemplate.yml

存在する場合は次のみ取得する。

-   サイズ
-   SHA-256
-   更新日時
-   推定文字コード
-   YAMLとして読み込めるか

※内容の意味は解析しない。

------------------------------------------------------------------------

## カテゴリー集計

各カテゴリーについて出力する。

-   category_id
-   category_name
-   directory
-   file_count
-   cab_count
-   html_count

------------------------------------------------------------------------

## テンプレート集計

各カテゴリーについて出力する。

-   テンプレート名候補
-   CAB
-   HTML
-   同名ペア
-   HTMLのみ
-   CABのみ

------------------------------------------------------------------------

# 出力

## JSON

``` text
knowledge/inventory/
├── directory_tree.json
├── files.json
├── categories.json
├── templates.json
├── extensions.json
└── summary.json
```

## CSV

``` text
knowledge/reports/
├── category_inventory.csv
├── template_inventory.csv
└── file_inventory.csv
```

## Excel

``` text
knowledge/reports/template_summary.xlsx
```

シート

-   Summary
-   Categories
-   Templates
-   Files

------------------------------------------------------------------------

# コンソール表示

実行時は次程度を表示する。

``` text
TemplateData Scan
Source
Categories
CAB
HTML
YAML
Images
Other files
Max depth
Completed
```

------------------------------------------------------------------------

# 推奨モジュール構成

``` text
src/bom_monitor_builder/template/
├── scanner.py
├── tree.py
├── category.py
├── inventory.py
├── report.py
└── template_cli.py
```

------------------------------------------------------------------------

# 品質要件

以下を実行し、結果を報告する。

``` bash
pytest
ruff
mypy
```

------------------------------------------------------------------------

# 完了条件

次のコマンドが正常終了すること。

``` bash
bom-monitor-builder template scan
```

以下が生成されること。

-   JSON
-   CSV
-   Excel

------------------------------------------------------------------------

# 完了報告

実装後は以下を報告する。

-   追加したファイル
-   変更したファイル
-   CLI使用方法
-   生成ファイル一覧
-   テスト結果
-   ruff結果
-   mypy結果
-   既知の制限
-   次Iterationへの提案

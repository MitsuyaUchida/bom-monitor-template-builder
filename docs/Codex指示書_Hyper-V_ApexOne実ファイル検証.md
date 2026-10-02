# Codex指示書：Hyper-V_ApexOne.xlsxを使用した汎用変換フレームワーク実ファイル検証

## 1. 目的

既に実装済みの `bom-monitor-builder design-excel` 汎用変換フレームワークについて、AWSコスト監視とは構造が異なる実ファイル `Hyper-V_ApexOne.xlsx` を使用して汎用性を検証する。

この作業では、Hyper-VおよびApex Oneに関する監視設定を、Pythonのコア処理を原則変更せず、追加のYAMLプロファイルとExcelテンプレートだけで変換できることを確認する。

AWSコスト監視の既存変換を壊してはならない。

---

## 2. 使用ファイル

### 2.1 実ファイル

```text
Hyper-V_ApexOne.xlsx
```

プロジェクト内では、まず次のいずれかへ配置されているか確認する。

```text
input/Hyper-V_ApexOne.xlsx
templates/Hyper-V_ApexOne.xlsx
reference/Hyper-V_ApexOne.xlsx
```

ファイルの内容を確認し、次のどちらに該当するか判定する。

1. CAB解析ツール等が出力したBOM監視設定Excel
2. 実際に必要とする完成形の監視設計書Excel

ファイル名だけで役割を決めず、シート構成、見出し、セル内容、非表示シート、監視設定値を確認して判定すること。

### 2.2 対応するもう一方のファイル

`Hyper-V_ApexOne.xlsx` が入力Excelの場合は、完成形テンプレートの候補を `templates/`、`reference/`、`input/` から検索する。

`Hyper-V_ApexOne.xlsx` が完成形テンプレートの場合は、対応するCAB解析結果または監視設定Excelの候補を `input/` から検索する。

候補が複数ある場合は、次の情報を比較して最も対応関係が高いものを選択する。

- グループ名
- 監視名
- 監視ID
- Hyper-V関連の文字列
- Apex One関連の文字列
- サービス名
- イベントログ名
- パフォーマンスカウンター名
- 監視件数

対応するファイルを自動で特定できない場合は、推測で変換せず、候補ファイル一覧と不足情報を作業報告に記載する。ただし、ブック構造の解析、プロファイル案、必要な追加機能の整理までは実施すること。

---

## 3. 既存実装の前提

既存の次の機能を利用する。

```text
bom-monitor-builder design-excel
```

既存の主要構成は次のとおり。

```text
src/bom_monitor_builder/design_excel/
  __init__.py
  cli.py
  exceptions.py
  models.py
  parser.py
  mapper.py
  profile_loader.py
  normalizers.py
  security.py
  writer.py
  validator.py
  service.py
```

既存AWSプロファイルは次のとおり。

```text
profiles/aws_cost.yml
```

既存AWS変換は、必ず回帰テストを通すこと。

---

## 4. 最初に行う解析

`Hyper-V_ApexOne.xlsx` を `openpyxl` で読み込み、少なくとも次の情報を調査する。

### 4.1 ブック全体

- シート名とシート順
- 表示シート、非表示シート、veryHiddenシート
- 使用範囲
- 結合セル
- 行高
- 列幅
- ウィンドウ枠固定
- オートフィルター
- 印刷設定
- 名前付き範囲
- 数式の有無
- 外部リンクの有無

### 4.2 監視設定

- グループ情報
- 監視項目一覧
- 監視ID
- 監視名
- 有効・無効
- 監視間隔
- 注意しきい値
- 危険しきい値
- アクション設定
- 通知設定
- 詳細設定
- XMLファイルパス
- 監視No.

### 4.3 Hyper-V関連項目

次のような項目が存在するか確認する。

- Hyper-V Virtual Machine Health Summary
- Health Critical
- Health Ok
- Hyper-V-VMMS
- Hyper-V-Worker
- VMMSイベントログ
- 仮想マシン名
- パフォーマンスカウンター
- インスタンス名
- サービス名

上記名称を固定前提にせず、実際のファイルに含まれる値を記録する。

### 4.4 Apex One関連項目

次のような項目が存在するか確認する。

- Apex One
- Trend Micro
- ウイルス対策サービス
- Apex One関連サービス名
- Apex One関連イベントログ
- パターンファイル更新
- 検知イベント
- サービス停止
- プロセス監視

上記名称も固定前提にせず、実ファイルの値を記録する。

### 4.5 機密情報

次の情報が含まれる場合は、ログ、JSON、テスト失敗メッセージへ平文出力しない。

- ユーザー名
- パスワード
- APIキー
- シークレット
- UNCパス内の個人名
- 接続先IPアドレス
- メールアドレス
- 認証情報を含むコマンド

---

## 5. 今回追加するプロファイル

解析結果に基づき、次のいずれかまたは両方を追加する。

```text
profiles/hyperv_apexone.yml
```

Hyper-VとApex Oneが明確に別グループまたは別設計書として分離される場合は、次の2つへ分割してよい。

```text
profiles/hyperv.yml
profiles/apexone.yml
```

ただし、分割する場合はその理由を報告すること。

プロファイルには、可能な限り次の内容を外出しする。

- 入力シート名候補
- 見出し名と別名
- データ開始位置
- グループ結合ルール
- 監視項目結合ルール
- 詳細シート結合ルール
- 出力シート名
- 出力セルまたは出力列
- テンプレート行
- 固定値
- 既定値
- 名称置換
- 値正規化
- 監視間隔の変換
- 有効状態の変換
- しきい値の変換
- 機密マスク対象
- 必須項目
- 任意項目
- 検証ルール

Pythonコードに `Hyper-V`、`Apex One`、`Trend Micro` などの監視固有文字列を直接埋め込まないこと。

---

## 6. コアコード変更の原則

次のコアファイルは、原則として変更しない。

```text
parser.py
mapper.py
writer.py
validator.py
service.py
models.py
normalizers.py
security.py
```

YAMLとテンプレートだけでは対応できない場合は、すぐに監視専用処理を追加せず、まず次の分類を行う。

### 6.1 汎用機能として追加可能

複数の監視種別でも利用できる機能であれば、コアへ汎用機能として追加してよい。

例：

- 複数キーによる結合
- 正規表現によるシート選択
- 複数詳細シートの統合
- 条件付き既定値
- 複数行ブロックの複製
- セクション単位のテンプレート複製

### 6.2 監視固有処理

Hyper-VまたはApex Oneだけに必要な処理の場合は、コアへ直書きしない。

プラグインが必要かを整理し、実装前に次を報告する。

- YAMLでは表現できない理由
- 入力例
- 期待出力
- 既存AWS変換への影響
- プラグインの入出力仕様
- 許可リスト方式の安全対策

今回、プラグインが不要であれば実装しない。

---

## 7. 期待する成果物

最低限、次の成果物を作成する。

```text
profiles/hyperv_apexone.yml
```

または

```text
profiles/hyperv.yml
profiles/apexone.yml
```

加えて、対応関係に応じて次を配置する。

```text
templates/Hyper-V_ApexOne監視設計書.xlsx
```

または、元の完成形ファイル名を維持してもよい。

テストは次へ追加する。

```text
tests/integration/test_design_excel_hyperv_apexone.py
```

必要に応じて次の文書も更新する。

```text
docs/adding_new_monitor_type.md
docs/profile_specification.md
README.md
```

出力例：

```text
output/Hyper-V_ApexOne監視設計書.xlsx
output/hyperv_apexone_model.json
```

---

## 8. 実行コマンド

ファイルの役割を確認後、実際のパスに合わせて実行する。

基本形は次のとおり。

```bash
.venv/bin/bom-monitor-builder design-excel \
  --input "input/<対応するBOM監視設定Excel>.xlsx" \
  --profile "profiles/hyperv_apexone.yml" \
  --template "templates/Hyper-V_ApexOne.xlsx" \
  --output "output/Hyper-V_ApexOne監視設計書.xlsx" \
  --overwrite
```

テンプレートパスがプロファイル内に定義されている場合、`--template`は省略してよい。

内部モデルを確認する。

```bash
.venv/bin/bom-monitor-builder design-excel \
  --input "input/<対応するBOM監視設定Excel>.xlsx" \
  --profile "profiles/hyperv_apexone.yml" \
  --dump-model "output/hyperv_apexone_model.json" \
  --dry-run
```

検証専用実行を行う。

```bash
.venv/bin/bom-monitor-builder design-excel \
  --input "input/<対応するBOM監視設定Excel>.xlsx" \
  --profile "profiles/hyperv_apexone.yml" \
  --output "output/Hyper-V_ApexOne監視設計書.xlsx" \
  --validate-only
```

すべてのテストを実行する。

```bash
.venv/bin/python -m pytest
```

---

## 9. 内部モデル要件

`--dump-model`のJSONは、既存形式を維持する。

```json
{
  "groups": [],
  "monitors": [],
  "metadata": {},
  "extensions": {}
}
```

共通項目は `groups` と `monitors` に格納する。

Hyper-V固有情報は次へ格納する。

```json
{
  "extensions": {
    "hyperv": {}
  }
}
```

Apex One固有情報は次へ格納する。

```json
{
  "extensions": {
    "apexone": {}
  }
}
```

Hyper-VとApex Oneが同一監視グループとして不可分の場合は、次でもよい。

```json
{
  "extensions": {
    "hyperv_apexone": {}
  }
}
```

認証情報やマスク対象値はJSONへ平文出力しない。

---

## 10. 自動検証要件

生成後、出力Excelを再度読み込んで検証する。

### 10.1 ファイル整合性

- Excelファイルが破損していない
- すべてのシートを読み込める
- 出力先ファイルが生成されている
- 入力Excelが変更されていない
- テンプレートExcelが変更されていない

### 10.2 シート・書式

- シート順がテンプレートと一致する
- 非表示状態が維持される
- 結合セルが維持される
- フォントが維持される
- 塗りつぶしが維持される
- 罫線が維持される
- 配置が維持される
- 表示形式が維持される
- 行高が維持される
- 列幅が維持される
- 印刷設定が維持される
- ウィンドウ枠固定が維持される

### 10.3 データ

- 入力監視件数と出力監視件数が一致する
- グループ件数が一致する
- 監視IDが正しい
- 監視名が正しい
- 有効状態が正しい
- 監視間隔が正しい
- 注意しきい値が正しい
- 危険しきい値が正しい
- アクション設定が正しい
- 詳細情報が正しい監視項目へ関連付けられる

### 10.4 Hyper-V

実ファイルに存在する場合、少なくとも次を検証する。

- Hyper-V関連監視が欠落していない
- パフォーマンスカウンター名が正しい
- インスタンス名が正しい
- サービス名が正しい
- イベントログ名、ソース、イベントIDが正しい
- 注意・危険条件が正しい

### 10.5 Apex One

実ファイルに存在する場合、少なくとも次を検証する。

- Apex One関連監視が欠落していない
- サービス名またはプロセス名が正しい
- イベントログ条件が正しい
- 更新監視条件が正しい
- 検知イベント条件が正しい
- 通知設定が正しい

### 10.6 セキュリティ

- パスワードを平文出力しない
- シークレットを平文出力しない
- マスク対象をログへ出力しない
- JSONへ機密値を出力しない
- テスト失敗時も機密値を表示しない

---

## 11. 結合テスト要件

`tests/integration/test_design_excel_hyperv_apexone.py`では、可能な限り実ファイルを使用する。

ただし、実ファイルそのものをGitへ登録できない場合は、環境変数またはファイル存在判定により実ファイルテストを分離する。

例：

```text
BOM_REAL_FILE_TESTS=1
```

通常テストでは、実ファイルから抽出した構造を再現する最小限の匿名化フィクスチャをコード内生成してよい。

少なくとも次を確認する。

- AWSプロファイルを変更せず追加できる
- コアコードを変更せず追加できる、または必要な変更が汎用機能のみである
- Hyper-VとApex Oneの複数監視項目を処理できる
- 異なる詳細設定形式を処理できる
- 任意項目欠落時に既定値を適用できる
- 列順変更に耐えられる
- 非表示シートを保持できる
- テンプレート書式を保持できる
- AWSコスト監視の回帰が成功する

---

## 12. 回帰テスト

既存AWS変換を再実行する。

```bash
.venv/bin/bom-monitor-builder design-excel \
  --input "input/0104_AWS月コスト監視.xlsx" \
  --profile "profiles/aws_cost.yml" \
  --output "output/AWSコスト監視設計書.xlsx" \
  --overwrite
```

次も実行する。

```bash
.venv/bin/python -m pytest
```

AWS出力の主要値、シート順、非表示シート、書式保持、入力・テンプレート不変が引き続き成功すること。

---

## 13. 完了条件

次をすべて満たした場合に完了とする。

1. `Hyper-V_ApexOne.xlsx` の役割を内容に基づいて判定した
2. 対応する入力またはテンプレートを特定した
3. 新しいプロファイルを追加した
4. 実ファイル変換が成功した
5. 出力Excelを生成した
6. 内部モデルJSONを生成した
7. 自動検証が成功した
8. Hyper-V関連項目が正しく出力された
9. Apex One関連項目が正しく出力された
10. 機密マスクが成功した
11. 新しい結合テストが成功した
12. 既存AWS回帰テストが成功した
13. 全pytestが成功した

対応ファイル不足により変換できない場合は、1、2、3の設計案、ブック解析結果、不足ファイル、候補ファイル、次に必要な操作を報告すること。

---

## 14. 作業完了時の報告内容

次の形式で報告する。

### 使用ファイル

- `Hyper-V_ApexOne.xlsx` の判定結果
- 入力Excel
- テンプレートExcel
- 出力Excel

### 解析結果

- シート構成
- グループ数
- 監視件数
- Hyper-V監視件数
- Apex One監視件数
- 詳細シート構造

### 実装結果

- 追加・変更ファイル
- 追加プロファイル
- YAMLへ外出しした内容
- コアコード変更の有無
- コア変更がある場合は汎用機能である理由
- プラグインの要否

### 検証結果

- 変換コマンド
- `--validate-only`結果
- `--dump-model`結果
- pytest結果
- AWS回帰結果
- 入力不変
- テンプレート不変
- 機密マスク結果

### 残課題

- YAMLだけでは対応できない項目
- プラグイン候補
- 複雑な結合セル・複数ブロックへの制限
- 追加で必要な実ファイル

---

## 15. 禁止事項

- AWSコスト監視の既存動作を壊さない
- Hyper-VやApex Oneの固定値をコアPythonへ直書きしない
- 入力Excelを上書きしない
- テンプレートExcelを上書きしない
- 実ファイルの機密値をログへ出さない
- 対応ファイルを根拠なく推測しない
- テストをスキップしたまま完成扱いにしない
- `Hyper-V_ApexOne.xlsx` の内容を確認せず、ファイル名だけで設計しない

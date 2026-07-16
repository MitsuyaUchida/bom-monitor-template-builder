# BOMテンプレート知識ベース構築機能 要求仕様書 Ver.1.0

## 1. 文書概要

### 1.1 文書名

BOMテンプレート知識ベース構築機能 要求仕様書

### 1.2 対象プロジェクト

```text
/home/ubuntu/projects/bom-monitor-template-builder
```

### 1.3 目的

BOM for Windowsのインストール環境に存在する `TemplateData` ディレクトリ全体を解析し、BOM標準テンプレートの構成、説明、監視設定および関連情報を検索・比較・参照できる知識ベースへ変換する。

構築した知識ベースは、将来実装する次の機能で利用する。

- Windows環境にインストールされているソフトウェアの検出
- 対象ソフトウェアに関連するWindowsサービスの検出
- 対象ソフトウェアに関連するイベントログ、プロバイダー、イベントIDの検出
- パフォーマンスカウンター候補の検出
- 既存BOMテンプレートを参考にした監視項目候補の提示
- BOM監視テンプレート生成
- 既存テンプレートと生成テンプレートの比較
- BOMの画面上の設定値とCAB内部値との対応関係の調査

本仕様における「学習」とは、AIモデル自体を再学習することではない。

`TemplateData` から抽出した情報を、ローカルのJSON、JSONL、CSV、Excelおよび解析済みファイルとして保存し、後続処理から検索・参照できる状態にすることを指す。

---

## 2. 前提条件

### 2.1 対象OS

```text
Ubuntu Server 24.04 LTS
```

### 2.2 Python

```text
Python 3.12以降
```

### 2.3 BOMテンプレートの入力元

Windows上のBOM for Windowsインストール先に存在する、次のようなディレクトリを入力元とする。

```text
C:\Program Files\SAY Technologies\BOMW8\Common\TemplateData
```

BOMのバージョン、インストール先またはフォルダー名が異なる場合もあるため、Windows上のパスをプログラムに固定しない。

WindowsからUbuntuへコピーした `TemplateData` ディレクトリを入力として使用する。

### 2.4 想定される構成例

```text
TemplateData/
├── 0000_標準構成テンプレート/
├── 0001_レポートテンプレート/
├── 0002_Windows 基本/
├── 0003_Windows オプション/
├── 0004_ハードウェア/
├── 0005_データベースサーバー/
├── 0007_Web サーバー/
├── 0009_バックアップソフト/
├── 0010_ウイルス対策ソフト/
├── 0998_BOMカスタム監視補助/
├── 0999_Windows その他/
├── 1000_Linux 標準構成テンプレート/
├── 1001_Linux 基本/
├── 1002_Linux アプリケーション/
├── 2000_VMware 標準構成テンプレート/
└── AutoTemplate.yml
```

各カテゴリーフォルダーには、次のファイルが含まれる可能性がある。

- CABファイル
- HTMLまたはHTMファイル
- 画像
- CSS
- JavaScript
- XML
- YAML
- テキスト
- その他の付属ファイル

### 2.5 重要な制約

`AutoTemplate.yml` の実際のスキーマは、内容を解析するまでは未確定である。

次のような情報が含まれる可能性はあるが、実物を確認せずに固定仕様として扱わない。

- カテゴリー定義
- テンプレート定義
- CAB参照
- HTML参照
- 表示順
- 対象OS
- 対象製品
- 対応バージョン

未知のキーや構造を保持したまま解析し、既知の形式へ無理に変換しないこと。

---

## 3. 開発方針

### 3.1 基本方針

解析は次の順序で行う。

```text
TemplateData全体の構造把握
        ↓
AutoTemplate.yml解析
        ↓
カテゴリーフォルダー解析
        ↓
HTML解析
        ↓
CAB一覧・展開・内部解析
        ↓
AutoTemplate.yml、カテゴリー、HTML、CABの関連付け
        ↓
監視設定候補の抽出
        ↓
正規化
        ↓
知識ベース・索引・確認レポート生成
```

### 3.2 段階開発

#### Phase 0: 入力構造の棚卸し

- `TemplateData` 全体のファイル一覧を取得する
- フォルダー階層を記録する
- 拡張子別件数を集計する
- 同一ハッシュの重複ファイルを検出する
- `AutoTemplate.yml` の文字コードと構造を確認する

#### Phase 1: メタデータ解析

- カテゴリー名を取得する
- カテゴリー番号を取得する
- CABとHTMLを列挙する
- ファイル名規則を分析する
- `AutoTemplate.yml` のキーと値をそのまま保存する

#### Phase 2: HTML解析

- テンプレート説明を取得する
- 対象製品、対象OS、前提条件、注意事項を抽出する
- HTMLからCABへの参照を取得する
- 表や見出しを構造化する

#### Phase 3: CAB解析

- CABを安全に展開する
- CAB内部のファイル形式を判定する
- テキスト、XML、INI、JSONなどを解析する
- バイナリ形式はハッシュ、サイズ、シグネチャを記録する
- BOM設定候補を抽出する

#### Phase 4: 関連付けと知識ベース生成

- `AutoTemplate.yml` とカテゴリーを関連付ける
- HTMLとCABを関連付ける
- 対象製品と監視項目を関連付ける
- 横断検索用の索引を作成する

#### Phase 5: CAB設定構造の学習支援

- CAB間の差分比較を行う
- 同種テンプレート間の共通要素を抽出する
- BOM画面項目とCAB内部値の対応関係を記録できるようにする
- 未確定項目を人が確認・追記できるようにする

---

## 4. 入力仕様

### 4.1 標準入力ディレクトリ

```text
import/TemplateData
```

ユーザーはWindowsからコピーした `TemplateData` ディレクトリの内容を、元の階層を維持したまま配置する。

推奨配置例:

```text
/home/ubuntu/projects/bom-monitor-template-builder/
└── import/
    └── TemplateData/
        ├── 0000_標準構成テンプレート/
        ├── 0001_レポートテンプレート/
        ├── ...
        └── AutoTemplate.yml
```

### 4.2 任意入力ディレクトリ

CLIオプションで別の入力先を指定できること。

```bash
bom-monitor-builder knowledge import \
  --source /path/to/TemplateData
```

### 4.3 入力検証

取込前に次を確認する。

- 指定パスが存在する
- 指定パスがディレクトリである
- 読み取り可能である
- `AutoTemplate.yml` が存在するか
- CABファイルが存在するか
- HTMLまたはHTMファイルが存在するか
- シンボリックリンクが含まれるか
- フォルダー名およびファイル名が正しく読み取れるか
- 同名ファイルが複数存在するか
- 大文字・小文字の違いだけのファイルが存在するか

`AutoTemplate.yml` が存在しない場合も、フォルダー走査による解析を継続できること。

ただし、警告として記録する。

### 4.4 日本語対応

次を正常に扱うこと。

- 日本語フォルダー名
- 日本語ファイル名
- 日本語HTML
- CP932
- Shift_JIS
- UTF-8
- UTF-8 BOM
- UTF-16 LE
- UTF-16 BE

---

## 5. 出力ディレクトリ

次の構成を作成する。

```text
knowledge/
├── source_inventory/
├── autotemplate/
├── categories/
├── extracted/
├── normalized/
├── mappings/
├── index/
├── reports/
├── state/
└── errors/
```

### 5.1 各ディレクトリの役割

#### `knowledge/source_inventory`

入力元のファイル一覧、ハッシュ値、ファイル種別、サイズ、更新日時を保存する。

#### `knowledge/autotemplate`

`AutoTemplate.yml` の原文情報、解析結果、未知キー一覧および構造レポートを保存する。

#### `knowledge/categories`

カテゴリーフォルダー単位の解析結果を保存する。

#### `knowledge/extracted`

CAB展開結果を保存する。

#### `knowledge/normalized`

テンプレート単位に正規化したJSONを保存する。

#### `knowledge/mappings`

カテゴリー、HTML、CAB、製品、監視項目の関連付け情報を保存する。

#### `knowledge/index`

横断検索用のJSON、JSONLおよび索引を保存する。

#### `knowledge/reports`

人が確認するCSVおよびExcelを保存する。

#### `knowledge/state`

前回取込状態、ハッシュ値および差分取込情報を保存する。

#### `knowledge/errors`

解析できなかったファイルやエラー詳細を保存する。

---

## 6. CLI要求

### 6.1 コマンド体系

既存のCLIへ次を追加する。

```bash
bom-monitor-builder knowledge import
bom-monitor-builder knowledge inspect
bom-monitor-builder knowledge validate
bom-monitor-builder knowledge compare
bom-monitor-builder knowledge report
```

### 6.2 `knowledge inspect`

入力元を変更せず、構造だけを確認する。

```bash
bom-monitor-builder knowledge inspect \
  --source import/TemplateData
```

表示項目:

- 入力パス
- カテゴリー数
- CAB数
- HTML/HTM数
- YAML数
- その他ファイル数
- 総容量
- `AutoTemplate.yml` の有無
- 日本語ファイル名の件数
- 重複ハッシュ件数
- 読み取り不能ファイル件数
- 想定外拡張子
- 警告一覧

### 6.3 `knowledge import`

知識ベースへ取り込む。

```bash
bom-monitor-builder knowledge import \
  --source import/TemplateData \
  --output knowledge
```

### 6.4 dry-run

```bash
bom-monitor-builder knowledge import --dry-run
```

dry-runでは次を行わない。

- CABの展開
- 既存知識ベースの更新
- インデックスの書換え
- Excelレポートの上書き

次を表示する。

- 追加予定
- 更新予定
- 変更なし
- 削除扱い予定
- 解析対象
- スキップ対象
- エラー予測
- 出力予定先

### 6.5 差分取込

標準ではSHA-256を利用した差分取込とする。

状態:

- `added`
- `updated`
- `unchanged`
- `removed`
- `failed`
- `skipped`

### 6.6 全件再解析

```bash
bom-monitor-builder knowledge import --force
```

### 6.7 検証

```bash
bom-monitor-builder knowledge validate
```

検証内容:

- インデックスと実ファイルの整合性
- CAB展開結果の整合性
- HTMLとCABの関連付け
- 重複ID
- 孤立したHTML
- 孤立したCAB
- 存在しない参照先
- JSONスキーマ妥当性
- 解析途中状態

### 6.8 比較

```bash
bom-monitor-builder knowledge compare \
  --left path/to/template_a.cab \
  --right path/to/template_b.cab
```

比較対象:

- CAB内部ファイル一覧
- XML要素
- 属性
- INIキー
- JSONキー
- 文字列
- 数値
- GUID
- しきい値候補
- サービス名候補
- イベントログ候補
- パフォーマンスカウンター候補

---

## 7. TemplateData構造解析

### 7.1 カテゴリー判定

ルート直下のディレクトリをカテゴリー候補として扱う。

カテゴリー名は次に分解して保存する。

例:

```text
0005_データベースサーバー
```

保存項目:

```json
{
  "category_directory": "0005_データベースサーバー",
  "category_code": "0005",
  "category_name": "データベースサーバー",
  "category_type": "directory-derived"
}
```

フォルダー名が番号規則に一致しない場合も除外しない。

その場合:

```json
{
  "category_code": null,
  "category_name": "元のフォルダー名",
  "category_type": "unclassified"
}
```

### 7.2 ファイル名解析

例:

```text
0101_Windows システム監視 Basic.cab
0101_Windows システム監視 Basic.htm
```

抽出候補:

- テンプレート番号
- テンプレート表示名
- 拡張子
- ローカル監視等のバリエーション
- 同一ベース名のCAB/HTMLペア

ただし、ファイル名だけで意味を確定しない。

### 7.3 ケース非依存

次を同じ拡張子として扱う。

```text
.cab
.CAB
.Cab
.htm
.HTM
.html
.HTML
```

元の大文字・小文字は保持する。

---

## 8. AutoTemplate.yml解析

### 8.1 原本保護

元ファイルを変更しない。

SHA-256、サイズ、更新日時、文字コードを記録する。

### 8.2 汎用YAML解析

YAMLを任意の辞書、配列、スカラーとして読み取り、未知キーを破棄しない。

次を出力する。

```text
knowledge/autotemplate/raw_structure.json
knowledge/autotemplate/key_inventory.csv
knowledge/autotemplate/path_value_inventory.csv
knowledge/autotemplate/parse_summary.json
knowledge/autotemplate/unknown_keys.json
```

### 8.3 YAMLパス記録

すべての値を、YAMLパスとともに記録する。

例:

```text
categories[0].name
categories[0].templates[0].cab
categories[0].templates[0].html
```

実際のキー名はファイル内容に従う。

### 8.4 参照候補の検出

文字列値から次を検出する。

- CABファイル名
- HTML/HTMファイル名
- フォルダー名
- カテゴリー番号
- テンプレート番号
- OS名
- 製品名
- バージョン
- 表示順らしい数値
- 有効/無効らしい真偽値

### 8.5 解決結果

YAML内のパスが実ファイルへ解決できるか確認する。

状態:

- `resolved`
- `case-insensitive-resolved`
- `ambiguous`
- `missing`
- `external-reference`
- `not-a-file-reference`

推測で1件へ確定できない場合は `ambiguous` とする。

---

## 9. HTML解析

### 9.1 対象

- `.html`
- `.htm`

### 9.2 抽出情報

- title
- meta description
- meta keywords
- h1
- h2
- h3
- 本文テキスト
- 箇条書き
- 定義リスト
- table
- caption
- 画像alt
- リンク
- CABへのリンク
- 相対パス
- 対象製品名候補
- ベンダー名候補
- 対応バージョン候補
- 対象OS候補
- 前提条件
- 注意事項
- 監視項目説明
- 導入手順
- テンプレート名候補

### 9.3 HTML資産

画像、CSS、JavaScriptは内容を知識本文へ混在させない。

次のみ記録する。

- 相対パス
- ハッシュ
- サイズ
- MIMEタイプ
- 参照元HTML
- 未解決リンク

### 9.4 文字コード

HTMLのmeta charset、HTTP相当meta、BOM、文字コード推定を組み合わせる。

推定結果と根拠を記録する。

---

## 10. CAB解析

### 10.1 展開ツール

第一候補:

```text
cabextract
```

補助候補:

```text
7z
```

外部コマンドは直接文字列連結せず、安全な引数配列で実行する。

### 10.2 必要パッケージ

```bash
sudo apt update
sudo apt install -y cabextract p7zip-full file
```

### 10.3 展開前記録

CABごとに次を記録する。

- 元の相対パス
- ファイル名
- サイズ
- SHA-256
- 更新日時
- カテゴリー
- 対応HTML候補
- `AutoTemplate.yml` からの参照有無

### 10.4 展開先

```text
knowledge/extracted/<category_id>/<template_id>/<cab_sha256先頭12文字>/
```

IDに使用できない文字は安全な形式へ変換する。

元名称はメタデータとして保持する。

### 10.5 安全対策

- `../` を含むエントリーを拒否する
- 絶対パスを拒否する
- 展開先外へ解決されるパスを拒否する
- シンボリックリンクを拒否または隔離する
- 展開ファイル数に上限を設定する
- 合計展開サイズに上限を設定する
- 単一ファイルサイズに上限を設定する
- タイムアウトを設定する
- 壊れたCABでも全処理を停止しない

### 10.6 内部ファイル解析

記録項目:

- CAB内相対パス
- ファイル名
- 拡張子
- ファイルサイズ
- SHA-256
- `file` コマンド結果
- MIME候補
- テキスト/バイナリ
- 推定文字コード
- 解析方式
- 解析状態
- エラー

### 10.7 構造解析対象

- XML
- INI
- JSON
- YAML
- CSV
- TXT
- REG
- HTML
- 独自テキスト形式

バイナリ形式は、次を記録する。

- マジックバイト
- 先頭部分の16進表現
- 埋め込み文字列候補
- GUID候補
- UTF-16文字列候補
- ファイル間差分用ハッシュ

バイナリを推測で書き換えない。

---

## 11. HTML、CAB、カテゴリーの関連付け

### 11.1 関連付け優先順位

1. `AutoTemplate.yml` による明示的参照
2. HTML内のCABへの明示的リンク
3. CABとHTMLの相対パスまたはベース名一致
4. 同一カテゴリーフォルダー内の同一テンプレート番号
5. 同一カテゴリーフォルダー内でCABとHTMLが各1件
6. タイトルまたは表示名の類似
7. 親フォルダー名の一致

### 11.2 関連付けスコア

各関連付けに次を保存する。

- `relation_score`
- `relation_status`
- `relation_reasons`
- `evidence`
- `manual_review_required`

状態:

- `confirmed`
- `probable`
- `ambiguous`
- `unresolved`
- `conflicting`

### 11.3 推測制限

類似度だけで `confirmed` にしない。

明示参照がない場合は、原則として `probable` 以下とする。

---

## 12. 監視設定候補抽出

### 12.1 共通要件

候補値だけでなく、抽出根拠を必ず保存する。

保存項目:

- 候補種別
- 候補値
- 正規化値
- 元ファイル
- CAB内パス
- XML要素名
- 属性名
- INIセクション
- キー名
- JSONパス
- 元文字列
- 信頼度
- 抽出ルール
- 人による確認状態

### 12.2 サービス監視候補

- サービス名
- 表示名
- 実行ファイル
- サービス状態
- スタートアップ種別
- 監視対象状態
- 自動回復設定候補
- 監視間隔
- 連続回数
- 重大度

### 12.3 イベントログ監視候補

- ログ名
- チャネル名
- イベントソース
- プロバイダー
- イベントID
- レベル
- タスクカテゴリ
- キーワード
- ユーザー
- コンピューター
- メッセージ文字列
- 正規表現
- 除外条件
- 発生回数
- 監視期間

### 12.4 パフォーマンスカウンター候補

- オブジェクト名
- カウンター名
- インスタンス名
- 比較演算子
- 警告しきい値
- 危険しきい値
- 監視間隔
- 連続回数
- 単位
- スケール

### 12.5 その他の監視候補

- プロセス
- ファイル
- フォルダー
- 容量
- レジストリ
- TCP/UDPポート
- URL
- SNMP
- WMI
- スクリプト
- コマンド
- サービス応答
- ログファイル
- Windows機能
- クラスター
- Hyper-V
- IIS
- SQL Server
- Linux
- VMware

### 12.6 未知監視種別

既知の分類へ無理に割り当てない。

```json
{
  "candidate_type": "unknown",
  "raw_type": "元の値",
  "source": "抽出元",
  "manual_review_required": true
}
```

---

## 13. 正規化データ

### 13.1 カテゴリーJSON

```text
knowledge/categories/<category_id>.json
```

例:

```json
{
  "category_id": "0005",
  "category_name": "データベースサーバー",
  "source_directory": "0005_データベースサーバー",
  "autotemplate_references": [],
  "template_ids": [],
  "file_count": 0,
  "warnings": []
}
```

### 13.2 テンプレートJSON

```text
knowledge/normalized/<template_id>.json
```

基本構造:

```json
{
  "schema_version": "1.0",
  "template_id": "0101",
  "template_name": "Windows システム監視 Basic",
  "category": {
    "id": "0000",
    "name": "標準構成テンプレート"
  },
  "source": {
    "directory": "0000_標準構成テンプレート",
    "cab_files": [],
    "html_files": [],
    "asset_files": []
  },
  "autotemplate": {
    "referenced": false,
    "yaml_paths": [],
    "raw_values": []
  },
  "description": null,
  "products": [],
  "operating_systems": [],
  "versions": [],
  "prerequisites": [],
  "warnings": [],
  "relationships": [],
  "monitoring_candidates": {
    "services": [],
    "event_logs": [],
    "performance_counters": [],
    "processes": [],
    "files": [],
    "registry": [],
    "ports": [],
    "urls": [],
    "snmp": [],
    "wmi": [],
    "scripts": [],
    "unknown": []
  },
  "analysis": {
    "status": "completed",
    "confidence": 0,
    "manual_review_required": true
  }
}
```

### 13.3 不明値

不明値を捏造しない。

次を使い分ける。

- `null`: 値そのものが存在しない、または不明
- `unknown`: 値の概念は分かるが内容不明
- `unresolved`: 関係を解決できない
- `ambiguous`: 複数候補がある
- `unsupported`: 現行解析機能では未対応

---

## 14. CAB設定マッピング

### 14.1 目的

BOM画面上の設定項目と、CAB内部のファイル・要素・属性・キー・値との対応関係を蓄積する。

### 14.2 保存先

```text
knowledge/mappings/bom_field_mappings.json
knowledge/mappings/bom_field_mappings.csv
```

### 14.3 マッピング構造

```json
{
  "bom_ui_field": "サービス名",
  "monitor_type": "service",
  "cab_internal_file": "unknown",
  "data_path": "unknown",
  "example_value": "MSSQLSERVER",
  "evidence_template_ids": [],
  "confidence": 0,
  "verification_status": "unverified",
  "notes": null
}
```

### 14.4 検証状態

- `unverified`
- `inferred`
- `verified-by-diff`
- `verified-by-import`
- `rejected`

### 14.5 1項目差分比較

将来、BOM上で設定を1項目だけ変更した2つのCABを比較し、変化した値を特定できること。

例:

```text
A.cab: サービス名 MSSQLSERVER
B.cab: サービス名 SQLSERVERAGENT
```

差分結果により、CAB内部でサービス名を保持する位置を推定する。

---

## 15. 索引

次を生成する。

```text
knowledge/index/categories.json
knowledge/index/templates.json
knowledge/index/products.json
knowledge/index/operating_systems.json
knowledge/index/cab_files.json
knowledge/index/html_files.json
knowledge/index/services.json
knowledge/index/event_logs.json
knowledge/index/event_providers.json
knowledge/index/event_ids.json
knowledge/index/performance_counters.json
knowledge/index/monitor_types.json
knowledge/index/unresolved.json
knowledge/index/search_documents.jsonl
```

### 15.1 全文検索文書

`search_documents.jsonl` は1行1JSONとする。

含める情報:

- カテゴリー
- テンプレート名
- HTML本文
- 製品名
- OS名
- CAB内部の解析可能な文字列
- サービス候補
- イベントログ候補
- パフォーマンスカウンター候補
- 注意事項
- 前提条件

外部AI APIやベクトルデータベースはVer.1.0では使用しない。

---

## 16. レポート

### 16.1 CSV

```text
knowledge/reports/category_inventory.csv
knowledge/reports/template_inventory.csv
knowledge/reports/source_file_inventory.csv
knowledge/reports/autotemplate_paths.csv
knowledge/reports/autotemplate_references.csv
knowledge/reports/cab_html_relationships.csv
knowledge/reports/cab_internal_files.csv
knowledge/reports/service_candidates.csv
knowledge/reports/eventlog_candidates.csv
knowledge/reports/eventid_candidates.csv
knowledge/reports/performance_counter_candidates.csv
knowledge/reports/unknown_candidates.csv
knowledge/reports/unresolved_items.csv
knowledge/reports/errors.csv
```

### 16.2 Excel

```text
knowledge/reports/import_summary.xlsx
```

シート:

- Summary
- Categories
- Templates
- Source Files
- AutoTemplate Keys
- AutoTemplate References
- CAB Files
- CAB Internal Files
- HTML Files
- CAB-HTML Relations
- Products
- Operating Systems
- Services
- Event Logs
- Event Providers
- Event IDs
- Performance Counters
- Unknown Candidates
- Unresolved
- Errors

### 16.3 Excel要件

- 1行目を見出しとする
- オートフィルターを設定する
- 見出しを固定する
- 列幅を読みやすく調整する
- 長文セルは折り返す
- エラーや未解決項目を確認しやすくする
- 元ファイルへの相対パスを記載する

---

## 17. 設定ファイル

追加:

```text
config/knowledge.yml
```

例:

```yaml
knowledge:
  source_dir: import/TemplateData
  output_dir: knowledge

  autotemplate:
    filenames:
      - AutoTemplate.yml
      - AutoTemplate.yaml
    preserve_unknown_keys: true

  file_types:
    cab:
      - .cab
    html:
      - .html
      - .htm
    text:
      - .xml
      - .ini
      - .conf
      - .cfg
      - .json
      - .yaml
      - .yml
      - .csv
      - .txt
      - .reg

  extraction:
    cab_command: cabextract
    fallback_command: 7z
    timeout_seconds: 120
    max_files_per_cab: 10000
    max_total_size_mb: 500
    max_single_file_size_mb: 100

  parsing:
    max_text_file_size_mb: 20
    encodings:
      - utf-8-sig
      - utf-8
      - cp932
      - shift_jis
      - utf-16-le
      - utf-16-be

  import:
    calculate_sha256: true
    incremental: true
    retain_removed_records: true

  relationship:
    explicit_reference_score: 100
    basename_match_score: 80
    template_number_match_score: 70
    same_directory_single_pair_score: 60
    title_similarity_threshold: 0.85

  logging:
    level: INFO
    file: logs/bom-knowledge-import.log
```

CLIオプションは設定ファイルより優先する。

---

## 18. 推奨モジュール構成

```text
src/bom_monitor_builder/
├── knowledge/
│   ├── __init__.py
│   ├── cli.py
│   ├── importer.py
│   ├── source_scanner.py
│   ├── autotemplate_parser.py
│   ├── category_parser.py
│   ├── filename_parser.py
│   ├── html_parser.py
│   ├── cab_extractor.py
│   ├── cab_parser.py
│   ├── text_parser.py
│   ├── binary_inspector.py
│   ├── relationship_resolver.py
│   ├── candidate_extractor.py
│   ├── normalizer.py
│   ├── mapping_repository.py
│   ├── index_builder.py
│   ├── report_builder.py
│   ├── state_repository.py
│   ├── validator.py
│   ├── comparer.py
│   └── models.py
```

すべての処理を1ファイルへ実装しない。

責務ごとに分割する。

---

## 19. データモデル

Pydanticを使用して、最低限次を定義する。

- SourceFile
- Category
- Template
- AutoTemplateNode
- AutoTemplateReference
- CabFile
- CabInternalFile
- HtmlDocument
- Relationship
- MonitoringCandidate
- ServiceCandidate
- EventLogCandidate
- PerformanceCounterCandidate
- FieldMapping
- ImportState
- ImportResult
- ValidationResult
- ErrorRecord

JSONには `schema_version` を含める。

---

## 20. ログ

### 20.1 出力先

```text
logs/bom-knowledge-import.log
```

### 20.2 記録内容

- 実行ID
- 開始日時
- 終了日時
- 入力パス
- 出力パス
- コマンドラインオプション
- 対象ファイル数
- カテゴリー数
- CAB数
- HTML数
- 成功件数
- 警告件数
- 失敗件数
- スキップ件数
- CAB展開結果
- YAML解析結果
- 文字コード判定結果
- 関連付け結果
- 例外
- 処理時間

### 20.3 機密情報

認証情報らしい文字列をログへそのまま出力しない。

---

## 21. エラー処理

次のエラーを個別に扱う。

- 入力ディレクトリなし
- 権限不足
- YAML構文エラー
- 文字コード不明
- CAB破損
- CAB展開ツールなし
- CAB展開タイムアウト
- パストラバーサル
- 展開上限超過
- HTML構文異常
- XML構文異常
- JSON構文異常
- 同一参照先が複数
- 参照先なし
- 出力書込み失敗
- 既存状態ファイル破損

1件の失敗で全体処理を中断しない。

ただし、入力ルートまたは出力ルートが利用できない場合は異常終了する。

---

## 22. セキュリティ

- 入力ファイルを変更しない
- 入力ディレクトリを削除しない
- 展開先外への書込みを防止する
- シンボリックリンクを安全に扱う
- 外部コマンドへシェル展開可能な文字列を渡さない
- 巨大ファイルを無制限に読み込まない
- ZIP/CAB爆弾相当の展開を制限する
- 一時ファイルを適切に削除する
- ファイル権限を必要以上に広げない
- HTML内のJavaScriptを実行しない
- 外部URLへ自動アクセスしない

---

## 23. テスト要求

### 23.1 単体テスト

```text
tests/unit/test_source_scanner.py
tests/unit/test_autotemplate_parser.py
tests/unit/test_category_parser.py
tests/unit/test_filename_parser.py
tests/unit/test_html_parser.py
tests/unit/test_cab_extractor.py
tests/unit/test_cab_parser.py
tests/unit/test_relationship_resolver.py
tests/unit/test_candidate_extractor.py
tests/unit/test_normalizer.py
tests/unit/test_mapping_repository.py
tests/unit/test_index_builder.py
tests/unit/test_report_builder.py
tests/unit/test_validator.py
tests/unit/test_comparer.py
```

### 23.2 結合テスト

```text
tests/integration/test_template_data_inspect.py
tests/integration/test_template_data_import.py
tests/integration/test_incremental_import.py
tests/integration/test_full_report_generation.py
```

### 23.3 テストケース

- `AutoTemplate.yml` が存在する
- `AutoTemplate.yml` が存在しない
- YAMLが配列ルート
- YAMLが辞書ルート
- YAMLに未知キーがある
- YAMLにCAB参照がある
- YAML参照先が存在しない
- CABとHTMLのベース名が一致する
- CAB拡張子が大文字
- HTML拡張子が大文字
- 日本語カテゴリー名
- 日本語ファイル名
- CP932 HTML
- UTF-8 HTML
- CABが壊れている
- CABが空
- CAB展開ツールがない
- パストラバーサルを含むCAB
- 同一SHA-256の重複CAB
- HTMLだけ存在する
- CABだけ存在する
- CAB複数、HTML1件
- HTML複数、CAB1件
- 関連付けが曖昧
- dry-run
- 初回取込
- 2回目の変更なし取込
- ファイル追加
- ファイル更新
- ファイル削除
- `--force`
- レポート生成
- インデックス検証

実物のBOM CABをGitへコミットしない。

テストでは小さな模擬データ、モックまたはテスト専用CABを使う。

---

## 24. 依存パッケージ

候補:

```text
beautifulsoup4
lxml
charset-normalizer
pydantic
PyYAML
openpyxl
pandas
click
```

依存関係を追加した場合、次を整合させる。

- `requirements.txt`
- `requirements-dev.txt`
- `pyproject.toml`

---

## 25. ドキュメント

追加:

```text
docs/template_data_import.md
docs/autotemplate_analysis.md
docs/cab_analysis.md
docs/knowledge_schema.md
docs/bom_field_mapping.md
```

READMEに次を追記する。

- Windowsからの `TemplateData` コピー方法
- 推奨配置
- 必要パッケージ
- inspect
- dry-run
- import
- validate
- compare
- 出力先
- エラー確認
- 既知の制限

---

## 26. 実行例

### 26.1 事前確認

```bash
cd /home/ubuntu/projects/bom-monitor-template-builder
source .venv/bin/activate

bom-monitor-builder knowledge inspect \
  --source import/TemplateData
```

### 26.2 dry-run

```bash
bom-monitor-builder knowledge import \
  --source import/TemplateData \
  --dry-run
```

### 26.3 本取込

```bash
bom-monitor-builder knowledge import \
  --source import/TemplateData
```

### 26.4 検証

```bash
bom-monitor-builder knowledge validate
```

### 26.5 CAB比較

```bash
bom-monitor-builder knowledge compare \
  --left samples/cab/service_a.cab \
  --right samples/cab/service_b.cab
```

---

## 27. 完了条件

Ver.1.0は、次を満たした時点で完了とする。

1. `TemplateData` 全体を入力として認識できる
2. カテゴリーフォルダーを一覧化できる
3. `AutoTemplate.yml` を未知キーを失わず解析できる
4. CAB、HTML、付属ファイルを一覧化できる
5. CABを安全に展開できる
6. HTML本文および表を解析できる
7. `AutoTemplate.yml`、カテゴリー、HTML、CABを関連付けできる
8. 未解決の関連付けを明示できる
9. サービス、イベントログ、イベントID、パフォーマンスカウンター候補を抽出できる
10. テンプレート単位の正規化JSONを生成できる
11. 横断索引を生成できる
12. CSVおよびExcelレポートを生成できる
13. 差分取込ができる
14. dry-runができる
15. 解析失敗があっても他のファイルを継続処理できる
16. CAB間の差分比較ができる
17. BOM画面項目とCAB内部値のマッピングを保存できる
18. 単体テストと結合テストが成功する
19. `ruff` が成功する
20. `mypy` が成功する

---

## 28. Ver.1.0で実施しないこと

次はVer.1.0の対象外とする。

- AIモデルの追加学習
- 外部AI APIへのデータ送信
- ベクトルデータベース
- CABの新規生成
- CAB内部バイナリの直接書換え
- BOMへのテンプレート自動インポート
- Windows端末へのリモート情報採取
- GUI
- BOMサービスへの直接接続
- 本番環境への自動設定反映

---

## 29. Codexへの実装指示

以下を守って実装すること。

1. 最初に既存プロジェクト構成とコードを調査する
2. 既存CLI、テスト、設定を壊さない
3. 実装前に作業計画を提示する
4. `AutoTemplate.yml` のスキーマを仮定しない
5. 未知キーを保持する
6. 既存の実物CABをGitへ追加しない
7. 元ファイルを変更しない
8. パストラバーサル対策を実装する
9. 1ファイルへ処理を集中させない
10. 例外処理とログを実装する
11. dry-runを先に実装する
12. 単体テストを機能と同時に追加する
13. 型注釈を付ける
14. `ruff` と `mypy` に対応する
15. 不明点を推測で埋めず、未解決として報告する

---

## 30. Codexの作業順序

一度にすべてを実装せず、次の順番で進めること。

### Iteration 1

- 入力構造走査
- `knowledge inspect`
- source inventory
- カテゴリー解析
- `AutoTemplate.yml` 汎用解析
- dry-run
- テスト

### Iteration 2

- HTML解析
- CABとHTMLの基本関連付け
- レポート
- テスト

### Iteration 3

- CAB安全展開
- CAB内部ファイル一覧
- テキスト形式解析
- テスト

### Iteration 4

- 監視候補抽出
- 正規化JSON
- インデックス
- Excelレポート
- テスト

### Iteration 5

- 差分取込
- validate
- compare
- BOM設定項目マッピング
- ドキュメント
- 全体テスト

各Iteration完了時に、次を報告すること。

- 変更ファイル一覧
- 実装機能
- CLI実行例
- テスト結果
- `ruff` 結果
- `mypy` 結果
- 未解決事項
- 次のIterationで行う作業

---

## 31. 最初にCodexへ依頼する範囲

最初の依頼では、Iteration 1だけを実装すること。

実装対象:

- `import/TemplateData` の走査
- カテゴリー抽出
- 全ファイルの棚卸し
- `AutoTemplate.yml` の汎用YAML解析
- YAMLパスと値の一覧化
- `knowledge inspect`
- `knowledge import --dry-run`
- source inventoryのJSON/CSV出力
- AutoTemplate解析JSON/CSV出力
- 設定ファイル
- ログ
- 単体テスト
- ドキュメント

Iteration 1ではCABを展開しない。

Iteration 1の結果を確認し、実際の `AutoTemplate.yml` の構造が判明してから、Iteration 2以降の詳細を調整する。

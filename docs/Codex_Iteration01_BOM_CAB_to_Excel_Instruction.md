# Codex Iteration 01 指示書

## BOM CAB設定仕様書生成ツール

- 文書名: Codex Iteration 01 BOM CAB設定仕様書生成ツール 開発指示書
- 対象プロジェクト: BOM設定をExcel化
- 想定実装言語: Python 3.11以降
- 主な実行環境: Windows 10/11、Windows Server 2022/2025
- 開発環境: Ubuntu 24.04またはWindows上のCodex CLI
- 初版の対象: BOM for Windows 8.0の監視設定エクスポートCAB

---

## 1. 目的

BOM for WindowsからエクスポートされたCABファイルを解析し、CAB内に保存されている監視グループおよび監視項目の設定を、閲覧しやすいExcel設定仕様書として出力するツールを作成する。

既存の `TemplateMaker.exe` はCABからHTMLおよびReadMe.txtを生成するが、本ツールは既存EXEの逆コンパイルや内部実装への依存を避け、CAB内部の `MANIFEST.MF` とXMLファイルを直接読み取る。

初版では、添付サンプルに含まれる `Custom2` 監視を正しくExcel化する。将来、イベントログ監視、サービス監視、パフォーマンスカウンター監視など、異なる監視種類のXML構造を追加しやすい設計とする。

---

## 2. 参照資料

リポジトリ内に、ユーザーから提供された `templatemaker.zip` を展開して参照できるようにする。

想定される主な参照ファイルは次のとおり。

```text
templatemaker/
├─ TemplateMaker.exe
├─ TemplateMaker.exe.config
├─ Microsoft.Deployment.Compression.Cab.dll
├─ Microsoft.Deployment.Compression.dll
├─ SupportCommon.dll
├─ base/
│  ├─ template.htm
│  └─ ReadMe.txt
├─ temp/
│  ├─ MANIFEST.MF
│  └─ Monitor/
│     └─ GRP01/
│        ├─ GRP.xml
│        ├─ MON01.xml
│        ├─ MON02.xml
│        ├─ MON03.xml
│        └─ MON04.xml
└─ out/
   ├─ 生成済みCAB
   ├─ 生成済みHTML
   └─ 生成済みReadMe.txt
```

`temp` フォルダーはCABを展開した内容の参照サンプルとして扱う。`out` フォルダーは既存ツールの出力例として扱う。

既存EXEおよびDLLは、挙動と入出力を理解するための参考資料に限定する。逆コンパイルは初版の作業範囲に含めない。

---

## 3. 確認済みCAB構造

### 3.1 MANIFEST.MF

サンプルでは次の情報が格納されている。

```text
Product: BOM for Windows
Type: Monitor_Export
MajorVersion: 8
MinorVersion: 0
```

最低限、次のキーを読み取る。

- Product
- Type
- MajorVersion
- MinorVersion

未知のキーが存在してもエラーにせず、追加情報として保持すること。

### 3.2 監視グループ

監視グループは、次のようなパスに保存される。

```text
Monitor/GRP01/GRP.xml
```

サンプルのルート要素は `MonitorGroup` であり、次の要素を含む。

- ParentId
- Id
- Name
- Comments
- IconIndex
- Enabled
- TTMon
- TTTue
- TTWed
- TTThu
- TTFri
- TTSat
- TTSun

複数の `GRPxx` フォルダーが存在する可能性を考慮すること。

### 3.3 監視項目

各監視項目は、グループ配下の `MONxx.xml` に保存される。

```text
Monitor/GRP01/MON01.xml
Monitor/GRP01/MON02.xml
...
```

サンプルのルート要素は `MonitorItem` であり、次の要素を含む。

- Type
- ParentId
- Id
- Name
- StartTime
- Interval
- IntervalUnit
- CLSID
- ObjectName
- ValueName
- Options
- CmpMethodR
- CmpValueR
- CmpMethodY
- CmpValueY
- Comments
- IconIndex
- Enabled
- DisplayUnit
- Scale

初版で確認済みの監視タイプは `Custom2` である。

XMLに未知の要素が存在した場合、破棄せず、後述する「XML全項目」シートまたは内部データへ保持すること。

---

## 4. 実装する機能

### 4.1 入力

次のいずれかを入力できること。

1. 単一CABファイル
2. CABファイルを複数含むフォルダー
3. 開発・デバッグ用として、CAB展開済みフォルダー

コマンドライン例:

```bash
python -m bom_cab_excel input/sample.cab
python -m bom_cab_excel input/ --output output/
python -m bom_cab_excel extracted/sample/ --extracted
```

最低限実装するCLIオプション:

```text
input                         CABファイル、CAB格納フォルダー、または展開済みフォルダー
-o, --output                  出力先ファイルまたは出力先フォルダー
--extracted                   入力をCAB展開済みフォルダーとして扱う
--keep-extracted              一時展開フォルダーを削除しない
--overwrite                   既存のExcelを上書きする
--log-level                   DEBUG / INFO / WARNING / ERROR
--version                     ツールのバージョンを表示する
```

### 4.2 CAB展開

CAB展開処理は解析処理から分離し、`CabExtractor` のような抽象化を行う。

Windowsでの優先順位:

1. Windows標準の `expand.exe`
2. `7z.exe` または `7zz.exe`

Linuxでの優先順位:

1. `7zz`
2. `7z`
3. `cabextract`

利用可能な展開コマンドを自動検出する。どれも見つからない場合は、必要なツールと導入例を明確に表示して終了する。

CABの展開は一時ディレクトリで行い、パストラバーサルを防止する。展開後の各パスが一時ディレクトリ配下に収まっていることを検証する。

ファイル名に日本語または `#U30c7` のようなUnicodeエスケープ表現が含まれる場合がある。入力ファイル名をそのまま表示できない場合でも、処理自体が停止しないようにする。

### 4.3 MANIFEST解析

`MANIFEST.MF` を `key: value` 形式として読み取る。

- UTF-8を優先する。
- UTF-8で読めない場合はCP932を試す。
- 空行を許容する。
- 未知のキーを許容する。
- `Type` が `Monitor_Export` でない場合は警告を表示する。ただし、可能な範囲で解析を続行する。

### 4.4 XML解析

Python標準の `xml.etree.ElementTree` または `lxml` を使用する。

初版は標準ライブラリを優先し、不要な依存を増やさない。

XML名前空間が付与されていても、要素のローカル名で読み取れるようにする。

値の型変換:

- `true` / `false`: Pythonのbool
- 整数として解釈できる値: int
- 小数として解釈できる値: Decimalまたはfloat
- 空要素: 空文字列またはNone
- その他: 文字列

ただし、Excel出力時に元の文字列表現も失わない設計が望ましい。

### 4.5 比較演算子の日本語化

サンプルで確認済みの比較方法を次のように表示する。

| XML値 | Excel表示 |
|---|---|
| GreaterEqual | 以上 |
| Greater | より大きい |
| LessEqual | 以下 |
| Less | より小さい |
| Equal | 等しい |
| NotEqual | 等しくない |

未知の値は無理に変換せず、元の値を表示し、警告ログへ記録する。

注意判定は `CmpMethodY` と `CmpValueY`、危険判定は `CmpMethodR` と `CmpValueR` から生成する。

例:

```text
CmpMethodY = GreaterEqual
CmpValueY  = 20
```

Excel表示:

```text
20 以上
```

### 4.6 監視間隔の日本語化

最低限、次の単位を変換する。

| XML値 | Excel表示 |
|---|---|
| Seconds | 秒 |
| Minutes | 分 |
| Hours | 時間 |
| Days | 日 |

例:

```text
Interval = 5
IntervalUnit = Minutes
```

Excel表示:

```text
5分
```

未知の単位は元の値を併記する。

### 4.7 Options解析

`Options` は初版では必ず元文字列をそのまま保存する。

加えて、可能な範囲で次の値を抽出する。

- `-RetryInterval:<値>`
- `-t:<値>`
- `-x:<値>`
- PowerShellのスクリプトパス
- その他の引数

抽出に失敗してもCAB全体の解析を失敗させない。

サンプル例:

```text
-RetryInterval:60000 -t:60000 "-x:-ExecutionPolicy Bypass -F \"$(InstallDir)\bin\support\disklatency.ps1\""
```

想定する抽出結果:

- リトライ間隔: 60000 ms
- タイムアウト: 60000 ms
- 実行形式: PowerShell
- スクリプト: `$(InstallDir)\bin\support\disklatency.ps1`
- 元のOptions: 全文

### 4.8 Excel出力

`openpyxl` を使用し、CABファイルごとに1つの `.xlsx` を作成する。

出力ファイル名の初期値:

```text
<入力CABのベース名>_設定仕様書.xlsx
```

ファイル名として使用できない文字は `_` に置換する。

---

## 5. Excelのシート構成

### 5.1 「表紙」シート

次の項目を縦型の帳票として表示する。

| 項目 | 内容 |
|---|---|
| 文書名 | BOM監視設定仕様書 |
| 元CABファイル名 | 入力ファイル名 |
| 製品名 | MANIFESTのProduct |
| エクスポート種別 | MANIFESTのType |
| BOMバージョン | MajorVersion.MinorVersion |
| 監視グループ数 | 解析件数 |
| 監視項目数 | 解析件数 |
| 作成日時 | Excel生成日時 |
| 生成ツールバージョン | 本ツールのバージョン |

作成日時はローカルタイムで記録し、表示形式を `yyyy/mm/dd hh:mm:ss` とする。

### 5.2 「監視グループ一覧」シート

1グループ1行で出力する。

列:

1. No.
2. グループフォルダー
3. グループ名
4. 有効
5. コメント
6. アイコン番号
7. 月曜日
8. 火曜日
9. 水曜日
10. 木曜日
11. 金曜日
12. 土曜日
13. 日曜日
14. ParentId
15. Id

Enabledは `有効` / `無効` と表示する。

曜日設定値は初版では元の数値を保持し、別列またはセルコメントで元値を確認できるようにする。`-1` の意味を推測して「常時」などと断定しない。

### 5.3 「監視項目一覧」シート

1監視項目1行で出力する。

列:

1. No.
2. グループ名
3. 監視ファイル
4. 監視名
5. 監視タイプ
6. 有効
7. 監視間隔
8. 開始時刻
9. 注意判定
10. 危険判定
11. 表示単位
12. スケール
13. 実行オブジェクト
14. 値名
15. コメント

### 5.4 「監視項目詳細」シート

監視項目の全主要設定を縦型ブロックで出力する。

各監視項目のブロック例:

```text
監視No.
グループ名
監視名
監視タイプ
有効
開始時刻
監視間隔
CLSID
ObjectName
ValueName
Options
RetryInterval
Timeout
実行スクリプト
注意比較方法
注意しきい値
危険比較方法
危険しきい値
表示単位
スケール
コメント
XMLファイルパス
```

監視項目ごとに空行または見出し行で区切る。

### 5.5 「XML全項目」シート

未知の監視タイプや未知の要素を確認できるように、解析したXML要素を正規化して出力する。

列:

1. 種別 (`MonitorGroup` / `MonitorItem`)
2. グループフォルダー
3. XMLファイル
4. 監視名またはグループ名
5. 要素名
6. 値

このシートにより、初版で専用列へ割り当てていないXML項目も失わないようにする。

### 5.6 「解析情報」シート

次を出力する。

- MANIFESTの全キーと値
- CAB展開に使用した方式
- 入力ファイルのSHA-256
- 解析開始日時
- 解析完了日時
- 警告一覧
- 認識した監視タイプ一覧
- 認識できなかった比較演算子または単位

パスに個人情報が含まれる可能性があるため、一時ディレクトリの絶対パスは原則としてExcelへ記録しない。

---

## 6. Excel書式

すべてのシートに次の書式を適用する。

- 先頭行を固定する。
- 一覧シートにはオートフィルターを設定する。
- 見出し行は太字、背景色、中央揃えとする。
- 長い文字列には折り返しを設定する。
- 列幅を内容に応じて調整する。ただし最大幅を60程度に制限する。
- `Options` など長文列は幅60、折り返しを設定する。
- 外枠および主要セルへ罫線を設定する。
- 印刷時に見出し行が各ページで繰り返されるように設定する。
- 用紙方向は一覧シートを横、表紙と詳細シートを縦とする。
- 日本語フォントは環境依存を避けるため、特定フォントの存在を必須としない。
- 数値は可能な限り数値セルとして出力する。
- 元XML値を保持すべき項目は文字列として出力する。

色や装飾は過剰にせず、業務用設定仕様書として読みやすいものにする。

---

## 7. 推奨プロジェクト構成

```text
bom-cab-excel/
├─ README.md
├─ pyproject.toml
├─ .gitignore
├─ src/
│  └─ bom_cab_excel/
│     ├─ __init__.py
│     ├─ __main__.py
│     ├─ cli.py
│     ├─ models.py
│     ├─ extractor.py
│     ├─ manifest.py
│     ├─ xml_parser.py
│     ├─ options_parser.py
│     ├─ formatter.py
│     ├─ excel_writer.py
│     ├─ logging_config.py
│     └─ exceptions.py
├─ tests/
│  ├─ test_manifest.py
│  ├─ test_xml_parser.py
│  ├─ test_options_parser.py
│  ├─ test_excel_writer.py
│  └─ fixtures/
│     └─ sample_extracted/
├─ samples/
│  └─ README.md
├─ docs/
│  ├─ architecture.md
│  └─ supported_monitor_types.md
└─ output/
```

---

## 8. データモデル

`dataclasses` を利用し、最低限次のモデルを定義する。

```python
ManifestInfo
MonitorGroup
MonitorItem
ParsedCab
ParseWarning
```

概念例:

```python
@dataclass
class MonitorItem:
    group_folder: str
    xml_file: str
    values: dict[str, object]
    raw_values: dict[str, str]
    unknown_values: dict[str, str]
```

既知項目をすべて個別フィールドにしてもよいが、将来の監視タイプ追加に耐えられるよう、元のキー・値辞書も必ず保持する。

---

## 9. ログとエラー処理

ログは標準エラーおよびログファイルへ出力可能にする。

主なエラー区分:

- 入力ファイルが存在しない
- CAB展開ツールがない
- CAB展開に失敗した
- MANIFEST.MFがない
- XMLが不正
- Excel出力先へ書き込めない
- 既存ファイルがあり、`--overwrite` がない

一部のXMLだけが不正な場合は、可能な限り残りのXMLを処理し、Excelの解析情報シートとログへ警告を残す。

終了コード例:

| コード | 意味 |
|---:|---|
| 0 | 正常終了 |
| 1 | 入力・引数エラー |
| 2 | CAB展開エラー |
| 3 | 解析エラー |
| 4 | Excel出力エラー |
| 10 | 一部警告ありで出力完了 |

終了コード10を採用するかどうかはREADMEへ明記する。

---

## 10. セキュリティ要件

- 入力CABを実行しない。
- 同梱EXEやDLLを自動実行しない。
- XML外部実体参照を無効化する。
- CAB展開時のパストラバーサルを防止する。
- マクロ付きExcelを生成しない。
- 数式インジェクションを防ぐ。XML値が `=`, `+`, `-`, `@` で始まる場合、Excelで数式として評価されないよう文字列として安全に出力する。
- 一時フォルダーは処理後に削除する。ただし `--keep-extracted` 指定時を除く。
- ログへCAB内容の機密値を過剰に出力しない。DEBUG時のみ詳細値を許可する。

---

## 11. テスト要件

### 11.1 単体テスト

最低限、次をテストする。

- MANIFESTの正常解析
- MANIFESTの未知キー
- UTF-8およびCP932の読み込み
- 名前空間付きXML
- 空要素
- bool、整数、小数、文字列の型変換
- `Custom2` の解析
- 比較演算子の日本語化
- 監視間隔の日本語化
- OptionsからRetryIntervalとTimeoutを抽出
- 未知の監視タイプを保持
- 数式インジェクション対策
- Excelに必要なシートが生成される
- 行数、主要セル値、オートフィルター、固定行が正しい

### 11.2 結合テスト

提供サンプルを使用し、次を確認する。

- Productが `BOM for Windows`
- Typeが `Monitor_Export`
- BOMバージョンが `8.0`
- グループ数が1
- グループ名が `ディスクパフォーマンス監視`
- 監視項目数が4
- `MON01.xml` の監視名が `レイテンシ(ディスク転送時間)`
- `MON01.xml` の監視タイプが `Custom2`
- 監視間隔が `5分`
- 注意判定が `20 以上`
- 危険判定が `30 以上`
- ObjectNameが `powershell.exe`
- RetryIntervalが `60000`
- Timeoutが `60000`
- 出力Excelがopenpyxlで再度正常に開ける

### 11.3 回帰テスト用スナップショット

Excelバイナリ全体の一致比較は行わない。代わりに、主要セル値、シート名、行数、列名、セル型、書式の主要プロパティを検証する。

---

## 12. READMEに記載する内容

- ツールの目的
- 対応OS
- Pythonバージョン
- インストール方法
- CAB展開ツールの要件
- CLI使用例
- 入出力例
- 対応済み監視タイプ
- 未対応監視タイプの扱い
- トラブルシューティング
- 開発者向けテスト方法
- EXE化方法は将来対応であること

初版はPython CLIとして完成させる。PyInstallerによるWindows EXE化は、CLIが安定した後の次イテレーションとする。

---

## 13. 実装手順

Codexは次の順序で作業すること。

1. リポジトリと基本ファイルを作成する。
2. `pyproject.toml` と依存関係を定義する。
3. データモデルを作成する。
4. MANIFEST解析を実装し、単体テストを作成する。
5. XML解析を実装し、単体テストを作成する。
6. Options解析を実装し、単体テストを作成する。
7. 展開済みフォルダー入力でExcelを作れるようにする。
8. Excel書式と各シートを実装する。
9. CAB展開アダプターを実装する。
10. CLIを完成させる。
11. 提供サンプルで結合テストを実行する。
12. READMEと設計文書を更新する。
13. lint、型チェック、テストを実行し、エラーを解消する。

CAB展開機能より先に、提供済みの `temp` フォルダーを使用してXML解析とExcel出力を完成させる。これにより、CAB展開環境の差異と解析ロジックを分離する。

---

## 14. 完了条件

次のすべてを満たした時点で初版完了とする。

- 提供サンプルCABまたは展開済みフォルダーを入力できる。
- 1グループ、4監視項目を正しく認識できる。
- 指定した6シートを持つExcelが生成される。
- Excelで日本語が文字化けしない。
- 既知項目と元XML全項目の両方が保存される。
- 未知のXML要素があっても処理が停止しない。
- 同梱EXEやDLLを実行しない。
- 単体テストおよび結合テストが成功する。
- READMEだけで別の開発者がセットアップと実行を行える。

---

## 15. 初版で行わないこと

- `TemplateMaker.exe` の逆コンパイル
- HTMLおよびReadMe.txtの完全再現
- BOMへ設定をインポートする機能
- CAB内容の編集および再CAB化
- すべての監視タイプの専用解析
- GUI
- Windows EXE配布物の作成
- 電子署名

これらは初版の解析結果と追加CABサンプルを確認後、次イテレーションで検討する。

---

## 16. 将来拡張

- 監視タイプごとの専用パーサープラグイン
- 複数CABの統合設定仕様書
- CAB間の設定差分比較
- HTML出力
- JSON中間形式の出力
- GUIによるCAB選択
- PyInstallerでのEXE化
- Excelテンプレート差し替え
- BOM 7.0および将来バージョンへの対応
- 監視グループ階層の図示
- アクション設定、通知設定、スケジュールの詳細解析

---

## 17. Codexへの重要な指示

- 推測でXML要素の意味を確定しないこと。
- 意味が不明な値は元値を保持し、READMEまたは解析情報へ「意味未確定」と記載すること。
- サンプルに存在しない監視タイプを、存在する前提で作り込まないこと。
- 既存EXEの出力HTMLは表示名称の参考にしてよいが、HTMLの文字列だけを解析元にしないこと。
- 実装途中でもテストを追加し、各段階で動作を確認すること。
- コード内へサンプル固有のグループ名、監視名、しきい値をハードコードしないこと。
- WindowsパスとLinuxパスの両方を考慮すること。
- 文字コード、長いOptions文字列、日本語ファイル名を重点的に確認すること。

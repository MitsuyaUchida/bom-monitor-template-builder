# BOM Monitor Template Builder

## Windows setup (PowerShell)

Python 3.12 or later is required.

```powershell
cd D:\projects\bom-monitor-template-builder

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .

pytest

bom-monitor-builder --help
```

If pytest cannot access the Windows shared Temp directory, use a workspace-local temporary directory:

```powershell
pytest --basetemp=.pytest-tmp
```

Example build:

```powershell
bom-monitor-builder build `
  --input "import\cab\Hyper-V.CAB" `
  --output "output\Hyper-V.xlsx" `
  --overwrite `
  --keep-intermediate `
  --verbose
```

## 概要

このリポジトリは、BOM 監視設定の実ファイルを次の 3 つの入口で扱うためのプロジェクトです。

- `build`: CAB 解析から設計書生成・検証までを 1 コマンドで実行する
- `cab-excel`: BOM 監視設定 CAB を解析し、確認用の解析 Excel を生成する
- `design-excel`: 解析 Excel を共通内部モデルへ読み込み、YAML プロファイルと Excel テンプレートを使って監視設計書を生成する

補助的に、既存の `TemplateData` 調査・知識化機能も含みます。

初期開発完了時点の正式な記録は [initial_development_completion.md](docs/initial_development_completion.md)、運用手順は [operation_guide.md](docs/operation_guide.md) を参照してください。

## 対応範囲

初期開発完了時点で、実ファイル検証済みの監視種別は次のとおりです。

- AWS コスト監視
- Arcserve UDP 9.0
- SQL Server 2022（Windows版）
- Hyper-V / Apex One

検証結果の詳細は [initial_development_completion.md](docs/initial_development_completion.md) に記録しています。

## ディレクトリ

通常運用で主に使うディレクトリは次のとおりです。

```text
import/cab/      CAB入力
input/           cab-excel が生成した解析Excel
reference/       人が作成した正解設計書
templates/       design-excel が参照する生成用テンプレート
profiles/        YAMLプロファイル
output/          生成設計書、dump-model JSON、比較用出力
tests/           統合テスト、単体テスト
docs/            仕様、運用、完了記録
src/             実装本体
```

## セットアップ

```bash
./scripts/setup.sh
source .venv/bin/activate
```

`pip install -e .` 後は次の CLI が利用できます。

- `bom-monitor-builder`
- `bom-cab-excel`

## Windows EXE版

Windows 用の CLI EXE は PyInstaller の `--onefile` 形式で作成します。ビルド前に `.venv` を用意し、開発依存関係をインストールしてください。

配布用のGUI版・CLI版EXEは、GitHubの [Releases](https://github.com/MitsuyaUchida/bom-monitor-template-builder/releases) から `bom-monitor-builder-gui.exe` または `bom-monitor-builder.exe` をダウンロードしてください。配布先Windows PCへのPythonインストールは不要です。

CLI版の実行例（ReleaseからダウンロードしたEXEをCABと同じフォルダーに置いた場合）:

```powershell
.\bom-monitor-builder.exe build `
  --input ".\Hyper-V.CAB" `
  --output ".\Hyper-V.xlsx" `
  --overwrite
```

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
.\build_exe.ps1
```

生成先は `dist\bom-monitor-builder.exe` です。実行例:

```powershell
.\dist\bom-monitor-builder.exe build `
  --input ".\input.CAB" `
  --output ".\output.xlsx"
```

配布先 PC には Python のインストールは不要です。profiles、YAML、設定ファイル、テンプレート Excel は EXE に同梱されます。入力 CAB と出力先は実行時に指定してください。

### GUI版

GUI版はCLI版とは別のEXEとしてビルドします。次を実行すると `dist\bom-monitor-builder-gui.exe` が作成されます。CLI版EXEは削除・上書きされません。

```powershell
.\build_gui_exe.ps1
```

`bom-monitor-builder-gui.exe` をダブルクリックし、CABファイルを選択して出力先を確認後、「変換開始」を押してください。CAB選択時に出力先が未指定なら、CABと同じフォルダー・ベース名の `.xlsx` を設定します。既存ファイル上書きは初期状態で有効、中間ファイルの保持は無効です。変換結果と `Validation: PASS` は実行ログに表示されます。

「終了」ボタンまたはウィンドウ右上の閉じる操作でGUIを終了できます。

## 最も簡単な使い方

正式仕様の入力形式は `build --input <CAB>` です。

```bash
.venv/bin/bom-monitor-builder build \
  --input "import/cab/0307_sqlserver2022_windows.cab"
```

この 1 コマンドで次を実行します。

1. CAB を解析して中間 Excel を生成
2. 解析結果と CAB 名から profile を自動判定
3. profile から template を解決。template が無い場合でも profile が generated template を許可していれば自動生成して継続
4. 監視種別は内部値を保持したまま、Excel 出力時のみ表示名称へ変換する
   `Service -> サービス監視`
   `EventlogWSA / EvntlogWSA -> イベントログ監視`
5. 監視条件も内部値を保持したまま、Excel 出力時のみ表示名称へ変換する
   `5ContYellow -> 5回連続注意`
4. テンプレートの書式・レイアウトだけを使い、監視設定表は CAB 由来データで再構築
5. CAB 名ベースで output 名を解決
6. 同名ファイルが存在する場合は `_001`, `_002` ... を自動付与
7. 設計書 Excel を生成
8. validation を実行

通常実行では既存ファイルを上書きしません。

```text
output/0307_sqlserver2022_windows.xlsx
output/0307_sqlserver2022_windows_001.xlsx
output/0307_sqlserver2022_windows_002.xlsx
```

上書きしたい場合だけ `--overwrite` を指定します。

```bash
.venv/bin/bom-monitor-builder build \
  --input "import/cab/0307_sqlserver2022_windows.cab" \
  --overwrite
```

高度な用途では `cab-excel` と `design-excel` を個別実行できます。

## build コマンド

```bash
.venv/bin/bom-monitor-builder build \
  --input "import/cab/0307_sqlserver2022_windows.cab"
```

主要オプション:

- `--profile`: profile 自動判定を使わず、明示指定した profile を使う
- `--template`: profile 既定 template を上書きする
- `--output`: 完成設計書の出力先を明示指定する
- `--work-dir`: 中間 Excel の作業ディレクトリを固定する
- `--dry-run`: CAB 解析と profile/template 解決だけ行い、完成設計書は出力しない
- `--keep-intermediate`: 生成した中間 Excel を保持する
- `--dump-model`: 共通内部モデル JSON を出力する
- `--validate-only`: build が解決した profile/template を使って既存 output を再検証する
- `--overwrite`: 自動採番せず、解決済み output を上書きする
- `--verbose`: 判定根拠、validation check、各パスを詳細表示する

詳細は [build_command.md](docs/build_command.md) を参照してください。

build 失敗時の調査補助として `build-with-codex` も利用できます。

```bash
.venv/bin/bom-monitor-builder build-with-codex \
  --input "import/cab/0905_ActiveImage Protector 2022 ServerEditon.CAB" \
  --codex-prompt
```

- `--codex-prompt`: エラー分類、Intermediate Excel 要約、profile score 内訳付きの Codex 調査プロンプトを生成する
- `--codex-auto`: `codex exec` を使って非対話で Codex を実行し、修正後に同じ CAB の build を最大 1 回再実行する

調査ログは `output/codex_runs/` 配下に保存されます。

監視設定データについては、テンプレートに元から入っている旧監視値を正解として扱いません。`design-excel` / `build` は managed monitor region を毎回初期化し、CAB から生成した内部モデルだけで監視表を再構築します。
見た目についても、profile の `monitor_table.layout` / `monitor_table.format` と template の style source 行から再適用します。

## 基本フロー

1. CAB を `import/cab/` に配置する
2. まず `build --input <CAB>` を実行する
3. 必要に応じて `--profile` / `--template` / `--dump-model` を追加する
4. 監視種別追加や詳細調整時のみ `cab-excel` と `design-excel` を個別実行する
5. `reference/` と `output/` を比較し、`diff_count=0` を目標に調整する
6. 統合テストと全体 pytest を実行する

## CAB→解析Excel

単一 CAB の例:

```bash
.venv/bin/bom-monitor-builder cab-excel \
  "import/cab/0307_sqlserver2022_windows.cab" \
  --output "input/0307_sqlserver2022_windows.xlsx" \
  --overwrite
```

生成される主なシート:

- `表紙`
- `監視グループ一覧`
- `監視項目一覧`
- `監視項目詳細`
- `XML全項目`
- `解析情報`

## 解析Excel→設計書Excel

```bash
.venv/bin/bom-monitor-builder design-excel \
  --input "input/0307_sqlserver2022_windows.xlsx" \
  --profile "profiles/sqlserver2022_windows.yml" \
  --template "templates/sqlserver2022_windows_design.xlsx" \
  --output "output/sqlserver2022_windows_design.xlsx" \
  --overwrite
```

主要オプション:

- `--template`: プロファイル既定のテンプレートを上書き
- `--dry-run`: 解析とマッピングのみ実施
- `--dump-model`: 共通内部モデル JSON を出力
- `--validate-only`: 既存出力を再検証
- `--overwrite`: 既存出力を上書き

## YAMLプロファイル

`design-excel` / `build` は YAML プロファイルで次を定義します。

- 入力シート候補
- 見出し別名
- 正規化ルール
- 値置換
- 条件付き行マッピング
- 自動判定用 detection ルール
- 出力列マッピング
- 既定 output 名
- 固定セル
- 検証条件
- 機密情報マスク条件

詳細は [profile_specification.md](docs/profile_specification.md) を参照してください。

## 表示変換仕様

内部値は保持し、Excel 設計書へ出力する段階で表示名称へ変換します。CAB/XML、parser、model の値や profile 判定・validation 用データは書き換えません。

### サービス監視の CurrentState

`Monitor Type=Service` かつ `ValueName=CurrentState` の場合に限り、状態値を次の日本語表示へ変換します。

| 内部値 | Excel表示 |
|---:|---|
| 1 | 停止 |
| 2 | 開始中 |
| 3 | 停止中 |
| 4 | 開始 |
| 5 | 再開中 |
| 6 | 一時停止中 |
| 7 | 一時停止 |

条件に一致しない監視の数値や、未知の状態値は元の値のまま表示します。

### ContYellow 条件

`数字ContYellow` と `数字 ContYellow` は、Excel 表示時に `数字回連続注意` へ変換します。数字部分は固定値ではありません。

| 内部値 | Excel表示 |
|---|---|
| `2ContYellow` | `2回連続注意` |
| `3ContYellow` | `3回連続注意` |
| `5 ContYellow` | `5回連続注意` |

未知の条件値は変換せず、そのまま表示します。

### 確認結果

SQL Server 2025 CAB と `standard.cab` から生成した Excel、および Excel 保存後にセル値を読み直す統合テストで表示を確認済みです。SQL Server 2025 の出力では `5ContYellow` が `5回連続注意` となり、`standard.cab` の出力では `2回連続注意` と `3回連続注意` を確認しました。サービス状態の `開始` / `停止` も保存後セル値のテストで確認しています。

最終テスト結果: `131 passed / 0 failed`。

## 新しい監視種別の追加方針

最重要ルール:

- 新しい監視種別を追加する場合、原則としてコア Python を変更しない
- まず `YAMLプロファイル / テンプレートExcel / 統合テスト` で対応する
- YAML だけで対応できない場合、その要件が他監視種別でも利用できる汎用要件かを確認する
- 汎用要件の場合のみコアへ追加する
- 特定監視種別だけに必要な処理をコアへ直接ハードコードしない
- 複雑な固有処理は将来のプラグイン化候補とする

標準手順は [adding_new_monitor_type.md](docs/adding_new_monitor_type.md) を参照してください。

## セキュリティ

取り扱い注意の対象:

- CAB
- 解析 Excel
- reference
- templates
- output
- dump-model JSON
- ログ

既存実装では次を行っています。

- CAB 内バイナリは実行しない
- パストラバーサル拒否
- 数式インジェクション対策
- dump-model への再帰マスク
- CLI 形式の `-user value` / `--password value` などのマスク
- テンプレート固定値を許可セルで限定的に保持

運用注意を含む詳細は [operation_guide.md](docs/operation_guide.md) を参照してください。

## テスト

全体テスト:

```bash
.venv/bin/python -m pytest
```

初期開発完了確認時点の最終結果は `37 passed` です。

## 既存の TemplateData 調査機能

```bash
./scripts/run.sh knowledge inspect --source import/TemplateData
./scripts/run.sh knowledge import --source import/TemplateData --output knowledge --dry-run
./scripts/run.sh knowledge import --source import/TemplateData --output knowledge
```

## Profile selection

Build selects a profile in this order:

1. An explicitly supplied `--profile`
2. Automatic profile detection
3. Generic fallback

When no existing profile matches a CAB, the build continues with the generic standard layout and validates the generated workbook. The generic path keeps monitor settings and ActionItem XML settings profile independent. Action settings are written to a separate `Actions` worksheet when present; a CAB with no actions builds normally.

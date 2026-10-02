# Codex Iteration 02: BOM CAB to Excel 機能のプロジェクト構成作成指示書

## 1. 目的

既存リポジトリ `~/projects/bom-monitor-template-builder` に、BOM for Windows のCABファイルを解析し、Excel形式の設定仕様書を生成する機能を追加する。

本Iterationでは、まだ本格的なCAB解析処理やExcel生成処理を完成させない。
まず、既存プロジェクトを壊さず、後続開発に適したディレクトリ、Pythonパッケージ、設定ファイル、テスト、サンプル配置場所、ドキュメントの骨組みを作成する。

## 2. 前提環境

- OS: Ubuntu 24.04
- 作業ディレクトリ: `~/projects/bom-monitor-template-builder`
- エディター: VS Code Remote SSH
- Python: 3.11以上を想定
- 仮想環境: 既存の `.venv` を使用
- パッケージ管理: 既存の `pyproject.toml`、`requirements.txt`、`requirements-dev.txt` を優先
- Gitリポジトリは既に初期化済み

## 3. 最重要ルール

1. 新しいGitリポジトリを作成しないこと。
2. 既存ファイルを無断で削除、移動、上書きしないこと。
3. 既存のPythonパッケージ構成、命名規則、設定方式を最初に調査すること。
4. 既存構成と本指示書が衝突する場合は、既存構成を優先し、変更理由を報告すること。
5. `.env`、秘密情報、実際の顧客CAB、生成済みExcelをGit管理対象にしないこと。
6. CAB展開時のパストラバーサル対策を将来実装できる構造にすること。
7. GUIは本Iterationの対象外とすること。
8. `TemplateMaker.exe`の逆コンパイルや実行は本Iterationの対象外とすること。

## 4. 作業開始時の調査

最初に次を確認し、結果を短く整理すること。

```bash
pwd
find . -maxdepth 3 -type f | sort
find src -maxdepth 4 -type f | sort 2>/dev/null || true
sed -n '1,240p' pyproject.toml
sed -n '1,240p' README.md
sed -n '1,240p' .gitignore
sed -n '1,240p' requirements.txt
sed -n '1,240p' requirements-dev.txt
```

確認事項:

- 現在のPythonパッケージ名
- `src`レイアウトかフラットレイアウトか
- CLIの実装方式
- 設定ファイルの読込方式
- テストフレームワーク
- Ruff、mypy、pytestなどの設定
- 既存のログ方式
- `import`、`output`、`samples`、`knowledge`の用途

## 5. 推奨ディレクトリ構成

既存構成を尊重しつつ、原則として次の形にする。
Pythonパッケージ名は、既存の正式名称に合わせて読み替えること。
以下では仮に `bom_monitor_template_builder` と表記する。

```text
bom-monitor-template-builder/
├── config/
│   ├── settings.yml
│   ├── software_targets.yml
│   └── cab_to_excel/
│       ├── excel_layout.yml
│       ├── monitor_type_aliases.yml
│       └── xml_field_mappings.yml
│
├── docs/
│   ├── architecture.md
│   ├── development_plan.md
│   ├── requirements/
│   │   ├── Codex_Iteration01_BOM_CAB_to_Excel_Instruction.md
│   │   └── Codex_Iteration02_Project_Structure_Instruction.md
│   └── cab_to_excel/
│       ├── README.md
│       ├── cab_structure.md
│       ├── excel_specification.md
│       └── known_limitations.md
│
├── import/
│   └── cab/
│       └── .gitkeep
│
├── knowledge/
│   └── cab_to_excel/
│       ├── README.md
│       ├── manifest_fields.md
│       ├── group_xml_fields.md
│       └── monitor_xml_fields.md
│
├── logs/
│   └── .gitkeep
│
├── output/
│   └── excel/
│       └── .gitkeep
│
├── samples/
│   └── cab_to_excel/
│       ├── README.md
│       ├── cab/
│       │   └── .gitkeep
│       ├── extracted/
│       │   └── .gitkeep
│       └── expected/
│           └── .gitkeep
│
├── scripts/
│   ├── inspect_cab.py
│   ├── extract_cab.py
│   └── generate_bom_spec.py
│
├── src/
│   └── bom_monitor_template_builder/
│       ├── __init__.py
│       ├── cli.py
│       └── cab_to_excel/
│           ├── __init__.py
│           ├── application/
│           │   ├── __init__.py
│           │   └── generate_specification.py
│           ├── domain/
│           │   ├── __init__.py
│           │   ├── models.py
│           │   ├── enums.py
│           │   └── exceptions.py
│           ├── infrastructure/
│           │   ├── __init__.py
│           │   ├── cab_extractor.py
│           │   ├── manifest_parser.py
│           │   ├── xml_parser.py
│           │   ├── excel_writer.py
│           │   └── yaml_loader.py
│           └── presentation/
│               ├── __init__.py
│               └── cli.py
│
└── tests/
    ├── unit/
    │   └── cab_to_excel/
    │       ├── test_manifest_parser.py
    │       ├── test_xml_parser.py
    │       └── test_models.py
    ├── integration/
    │   └── cab_to_excel/
    │       └── test_generate_specification.py
    └── fixtures/
        └── cab_to_excel/
            ├── minimal_manifest/
            │   └── MANIFEST.MF
            ├── minimal_group/
            │   └── GRP.xml
            └── minimal_monitor/
                └── MON01.xml
```

## 6. 各ディレクトリの役割

### `config/cab_to_excel`

CAB内XMLの項目名とExcel列の対応、監視タイプの表示名、Excelレイアウトなど、コードに直接埋め込みたくない設定を配置する。

### `docs/cab_to_excel`

利用者および開発者向けの設計資料を配置する。

### `import/cab`

手動実行時に入力CABを一時配置する場所とする。
実際のCABは原則Git管理しない。

### `knowledge/cab_to_excel`

調査によって判明したBOM CAB、MANIFEST、GRP.xml、MONxx.xmlの知識を蓄積する。

### `output/excel`

生成したExcel設定仕様書の既定出力先とする。
Excelファイル自体はGit管理しない。

### `samples/cab_to_excel`

公開・共有可能な匿名化サンプルのみ配置する。
実顧客の情報を含むCABは置かない。

### `src/.../cab_to_excel/domain`

BOMテンプレート、監視グループ、監視項目、しきい値、実行設定などのデータモデルを配置する。
外部ライブラリへの依存を極力持たせない。

### `src/.../cab_to_excel/infrastructure`

CAB展開、ファイル読込、XML解析、YAML読込、Excel出力など、外部入出力を担当する。

### `src/.../cab_to_excel/application`

CAB入力からExcel出力までの処理順序を制御するユースケースを配置する。

### `src/.../cab_to_excel/presentation`

CLI引数の受付、終了コード、利用者向けメッセージを担当する。

### `tests`

単体テスト、結合テスト、最小限の匿名化fixtureを分離して配置する。

## 7. 本Iterationで作成するファイルの内容

### 7.1 Pythonファイル

すべてのPythonファイルに、最低限のモジュールドキュメント文字列を付ける。
未実装処理は、曖昧なダミー値を返さず、`NotImplementedError`または明示的な例外にする。

#### `domain/models.py`

最低限、次のdataclassを定義する。

- `BomManifest`
- `MonitorGroup`
- `MonitorItem`
- `ThresholdCondition`
- `ExecutionSetting`
- `BomTemplate`

このIterationでは、後から項目追加しやすい最小構成でよい。
未知のXML要素を保持できるよう、`extra_fields: dict[str, object]`相当を検討する。

#### `domain/enums.py`

最低限、次の列挙型の骨組みを作る。

- 有効・無効状態
- 判定レベル
- 比較演算子

XML上の未知値を失わない設計を優先する。

#### `domain/exceptions.py`

最低限、次の例外を定義する。

- `CabToExcelError`
- `CabExtractionError`
- `ManifestParseError`
- `MonitorXmlParseError`
- `ExcelGenerationError`
- `UnsafeArchivePathError`

#### Infrastructure

各クラスまたは関数の公開インターフェースだけ作成し、詳細実装は後続Iterationに残してよい。

想定インターフェース例:

```python
from pathlib import Path


def extract_cab(cab_path: Path, destination: Path) -> list[Path]:
    """CABを安全に展開し、展開ファイル一覧を返す。"""


def parse_manifest(path: Path) -> BomManifest:
    """MANIFEST.MFを解析する。"""


def parse_group_xml(path: Path) -> MonitorGroup:
    """GRP.xmlを解析する。"""


def parse_monitor_xml(path: Path) -> MonitorItem:
    """MONxx.xmlを解析する。"""


def write_excel(template: BomTemplate, output_path: Path) -> Path:
    """BOM設定仕様書をExcel形式で出力する。"""
```

### 7.2 CLI骨組み

将来、次の形式で実行できる設計にする。

```bash
python -m bom_monitor_template_builder.cab_to_excel.presentation.cli \
  --input import/cab/sample.cab \
  --output output/excel/sample.xlsx
```

または既存CLIに統合できる場合は次を想定する。

```bash
bom-monitor-template-builder cab-to-excel \
  --input import/cab/sample.cab \
  --output output/excel/sample.xlsx
```

本Iterationでは、`--help`が正常表示されるところまででよい。
実際の変換を実行した場合は、未実装であることが明確に分かる終了メッセージと非0終了コードを返す。

### 7.3 設定ファイル

以下のYAMLに、説明コメントと最小限の初期値を入れる。

#### `excel_layout.yml`

想定シート:

- テンプレート基本情報
- 監視グループ
- 監視項目一覧
- 監視項目詳細
- 未解析項目

#### `monitor_type_aliases.yml`

例:

```yaml
Custom2: カスタム監視
```

値が不明な場合は推測で大量登録しない。

#### `xml_field_mappings.yml`

MANIFEST、GRP、MONの既知項目を少数だけ例示し、後から追加できる構造にする。

### 7.4 ドキュメント

#### `docs/cab_to_excel/README.md`

次を記載する。

- 機能の目的
- 現在の実装状況
- 入力と出力
- 開発順序
- セキュリティ上の注意

#### `docs/cab_to_excel/cab_structure.md`

既知のCAB構造を記載する。

```text
MANIFEST.MF
Monitor/
└── GRP01/
    ├── GRP.xml
    ├── MON01.xml
    └── MONxx.xml
```

#### `docs/cab_to_excel/excel_specification.md`

想定シートと主要列の初期案を記載する。

#### `docs/cab_to_excel/known_limitations.md`

以下を明記する。

- 現時点では確認済みCABサンプルが限定的
- 監視種類ごとにXML構造が異なる可能性がある
- アクション、スケジュール、通知、複数グループは追加検証が必要
- `TemplateMaker.exe`の処理を完全再現するものではない

### 7.5 テスト

本Iterationでは、最低限次を実施する。

- dataclassが生成できる
- 独自例外が継承関係を満たす
- CLIの`--help`が成功する
- fixtureの最小MANIFESTを読める、または未実装ならテストを明示的にskipする

テストを偽装して成功させないこと。
未実装部分は `pytest.mark.skip` で理由を明示する。

## 8. `.gitignore`の更新

既存内容を維持し、重複を避けながら必要に応じて次を追加する。

```gitignore
# BOM CAB to Excel local inputs and outputs
/import/cab/*
!/import/cab/.gitkeep
/output/excel/*
!/output/excel/.gitkeep
/logs/*
!/logs/.gitkeep
/samples/cab_to_excel/cab/*
!/samples/cab_to_excel/cab/.gitkeep
/samples/cab_to_excel/extracted/*
!/samples/cab_to_excel/extracted/.gitkeep
/samples/cab_to_excel/expected/*
!/samples/cab_to_excel/expected/.gitkeep

# Temporary extraction directories
/tmp/
*.cab
*.xlsx
```

ただし、リポジトリ内で意図的に管理しているCABやXLSXが既にある場合は、全体除外を安易に追加しない。
より限定したパス指定にする。

## 9. 依存関係

既存依存関係を確認し、必要なものだけ追加する。
候補:

- `openpyxl`
- `PyYAML`
- `defusedxml`

CAB展開は初期段階ではUbuntuの `cabextract` コマンド利用を想定するが、本Iterationで必須インストールにはしない。
READMEに次の候補コマンドを記載する。

```bash
sudo apt update
sudo apt install -y cabextract
```

`subprocess`で外部コマンドを呼ぶ際は、将来必ず引数リスト形式を使い、`shell=True`を使わない設計とする。

## 10. 品質確認

作成後、既存プロジェクトの方式に合わせて可能な範囲で次を実行する。

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
```

設定されていないツールは無理に実行しない。
失敗した場合は、原因と本Iteration由来か既存問題かを区別して報告する。

## 11. Git確認

作業終了時に次を実行する。

```bash
git status --short
git diff --stat
git diff
```

Codex自身でコミット、push、reset、cleanを実行しないこと。

## 12. 完了条件

次をすべて満たしたら完了とする。

1. 既存プロジェクト構成を事前調査している。
2. CAB→Excel機能用のディレクトリ構成が作成されている。
3. Pythonパッケージの骨組みがimport可能である。
4. CLIの`--help`が表示できる。
5. 設定YAMLの初期ファイルが存在する。
6. CAB構造、Excel仕様、既知制約の文書が存在する。
7. テストの骨組みが存在し、虚偽の成功をさせていない。
8. 入力CAB、生成Excel、ログがGit管理されない設定になっている。
9. 既存機能を壊していない。
10. 変更ファイル一覧、テスト結果、未実装事項を最終報告している。

## 13. 最終報告形式

作業後、次の順番で報告する。

1. 調査した既存構成
2. 採用したディレクトリ構成
3. 新規作成ファイル
4. 変更した既存ファイル
5. 実行したテストと結果
6. 未実装事項
7. 次Iterationの推奨作業


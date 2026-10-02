# BOM CAB設定仕様書生成ツール 開発計画

## 目的

- `docs/Codex_Iteration01_BOM_CAB_to_Excel_Instruction.md` を最優先要件として、BOM監視設定CABまたは展開済みフォルダーからExcel設定仕様書を生成するPython CLIを実装する。

## 現状確認

- 既存リポジトリは TemplateData 調査機能が中心であり、CAB設定仕様書生成機能は未実装。
- `templatemaker/temp` に相当する展開済みサンプルは現時点で未配置。
- `import/TemplateData` には多数のCABサンプルが存在する。
- Linux環境には `7zz`、`7z`、`cabextract` が未導入。
- 既存の Iteration01 解析コードには CAB ヘッダーと内部ファイルテーブルを読む処理がある。

## 実装方針

1. 既存コードを壊さないよう、CAB→Excel機能は `src/bom_monitor_builder/cab_excel/` 配下へ新設する。
2. まず展開済みフォルダー入力を完成させ、MANIFEST解析、XML解析、データモデル、Excel出力、CLI、テストを整える。
3. その後、CAB抽出アダプターを追加する。
4. Linux上で外部コマンドがない場合でも、圧縮方式 `NONE` のCABは自前抽出できるようにする。
5. 不明項目は推測せず、元の要素名・元文字列・型変換後の値を保持する。

## 実装ステップ

### Step 1: 基盤

- パッケージ構成、例外、ロギング、共通ユーティリティを追加
- 既存CLIへ新コマンド群を統合
- `pyproject.toml`、README、テスト設定を要件に合わせて更新

### Step 2: 解析モデル

- `ManifestInfo`
- `MonitorGroup`
- `MonitorItem`
- `ParsedCab`
- `ParseWarning`
- `OptionsInfo`
- Excel出力用の派生ビュー

### Step 3: 展開済みフォルダー入力

- MANIFESTパーサー実装
- XMLパーサー実装
- 型変換、名前空間除去、未知項目保持
- 比較演算子と監視間隔の表示変換
- Options文字列の抽出

### Step 4: Excel生成

- 6シート構成の実装
- 書式、固定行、フィルター、印刷設定、列幅調整
- 数式インジェクション対策
- openpyxlで再オープンできることを検証

### Step 5: CAB抽出

- 抽象 `CabExtractor` 実装
- 外部コマンド検出
- `NONE` 圧縮向けの自前抽出
- MSZIPなど外部コマンドが必要な場合の明確なエラー
- 一時ディレクトリ管理とパストラバーサル検証

### Step 6: テスト

- MANIFEST、XML、Options、Formatter、Excelの単体テスト
- 展開済みサンプルの結合テスト
- `NONE` 圧縮CABの結合テスト
- 必要なら指示書期待値を満たすフィクスチャを追加

### Step 7: 文書更新

- `docs/architecture.md` に設計判断を記録
- `docs/supported_monitor_types.md` を追加
- READMEへ実行方法、lint、型チェック、テスト、CAB展開要件を記載

## リスクと対策

- 展開済みサンプル不足:
  指示書期待値に一致するCABまたは既存資料から対象を特定し、必要ならテストフィクスチャ化する。
- Linuxで外部展開ツール未導入:
  `NONE` 圧縮は自前抽出で対応し、MSZIPは外部ツール必須として明示する。
- XML項目の意味不明:
  専用列に割り当てず `XML全項目` と生値保持で安全に対応する。

## 完了判定

- 展開済みフォルダーまたはCAB入力からExcel生成可能
- 指定6シートを出力
- サンプル1グループ4監視項目の検証成功
- `pytest`、`ruff`、`mypy` を実行し、結果を確認

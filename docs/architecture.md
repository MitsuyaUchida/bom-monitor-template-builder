# Architecture

## 目的

- BOM for Windows の監視設定 CAB または展開済みフォルダーから、Excel 設定仕様書を生成する。
- `TemplateMaker.exe` や同梱 DLL は実行せず、`MANIFEST.MF` と XML を直接解析する。

## モジュール構成

- `bom_monitor_builder.cab_excel.cli`
  CLI と全体オーケストレーション。
- `bom_monitor_builder.cab_excel.extractor`
  CAB 抽出。解析処理と OS 依存処理を分離する。
- `bom_monitor_builder.cab_excel.manifest`
  `MANIFEST.MF` の文字コード判定と key/value 解析。
- `bom_monitor_builder.cab_excel.xml_parser`
  監視グループ・監視項目 XML の解析。
- `bom_monitor_builder.cab_excel.options_parser`
  `Options` 文字列のベストエフォート抽出。
- `bom_monitor_builder.cab_excel.formatter`
  比較演算子、監視間隔、有効状態、Excel 安全化の表示変換。
- `bom_monitor_builder.cab_excel.excel_writer`
  openpyxl による 6 シート構成の出力。
- `bom_monitor_builder.cab_excel.models`
  dataclass ベースの共通モデル。

## 処理フロー

1. CLI が入力を受け取り、単一 CAB、CAB フォルダー、展開済みフォルダーを判定する。
2. CAB 入力時は `CabExtractor` で一時ディレクトリへ展開する。
3. `MANIFEST.MF` を解析する。
4. `Monitor/GRPxx/*.xml` を走査し、`MonitorGroup` と `MonitorItem` を構築する。
5. 既知項目を Excel 用に整形しつつ、元の XML 全項目も保持する。
6. openpyxl で設定仕様書を生成し保存する。

## CAB 抽出方針

- 初版では Python 実装で `NONE` と `MSZIP` を扱う。
- それ以外の圧縮形式、または Python 抽出に失敗した場合は外部コマンドへフォールバックする。
- 検出順は概ね指示書の優先順位に合わせるが、実装上は Python 抽出を最優先にして Linux/Windows 差異を減らしている。
- 展開時は相対パス正規化を行い、絶対パスや `..` を拒否する。

## データ保持方針

- 既知項目は型変換後の値を保持する。
- 同時に、すべての XML 要素について元の要素名と元文字列を保持する。
- 意味不明の項目は推測しない。`XML全項目` シートに必ず残す。

## Excel 出力方針

- シート構成は `表紙`、`監視グループ一覧`、`監視項目一覧`、`監視項目詳細`、`XML全項目`、`解析情報`。
- 一覧シートは固定行とオートフィルターを設定する。
- 長文は折り返し、列幅は最大 60 を上限にする。
- 数式インジェクション対策として `=`, `+`, `-`, `@` で始まる文字列は先頭に `'` を付けて出力する。

## エラー処理

- 入力不正、抽出失敗、解析失敗、Excel 保存失敗を例外で分離する。
- 個別 XML の解析失敗は可能な範囲で継続し、警告として `解析情報` に記録する。

## 初版時点の判断

- 指示書で参照されている `templatemaker/temp` はリポジトリ内に存在しなかった。
- そのため、自動テスト用には指示書の期待値に整合する展開済みフィクスチャ `tests/fixtures/sample_extracted/` を追加した。
- 一方で、実在の CAB `import/TemplateData/0002_Windows 基本/0103_ハードディスク負荷状況.cab` を使う抽出テストも追加し、再現フィクスチャのみに依存しないようにした。

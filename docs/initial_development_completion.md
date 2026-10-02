# Initial Development Completion

## 目的

本プロジェクトの目的は、BOM 監視設定の実ファイルを安全かつ再利用可能な形で扱い、次の 2 段階を標準化することです。

1. BOM 監視設定 CAB を解析して、人が確認しやすい解析 Excel を生成する
2. 解析 Excel を共通内部モデルへ読み込み、YAML プロファイルとテンプレート Excel を使って社内向け監視設計書 Excel を生成する

初期開発では、新しい監視種別を追加するたびに Python コアへ固有処理を埋め込む方式ではなく、YAML プロファイルとテンプレート Excel を中心に拡張できる基盤を整備することを主目的としました。

## 初期開発の対象範囲

初期開発の対象範囲は次のとおりです。

- `cab-excel` CLI の実装
- `design-excel` CLI の実装
- 共通内部モデル
- YAML プロファイル方式
- テンプレート Excel 方式
- `--dry-run`
- `--dump-model`
- `--validate-only`
- 機密情報マスク
- 条件付き行マッピング
- 既存テンプレート行再利用
- 詳細シートの複合キー結合
- 実ファイルを使った監視種別検証
- pytest による回帰確認

## システム全体構成

主要ディレクトリは次のとおりです。

```text
import/cab/      CAB入力
input/           cab-excel の解析Excel出力
reference/       人が作成した正解設計書
templates/       design-excel が使う生成用テンプレート
profiles/        監視種別ごとの YAML プロファイル
output/          生成された設計書と dump-model JSON
tests/           統合テスト・単体テスト
docs/            仕様、運用、完了記録
src/             実装本体
```

## 処理フロー

```text
CAB
  ↓
cab-excel
  ↓
解析Excel
  ↓
design-excel parser
  ↓
共通内部モデル
  ↓
design-excel mapper
  ↓
レンダリング計画
  ↓
design-excel writer
  ↓
設計書Excel
  ↓
design-excel validator
  ↓
検証結果
```

## `cab-excel` の役割

`cab-excel` は、BOM 監視設定 CAB または展開済みフォルダーを解析し、確認用の解析 Excel を生成します。

主な役割:

- CAB 展開
- `MANIFEST.MF` 解析
- `Monitor/*/*.xml` 解析
- 監視グループ一覧作成
- 監視項目一覧作成
- 監視項目詳細作成
- XML 全項目一覧化
- 解析情報記録

生成される主なシート:

- `表紙`
- `監視グループ一覧`
- `監視項目一覧`
- `監視項目詳細`
- `XML全項目`
- `解析情報`

## `design-excel` の役割

`design-excel` は、`cab-excel` が生成した解析 Excel を読み込み、YAML プロファイルとテンプレート Excel を使って完成形の監視設計書を生成します。

主な役割:

- 解析 Excel からグループ・監視項目・詳細情報を抽出
- 共通内部モデルを構築
- YAML プロファイルに従って値変換
- テンプレートへ表形式で書き込み
- 出力結果の検証
- dump-model JSON 出力

## YAMLプロファイル方式

初期開発では、監視種別固有の差分を原則 YAML へ外出しする方式を採用しました。

YAML で定義する主な内容:

- 入力シート名候補
- 見出し別名
- 詳細シート候補
- 結合キー
- 既定値
- 値置換
- 正規化ルール
- 条件付き行マッピング
- 出力列マッピング
- 固定セル
- 検証条件
- 機密情報マスク条件
- テンプレート固定平文の許可セル

この方式により、SQL Server 2022 のような新規監視種別でも、新規の SQL Server 専用 Python 実装を作らずに対応できました。

## テンプレートExcel方式

完成形に近い設計書を `reference/` に配置し、それを `templates/` にコピーして生成用テンプレートとして扱う方式を採用しました。

この方式の利点:

- 既存の行高、列幅、結合セル、非表示シート、印刷設定を保持できる
- 人が作った完成形レイアウトをそのまま基準にできる
- 監視種別追加時の調整点を YAML とテンプレートに寄せられる

## 共通内部モデル

内部モデルの基本形式は次のとおりです。

```json
{
  "groups": [],
  "monitors": [],
  "metadata": {},
  "extensions": {}
}
```

設計方針:

- 共通項目は `groups` / `monitors` に格納
- 監視種別固有の詳細は `extensions.<profile_id>` に隔離
- 入力由来の生値を無制限に露出しない
- `dump-model` では機密情報を再帰マスクする

## 主要な汎用機能

初期開発で整備し、複数監視種別で利用している汎用機能は次のとおりです。

- CAB の Python 展開と外部展開ツールのフォールバック
- 見出し別名ベースの入力解析
- 詳細シートとの結合
- `group_id + monitor_id` を前提にした複合キー対応
- 値置換
- 正規化関数
- 条件付き行マッピング
- 既存テンプレート行再利用
- テンプレート固定セル出力
- 出力検証
- dump-model の再帰マスク
- `-user value` / `--password value` 等の機密マスク

## 機密情報保護

次のファイル群には認証情報が含まれる可能性があるため、取り扱いに注意する設計と運用を採用しました。

- CAB
- 解析 Excel
- reference
- templates
- output
- dump-model JSON
- ログ

主な保護内容:

- 機密候補語に基づく文字列マスク
- `-user value`
- `-user=value`
- `--password value`
- `--password=value`
- `-pw:secret`
- dump-model JSON の再帰マスク
- テンプレート固定の平文を許可セルで限定管理

## 検証機能

`design-excel --validate-only` は、少なくとも次を検証します。

- sheet order
- sheet visibility
- template formatting
- input workbook readable
- mapped values
- secret masking

## 実ファイル検証結果

### AWSコスト監視

- 実変換成功
- 既存回帰成功
- 実行時の `monitor_count=1`
- 実行時の `group_count=1`
- `sheet order / sheet visibility / template formatting / mapped values / secret masking` 成功

### Arcserve UDP 9.0

- グループ数: `1`
- 監視件数: `11`
- 主な監視種別: `Service / EventlogWSA`
- 実変換成功
- `reference/ArcserveUDP9設計書.xlsx` との差分: `diff_count=0`

### SQL Server 2022（Windows版）

- グループ数: `3`
- 監視件数: `39`
- 種別内訳:
  - `Service=5`
  - `EventlogWSA=14`
  - `Perf=20`
- 実変換成功
- `reference/sqlserver2022_windows_design.xlsx` との差分: `diff_count=0`
- SQL Server 対応のための新規コア変更: なし

### Hyper-V / Apex One

- グループ数: `6`
- 監視件数: `31`
- 実入力解析成功
- 複合キーによる詳細結合成功
- 完成形テンプレートがないため、完成設計書との実比較は未実施

## pytest の最終結果

初期開発完了記録作成時点で、全体テストは次の結果でした。

```text
37 passed
```

## 既知の制限事項

- 監視種別ごとの表示調整が多い場合、YAML の `row_rules` が長くなりやすい
- 完成形テンプレートがない監視種別では、設計書の reference 比較まで実施できない
- 現時点では許可制プラグイン機構は未実装
- 条件付き書式や入力規則を新規生成する機能は持たず、テンプレート保持が前提

## プラグインの現状

- プロファイル上の `plugins` は予約枠
- 初期開発完了時点では未使用
- 既存監視種別はすべて YAML とテンプレートで対応済み

## 初期開発完了の判定根拠

次を満たしたため、初期開発を完了扱いとします。

- CAB 解析機能が実装済み
- 汎用 `design-excel` 変換機能が実装済み
- YAML プロファイル方式が実装済み
- テンプレート Excel 方式が実装済み
- dump-model、dry-run、validate-only が実装済み
- 機密情報マスクが実装済み
- AWS、Arcserve UDP 9.0、SQL Server 2022（Windows版）で実設計書生成を検証済み
- Arcserve UDP 9.0 と SQL Server 2022（Windows版）で `diff_count=0`
- Hyper-V / Apex One で実入力解析と詳細結合を検証済み
- 全 pytest が成功

## 今後の運用方針

- 新しい監視種別を追加する場合、原則としてコア Python を変更しない
- まず `YAML プロファイル / テンプレート Excel / 統合テスト` で対応する
- YAML だけで対応できない場合、その要件が汎用要件かを確認する
- 汎用要件の場合のみコアへ追加する
- 特定監視種別だけに必要な処理をコアへ直接ハードコードしない
- 複雑な固有処理は将来のプラグイン候補として整理する

運用手順の詳細は [operation_guide.md](operation_guide.md) を参照してください。

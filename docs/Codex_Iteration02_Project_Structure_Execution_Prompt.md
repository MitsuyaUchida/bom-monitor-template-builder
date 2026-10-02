# Codex実行指示: BOM CAB to Excel プロジェクト構成作成

Ubuntu上の既存リポジトリで作業してください。

作業対象:

```text
~/projects/bom-monitor-template-builder
```

最初に次の指示書を必ず全文確認してください。

```text
docs/requirements/Codex_Iteration02_Project_Structure_Instruction.md
```

## 実行指示

1. `~/projects/bom-monitor-template-builder` に移動してください。
2. 現在のディレクトリ構成、`pyproject.toml`、README、既存Pythonパッケージ、テスト、設定ファイル、`.gitignore`を調査してください。
3. 指示書の推奨構成をそのまま機械的に作るのではなく、既存プロジェクトの命名規則と構成に合わせて調整してください。
4. 既存ファイルを削除、移動、破壊しないでください。
5. BOM CABからExcel設定仕様書を生成する機能のために、次を作成してください。
   - Pythonパッケージの骨組み
   - domain、application、infrastructure、presentationの責務分離
   - 設定YAMLの骨組み
   - CAB構造とExcel仕様のドキュメント
   - CLIの骨組み
   - 単体テストと結合テストの骨組み
   - 入力、出力、サンプル、fixture用ディレクトリ
6. 本Iterationでは、CAB解析やExcel生成の完全実装を行わないでください。
7. 未実装処理は曖昧な仮実装で成功させず、明示的な例外またはskip理由を使用してください。
8. 既存の依存管理方式に従い、必要最小限の依存だけを追加してください。
9. 作成後、pytest、ruff、mypyなど、既存プロジェクトで利用可能な品質確認を実行してください。
10. `git status`と`git diff`を確認してください。
11. コミット、push、reset、cleanは実行しないでください。

## 重要な設計方針

CAB解析結果を直接Excelセルへ書き込む密結合にはしないでください。
必ず次の流れを想定した構造にしてください。

```text
CAB
  ↓
安全な展開
  ↓
MANIFEST/XML解析
  ↓
Pythonドメインモデル
  ↓
Excel出力
```

将来、同じドメインモデルからHTML、Markdown、JSON、YAMLも出力できるようにしてください。

## 作業停止条件

次の場合は推測で大規模変更せず、状況を報告してください。

- 既存パッケージ構成が指示書と大きく異なる
- 同名の機能やディレクトリが既に存在する
- 既存テストが作業前から失敗している
- `pyproject.toml`の変更が既存CLIへ影響する
- 実顧客データらしいCABや設定ファイルが見つかった

## 最終報告

最後に次を簡潔に報告してください。

- 既存構成の調査結果
- 実際に採用した構成
- 作成・変更したファイル一覧
- テスト結果
- 未実装部分
- 次に実施すべきIteration


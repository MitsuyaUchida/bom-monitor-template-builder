# Iteration01 Generation Requirements

## CAB Generation

- monitoring_target_name
- category
- cab_file_name
- internal_file_names
- compression_format
- html_pair_path
- internal_file_categories

## HTML Generation

- title
- product_name
- description
- monitor_items
- services
- event_logs
- event_ids
- performance_counters
- thresholds
- monitoring_intervals
- related_cab
- image_references

## Sample Comparison

| Sample | HTML | CAB | Monitor items | Services | Event logs | Perf counters |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Windows標準 | 0000_標準構成テンプレート/0101_Windows システム監視 Basic.htm | 0101_Windows システム監視 Basic.cab | 0 | 0 | 0 | 0 |
| DNS | 0003_Windows オプション/0201_DNS Server.htm | 0201_DNS Server.cab | 3 | 1 | 2 | 0 |
| IIS | 0007_Web サーバー/0104_Internet Information Services 10.0.htm | 0104_Internet Information Services 10.0.CAB | 11 | 5 | 1 | 0 |
| SQL Server | 0005_データベース サーバー/0201_[オプション] SQL Server.htm | 0201_[オプション] SQL Server.cab | 0 | 0 | 0 | 0 |
| Hyper-V | 0001_レポートテンプレート/0106_Hyper-Vレポート用.htm | 0106_Hyper-Vレポート用.CAB | 0 | 0 | 0 | 0 |
| Arcserve | 0001_レポートテンプレート/0103_Arcserve UDPv6_6.5_7_8ログ取得レポート用.htm | 0103_Arcserve UDPv6_6.5_7_8ログ取得レポート用.cab | 0 | 0 | 0 | 0 |

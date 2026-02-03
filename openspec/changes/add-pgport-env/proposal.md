# Change: 将 PGPORT 加入环境变量输出

## Why
当前 `pg env` / `pg use` 生成的环境变量包含 `PGHOME`、`PGDATA`、`PG_CONFIG` 等，但缺少 `PGPORT`。在本仓库管理多个实例（不同 variant/version/profile）时，`psql`/`createdb`/`pg_isready` 等客户端若未显式指定端口，往往会默认使用 5432，从而容易连到错误的实例。

将 `PGPORT` 一并导出可以让常用客户端默认连接到“当前激活实例”的端口，减少误操作。

## What Changes
- 扩展 `pgfleet.json` 配置：支持为实例/profile 配置端口。
  - `instances.<name>.port`（实例级默认端口，可选）
  - `instances.<name>.profiles.<profile>.port`（profile 级覆盖，可选）
- `pg env` 与 `pg use` 生成的环境变量中：当端口已配置时，额外输出 `export PGPORT=<port>`。
- `pg info` 输出中增加 `port=<port>` 便于快速确认。

## Impact
- Affected specs: `pgdev-env`
- Affected code:
  - `bin/pg`: `resolve_instance()`（解析 port 与优先级）、`env_lines()`（追加 PGPORT）、`cmd_info()`（展示 port）
- Affected docs:
  - `README.md`（增加端口字段说明与示例）
  - `pgfleet.json`（示例更新）

## Compatibility
- 向后兼容：未配置 `port` 的现有 `pgfleet.json` 行为保持不变（不导出 `PGPORT`）。
- 非破坏性变更：新增字段均为可选。

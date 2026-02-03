## 1. Implementation
- [x] 在 `pgfleet.json` 中支持可选字段：`instances.<name>.port` 与 `instances.<name>.profiles.<profile>.port`。
- [x] 在 `bin/pg` 的 `resolve_instance()` 中解析并返回 `port`（优先级：profile.port > instance.port > unset）。
- [x] 在 `bin/pg` 的 `env_lines()` 中：当 `port` 存在时追加 `export PGPORT=<port>`。
- [x] 在 `bin/pg` 的 `cmd_info()` 中输出 `port=<port>`。
- [x] 更新 `README.md` 与 `pgfleet.json` 示例，说明端口字段与优先级。

## 2. Validation
- [x] 手工验证：配置 profile.port 后，`pg env <name> <profile>` 输出包含 `export PGPORT=...`。
- [x] 手工验证：只配置 instance.port 时同样生效。
- [x] 手工验证：未配置 port 时输出不包含 PGPORT，且命令正常工作。

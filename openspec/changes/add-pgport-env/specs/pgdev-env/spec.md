## ADDED Requirements

### Requirement: Export PGPORT when configured
当用户通过 `pg env` 或 `pg use` 选择某个实例/profile 时，系统 SHALL 在生成的环境变量中包含 `PGPORT`（仅当端口已配置）。

#### Scenario: Profile-level port overrides instance-level port
- **GIVEN** `instances.<name>.port` 已配置为 `5432`
- **AND** `instances.<name>.profiles.<profile>.port` 已配置为 `55432`
- **WHEN** 执行 `pg env <name> <profile>`
- **THEN** 输出包含 `export PGPORT=55432`

#### Scenario: Instance-level port is used by default
- **GIVEN** `instances.<name>.port` 已配置为 `55432`
- **AND** `instances.<name>.profiles.<profile>.port` 未配置
- **WHEN** 执行 `pg use <name> <profile>` 并生成 `active.env`
- **THEN** `active.env` 包含 `export PGPORT=55432`

#### Scenario: Port not configured
- **GIVEN** `instances.<name>.port` 未配置
- **AND** `instances.<name>.profiles.<profile>.port` 未配置
- **WHEN** 执行 `pg env <name> <profile>`
- **THEN** 输出 MUST NOT 包含 `export PGPORT=` 行

### Requirement: Port precedence
系统 SHALL 按如下优先级解析端口：`profiles.<profile>.port` > `instances.<name>.port`。

#### Scenario: Precedence is applied
- **GIVEN** 同时配置了 instance.port 与 profile.port
- **WHEN** 生成环境变量
- **THEN** 选择 profile.port

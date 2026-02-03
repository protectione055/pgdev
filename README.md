# pgdev

用于管理多个 PostgreSQL 源码/构建/安装/数据目录的轻量工具集。

## 目录结构

- src/：源码仓库（只作为规范建议，实际仓库可位于任意路径）
- build/：构建目录（profile 隔离）
- install/：安装前缀（profile 隔离）
- data/：数据目录（profile 隔离）
- logs/：日志目录（profile 隔离）
- bin/：管理脚本

## 配置

编辑 pgfleet.json，为每个实例配置 repo、版本、构建选项等。

### 端口（可选）

支持在配置中为实例/profile 指定端口：

- `instances.<name>.port`：实例级默认端口（可选）
- `instances.<name>.profiles.<profile>.port`：profile 级端口覆盖（可选）

端口优先级：`profile.port` > `instance.port`。

## 常用命令

```bash
# 列出所有实例
pg list

# 生成并切换环境（输出 source 命令）
pg use pg19 debug

# 构建/安装
pg build pg19 debug
pg install pg19 debug

# 查看路径信息
pg info babelfish17 release

# 查看仓库状态
pg status babelfish17
```

## 环境切换

执行 `pg use` 后会生成 active.env：

```bash
source /SSD/00/zzm/projects/PostgreSQL/pgdev/active.env
```

当配置了端口（见上文）时，`active.env` / `pg env` 输出会额外包含 `export PGPORT=<port>`，使 `psql` 等客户端默认连接到当前实例端口。

切换环境后可以直接安装扩展（例如在源码树中执行）：

```bash
make -C ${PGBUILD}/contrib/postgres_fdw install
```

以上命令会使用 `PG_CONFIG`/`PGXS` 指向的安装前缀，确保扩展安装到 `PGHOME`。若需要在源码树中执行，也可使用：

```bash
make -C contrib/postgres_fdw USE_PGXS=1 install
```

## 备注

- 默认 profile 为 debug（若存在）。
- 构建采用 out-of-source（build 目录）方式，避免污染源码树。
- `pg build` 在安装目录缺少 `pg_config` 时会自动执行一次 install，以确保扩展/插件能安装到正确目录。

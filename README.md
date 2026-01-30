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

## 备注

- 默认 profile 为 debug（若存在）。
- 构建采用 out-of-source（build 目录）方式，避免污染源码树。

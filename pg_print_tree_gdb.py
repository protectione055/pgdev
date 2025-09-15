# -*- coding: utf-8 -*-
"""
pg_node_printer.py — GDB Python 扩展

适用版本：PostgreSQL 17（其他版本大体兼容）
功能：
  1) pgnode  EXPR            -> 调用后端 nodeToString()，快速打印任意 Node* 的树结构（推荐）
  2) pgnode  EXPR --depth N  -> 限制展开深度
  3) pgnode  EXPR --safe     -> 安全模式（不调用被调试进程函数），目前支持 List / Bitmapset 等常见容器的结构化打印
  4) pgnode  EXPR --native   -> 强制使用 nodeToString（默认即为此模式）
  5) pgnode  EXPR --pretty   -> 对 nodeToString 输出进行缩进美化，更易读

注意：
  - “原生/快速模式”会通过 GDB 调用被调试进程的 nodeToString() 并读取返回的 C 字符串。
  - “安全模式”完全在 GDB 侧读取内存，不执行被调试进程代码。

示例：
  (gdb) pgnode parse
  (gdb) pgnode plannedstmt --depth 2 --pretty
  (gdb) pgnode query --safe
"""

from __future__ import annotations
import gdb
import re

# ------------------------------------------------------------
# 工具函数
# ------------------------------------------------------------

def _value_to_address(val: gdb.Value) -> int:
    try:
        v = gdb.parse_and_eval(str(val)) if not isinstance(val, gdb.Value) else val
        if v.type.code == gdb.TYPE_CODE_PTR:
            return int(v)
        if v.type.code in (gdb.TYPE_CODE_INT, gdb.TYPE_CODE_LONG, gdb.TYPE_CODE_ENUM):
            return int(v)
        return int(v.address)
    except Exception:
        return int(val)


def _gdb_read_c_string(cstr_val: gdb.Value) -> str:
    try:
        if int(cstr_val) == 0:
            return "<NULL>"
        return cstr_val.string()
    except Exception as e:
        return f"<string read error: {e}>"


# ------------------------------------------------------------
# 原生/快速模式：调用 nodeToString()
# ------------------------------------------------------------

def _node_to_string(expr: str) -> str:
    try:
        gdb.lookup_global_symbol("nodeToString")
    except Exception:
        raise gdb.GdbError("找不到符号 nodeToString。请确保已带调试符号并在 backend/nodes/outfuncs.c 链入。")

    call_expr = f"(char*)nodeToString((void*)({expr}))"
    cstr = gdb.parse_and_eval(call_expr)
    return _gdb_read_c_string(cstr)


def _pretty_format(s: str, max_depth: int | None = None) -> str:
    """对 nodeToString 输出做缩进美化，并支持限深折叠"""
    out = []
    depth = 0
    token = ""
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == '(':
            if token.strip():
                out.append("  " * depth + token.strip())
                token = ""
            if max_depth is not None and depth >= max_depth:
                out.append("  " * depth + "{...}")
                # 跳过直到匹配的闭括号
                skip = 1
                i += 1
                while i < len(s) and skip > 0:
                    if s[i] == '(':
                        skip += 1
                    elif s[i] == ')':
                        skip -= 1
                    i += 1
                continue
            out.append("  " * depth + "(")
            depth += 1
        elif ch == ')':
            if token.strip():
                out.append("  " * depth + token.strip())
                token = ""
            depth = max(0, depth - 1)
            out.append("  " * depth + ")")
        elif ch in (' ', '\n', '\t'):
            if token.strip():
                out.append("  " * depth + token.strip())
                token = ""
        else:
            token += ch
        i += 1
    return "\n".join(out)


# ------------------------------------------------------------
# 安全模式：结构化读取常见容器
# ------------------------------------------------------------

class SafePrinter:
    def __init__(self, max_items: int = 32):
        self.max_items = max_items

    def is_null(self, val: gdb.Value) -> bool:
        try:
            return int(val) == 0
        except Exception:
            return False

    def try_as_list(self, expr: str) -> str | None:
        try:
            lval = gdb.parse_and_eval(f"({expr})")
            if lval.type.code == gdb.TYPE_CODE_PTR:
                if int(lval) == 0:
                    return "List*: NULL"
                l = lval.dereference()
            else:
                l = lval
            length = int(l["length"]) if "length" in [f.name for f in l.type.fields()] else -1
            head = l["head"]
            out = [f"List(length={length})"]
            cell = head
            idx = 0
            while not self.is_null(cell) and idx < self.max_items:
                data = cell["data"]
                if "ptr_value" in [f.name for f in data.type.fields()]:
                    val = int(data["ptr_value"])
                    out.append(f"  [{idx}] ptr=0x{val:x}")
                elif "int_value" in [f.name for f in data.type.fields()]:
                    out.append(f"  [{idx}] int={int(data['int_value'])}")
                else:
                    out.append(f"  [{idx}] <unknown cell data>")
                cell = cell["next"]
                idx += 1
            if idx == self.max_items:
                out.append("  ... (truncated)")
            return "\n".join(out)
        except Exception:
            return None

    def try_as_bitmapset(self, expr: str) -> str | None:
        try:
            bset = gdb.parse_and_eval(f"({expr})")
            if bset.type.code == gdb.TYPE_CODE_PTR:
                if int(bset) == 0:
                    return "Bitmapset*: NULL"
                b = bset.dereference()
            else:
                b = bset
            nwords = int(b["nwords"])
            words = b["words"]
            bits = []
            for wi in range(nwords):
                w = int((words + wi).dereference())
                bit = 0
                while w:
                    if w & 1:
                        bits.append(wi * (8 * (words.type.target().sizeof)) + bit)
                    w >>= 1
                    bit += 1
            return f"Bitmapset{{{', '.join(map(str, bits))}}}"
        except Exception:
            return None

    def print_any(self, expr: str) -> str:
        s = self.try_as_list(expr)
        if s:
            return s
        s = self.try_as_bitmapset(expr)
        if s:
            return s
        try:
            v = gdb.parse_and_eval(f"({expr})")
            if v.type.code == gdb.TYPE_CODE_PTR and int(v) != 0:
                tag_val = (v.dereference())["type"]
                tag_int = int(tag_val)
                tag_name = str(tag_val)
                addr = int(v)
                return f"Node* @0x{addr:x}, nodeTag={tag_int} ({tag_name})"
                # tag = int((v.dereference())["type"]) if "type" in [f.name for f in v.dereference().type.fields()] else None
                # addr = int(v)
                # return f"Node* @0x{addr:x}, nodeTag={tag} (未知类型，建议使用 --native)"
        except Exception:
            pass
        return "<无法识别的对象，建议使用 --native 模式>"


# ------------------------------------------------------------
# GDB 命令实现：pgnode
# ------------------------------------------------------------

class PgNodeCommand(gdb.Command):
    def __init__(self):
        super(PgNodeCommand, self).__init__("pgnode", gdb.COMMAND_DATA)

    def invoke(self, arg, from_tty):
        argv = gdb.string_to_argv(arg)
        if not argv:
            raise gdb.GdbError("用法：pgnode EXPR [--depth N] [--safe|--native|--pretty]")

        mode_native = True
        pretty = False
        max_depth = None
        expr_parts = []
        i = 0
        while i < len(argv):
            a = argv[i]
            if a == "--safe":
                mode_native = False
                i += 1
                continue
            if a == "--native":
                mode_native = True
                i += 1
                continue
            if a == "--pretty":
                pretty = True
                i += 1
                continue
            if a == "--depth":
                if i + 1 >= len(argv):
                    raise gdb.GdbError("--depth 需要一个整数参数")
                try:
                    max_depth = int(argv[i + 1])
                except Exception:
                    raise gdb.GdbError("--depth 参数应为整数")
                i += 2
                continue
            expr_parts.append(a)
            i += 1

        if not expr_parts:
            raise gdb.GdbError("缺少 EXPR 参数")
        expr = " ".join(expr_parts)

        try:
            if mode_native:
                raw = _node_to_string(expr)
                if pretty:
                    out = _pretty_format(raw, max_depth=max_depth)
                else:
                    out = raw
            else:
                out = SafePrinter().print_any(expr)
            print(out)
        except gdb.error as ge:
            raise
        except Exception as e:
            raise gdb.GdbError(f"pgnode 失败：{e}")


PgNodeCommand()

class PgN(gdb.Command):
    def __init__(self):
        super(PgN, self).__init__("pn", gdb.COMMAND_DATA)
    def invoke(self, arg, from_tty):
        gdb.execute("pgnode " + arg)
PgN()

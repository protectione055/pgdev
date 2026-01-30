# pg_node_json.py
import gdb
import json
import traceback

# NodeTag 枚举
NODE_TAG_ENUM = gdb.lookup_type("NodeTag")

# 所有 NodeTag 值 -> 类型名 的映射
NODE_TAG_MAP = {}

# 初始化 NodeTag 映射表
def init_node_tag_map():
    global NODE_TAG_MAP
    tag_enum = NODE_TAG_ENUM
    for field in tag_enum.fields():
        name = field.name
        if name.startswith("T_"):
            NODE_TAG_MAP[field.enumval] = name[2:]  # 去掉前缀 T_
init_node_tag_map()

# 判断是否是 Node 派生类
def is_node_type(typ):
    while typ.code == gdb.TYPE_CODE_PTR:
        typ = typ.target()
    try:
        return typ.tag and ("struct" in str(typ)) and "Node" in str(typ.tag)
    except:
        return False

# bitmapset 打印为整数列表
def extract_bitmapset(b):
    result = []
    if b == 0:
        return result
    i = 0
    while b:
        if b & 1:
            result.append(i)
        i += 1
        b >>= 1
    return result

# 解析 bitmapset*
def handle_bitmapset(bmp):
    result = []
    while bmp:
        word = bmp['words'][0]
        result += extract_bitmapset(int(word))
        bmp = bmp['next']
    return result

# 打印结构体为 dict，可嵌套，node_ptr 表示是否当前指针需要解引用+转换类型
def print_struct(val, node_ptr=True, visited=None):
    if visited is None:
        visited = set()
    result = {}

    if val.address:
        addr = int(val.address)
        if addr in visited:
            return f"<circular@{hex(addr)}>"
        visited.add(addr)

    typ = val.type
    if typ.code == gdb.TYPE_CODE_PTR:
        if val == 0:
            return None
        val = val.dereference()
        typ = val.type

    # 如果是 bitmapset
    if typ.tag == "Bitmapset":
        return handle_bitmapset(val)

    for field in typ.fields():
        if field.name == 'type' and node_ptr:
            # 只在第一次遇到 Node 时执行类型转换
            tag_val = int(val['type'])
            if tag_val in NODE_TAG_MAP:
                typename = NODE_TAG_MAP[tag_val]
                try:
                    fulltype = gdb.lookup_type(typename)
                    val = val.cast(fulltype.pointer()).dereference()
                    typ = val.type
                except Exception as e:
                    result["<error_cast>"] = str(e)
                break

    for field in typ.fields():
        fname = field.name
        fval = val[fname]

        # 跳过匿名 union / struct
        if fname is None:
            continue

        if fval.type.code == gdb.TYPE_CODE_PTR:
            target = fval.type.target()

            # Node 类型特殊处理
            if target.tag and target.tag.startswith("List"):
                if "IntList" in target.tag:
                    result[fname] = [int(x['intval']) for x in iterate_list(fval)]
                elif "OidList" in target.tag:
                    result[fname] = [int(x['oidval']) for x in iterate_list(fval)]
                else:
                    result[fname] = [print_struct(x, node_ptr=False, visited=visited.copy()) for x in iterate_list(fval)]
            elif is_node_type(target):
                result[fname] = print_struct(fval, node_ptr=True, visited=visited.copy())
            else:
                result[fname] = str(fval)
        elif fval.type.code == gdb.TYPE_CODE_STRUCT:
            if is_node_type(fval.type):
                result[fname] = print_struct(fval.address, node_ptr=True, visited=visited.copy())
            else:
                result[fname] = print_struct(fval.address, node_ptr=False, visited=visited.copy())
        elif fval.type.code == gdb.TYPE_CODE_ARRAY:
            result[fname] = [int(x) for x in fval]
        elif fval.type.code in (gdb.TYPE_CODE_INT, gdb.TYPE_CODE_ENUM):
            result[fname] = int(fval)
        elif fval.type.code == gdb.TYPE_CODE_FLT:
            result[fname] = float(fval)
        else:
            result[fname] = str(fval)
    return result

# 遍历 List 类型
def iterate_list(lst):
    while lst:
        cell = lst.dereference()
        yield cell['ptr_value']
        lst = cell['next']

# GDB 命令：pgjson EXPR
class PgJsonPrinter(gdb.Command):
    def __init__(self):
        super(PgJsonPrinter, self).__init__("pgjson", gdb.COMMAND_DATA)

    def invoke(self, arg, from_tty):
        try:
            val = gdb.parse_and_eval(arg)
            struct_data = print_struct(val)
            print(json.dumps(struct_data, indent=2))
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()

PgJsonPrinter()

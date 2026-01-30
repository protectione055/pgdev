# -*- coding: utf-8 -*-
"""
pg_slot_printer.py — GDB Python 扩展
用法：
    (gdb) source pg_slot_printer.py
    (gdb) printslot myslot
"""

import gdb

class PrintTupleTableSlot(gdb.Command):
    """Print PostgreSQL TupleTableSlot"""

    def __init__(self):
        super(PrintTupleTableSlot, self).__init__("printslot", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        if not arg:
            print("用法: printslot EXPR   (EXPR 是 TupleTableSlot* 表达式)")
            return

        try:
            slot = gdb.parse_and_eval(arg)
        except gdb.error as e:
            print(f"解析参数失败: {e}")
            return

        if slot.type.code == gdb.TYPE_CODE_PTR:
            slot = slot.dereference()

        # 打印基本字段
        tts_flags = int(slot['tts_flags'])
        tts_nvalid = int(slot['tts_nvalid'])
        tts_tid = slot['tts_tid']
        tts_tableOid = int(slot['tts_tableOid'])

        print("TupleTableSlot {")
        print(f"  tts_flags        = {tts_flags}")
        print(f"  tts_nvalid       = {tts_nvalid}")
        print(f"  tts_tableOid     = {tts_tableOid}")
        print(f"  tts_tid(ip_blkid)= ({int(tts_tid['ip_blkid']['bi_hi'])},{int(tts_tid['ip_blkid']['bi_lo'])}) "
              f"offset={int(tts_tid['ip_posid'])}")

        # 取出 tuple descriptor 指针
        tupdesc = slot['tts_tupleDescriptor']
        print(f"  tts_tupleDescriptor = {tupdesc}")

        # 打印 values 和 isnull 数组（最多前 10 个属性）
        try:
            values = slot['tts_values']
            isnull = slot['tts_isnull']

            max_print = min(tts_nvalid, 10)
            print(f"  values (前 {max_print} 个属性):")
            for i in range(max_print):
                v = values[i]
                n = bool(isnull[i])
                if n:
                    print(f"    [{i}] = NULL")
                else:
                    print(f"    [{i}] = {v}")
        except Exception as e:
            print(f"  (读取 tts_values 失败: {e})")

        print("}")

PrintTupleTableSlot()

from copy import deepcopy
from enum import Enum


class ModificationType(Enum):
    UPDATE_INPLACE = 1
    NEW_TABLE = 2
    RESET = 3


class TableItemInfo(object):
    def __init__(self,
                 index,
                 dtype,
                 text,
                 column_name,
                 font,
                 font_size,
                 font_color,
                 bg_color):
        self.index = index
        self.dtype = dtype
        self.text = text
        self.column_name = column_name
        self.font = font
        self.font_size = font_size
        self.font_color = font_color
        self.bg_color = bg_color


def build_item_info(item, index, column_name):
    def clone(obj):
        return type(obj)(obj)

    font = clone(item.font())
    dtype = item.custom_dtype
    font_size = font.pointSize()
    font_color = clone(item.foreground().color())
    bg_color = clone(item.background().color())
    info = TableItemInfo(index, dtype, item.text(), column_name, font, font_size, font_color, bg_color)
    return info


class TableSnapShot(object):
    def __init__(self):
        self.memo = {}

    def set(self, item, index, column_name):
        info = build_item_info(item, index, column_name)
        self.memo[index] = info

    def get(self, index):
        return self.memo.get(index)


class Modification(object):
    def __init__(self, mtype, item_infos):
        self.mtype = mtype
        self.item_infos = item_infos


class TableMemo(object):
    def __init__(self, handle):
        self._memos = []
        self.handle = handle

    def backup(self):
        self._memos.append(self.handle.save())

    def undo(self):
        if not len(self._memos):
            return
        data = self._memos.pop()
        try:
            self.handle.restore(data)
        except Exception:
            pass

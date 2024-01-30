from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, \
    QMenu, QAction, QShortcut, \
    QColorDialog, QFontDialog, QFileDialog
from PyQt5.QtCore import Qt, QPoint
from src.memo import TableMemo, Modification, TableSnapShot, ModificationType, build_item_info
from src.utis import withoutconnect, hex_to_rgb
import pandas as pd
from src.logger import logger
from PyQt5.QtGui import QKeySequence, QIcon, QFont, QColor
from src.excelio import ExcelAgent
from src.dfagent import DataFrameAgent
import tempfile
import shutil


class ResultTable(QTableWidget):
    def __init__(self, parent=None):
        super(ResultTable, self).__init__(parent)

    def _update(self, subject):
        modifications = subject.modification
        mtype = modifications.mtype
        if mtype not in [ModificationType.NEW_TABLE]:
            return
        self.clearContents()
        df = modifications.df
        shape = df.shape
        row, col = shape
        self.setRowCount(row + 1)
        self.setColumnCount(col)
        self.setHorizontalHeaderLabels(list(df.columns))
        item_infos = modifications.item_infos
        for item_info in item_infos:
            text = item_info.text
            index = item_info.index
            font = item_info.font
            font_color = item_info.font_color
            bg_color = item_info.bg_color
            row, column = index
            new_item = QTableWidgetItem(text)
            self.setItem(row, column, new_item)


class EnhancedTable(QTableWidget):
    _observers = []

    def __init__(self, fig_dir=None):
        super(EnhancedTable, self).__init__()
        self.itemChanged.connect(self.handle_item_changed)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setSelectionMode(QTableWidget.MultiSelection)
        self.selectionModel().selectionChanged.connect(self.selection_changed)
        self.cellClicked.connect(self.cell_clicked)
        self.selected_indexes = set()
        self.dataframe = None
        self.loaded = False
        self.init_table()
        self.snapshot = TableSnapShot()
        self.excel_agent = ExcelAgent()
        self.df_agent = DataFrameAgent()
        self.attach(self.excel_agent)
        self.attach(self.df_agent)
        self.recoder = TableMemo(self)
        self._modification = None
        self.fig_dir = fig_dir

    @property
    def modification(self):
        return self._modification

    @modification.setter
    def modification(self, data):
        self._modification = data

    def show_context_menu(self, pos):
        item = self.itemAt(pos)
        if item:
            row, column = item.row(), item.column()
            if len(self.selected_indexes) <= 1:
                self.clearSelection()
                self.selected_indexes = {(row, column)}
                self.setCurrentCell(row, column)
            main_menu = QMenu(self)
            style_menu = QMenu("设置单元格样式", self)

            font_action = QAction('字体', self)
            font_action.triggered.connect(self.config_font_style)
            style_menu.addAction(font_action)

            font_color_action = QAction('文字颜色', self)
            font_color_action.triggered.connect(self.config_font_color)
            style_menu.addAction(font_color_action)
            main_menu.addMenu(style_menu)

            bg_color_action = QAction('背景颜色', self)
            bg_color_action.triggered.connect(self.config_bg_color)
            style_menu.addAction(bg_color_action)

            # edit_menu = QMenu("删除", self)
            # delete_row_action = QAction('删除整行', self)
            # # delete_action.triggered.connect(lambda: self.delete_item(item))
            # edit_menu.addAction(delete_row_action)
            # delete_column_action = QAction('删除整列', self)
            # # delete_action.triggered.connect(lambda: self.delete_item(item))
            # edit_menu.addAction(delete_column_action)
            # main_menu.addMenu(edit_menu)

            main_menu.exec_(self.mapToGlobal(QPoint(pos.x() + 100, pos.y())))

    def clear_selection(self):
        self.clearSelection()
        # self.selected_indexes = set()

    def selection_changed(self, selected, deselected):
        selected_indexes = selected.indexes()

        if selected_indexes:
            selected_cells = set((index.row(), index.column()) for index in selected_indexes)
            self.selected_indexes = self.selected_indexes | selected_cells

    def cell_clicked(self, row, column):
        table_widget = self.sender()

        table_widget.clearSelection()
        self.selected_indexes = {(row, column)}

        table_widget.setCurrentCell(row, column)

    @withoutconnect
    def config_font_style(self):
        font, ok = QFontDialog.getFont()
        if ok:
            item_infos = []
            for index in self.selected_indexes:
                row, column = index
                old_item_info = self.snapshot.get(index)
                item_infos.append(old_item_info)
                item = self.item(row, column)
                item.setFont(font)
            self.modification = Modification(ModificationType.UPDATE_INPLACE, item_infos)
            self.clearSelection()
            self.save_checkpoint()

    @withoutconnect
    def config_font_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            item_infos = []
            for index in self.selected_indexes:
                row, column = index
                old_item_info = self.snapshot.get(index)
                item_infos.append(old_item_info)
                item = self.item(row, column)
                item.setData(Qt.TextColorRole, color)
            self.modification = Modification(ModificationType.UPDATE_INPLACE, item_infos)
            self.save_checkpoint()
            self.clearSelection()

    @withoutconnect
    def config_bg_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            item_infos = []
            for index in self.selected_indexes:
                row, column = index
                old_item_info = self.snapshot.get(index)
                item_infos.append(old_item_info)
                item = self.item(row, column)
                item.setBackground(color)
            self.modification = Modification(ModificationType.UPDATE_INPLACE, item_infos)
            self.save_checkpoint()
            self.clearSelection()

    @withoutconnect
    def init_table(self):
        self.setRowCount(20)
        self.setColumnCount(20)
        for row in range(20):
            for col in range(20):
                self.setItem(row, col, QTableWidgetItem(''))

    @withoutconnect
    def open_excel(self):
        filename, filetype = QFileDialog.getOpenFileName(self, "select excel file", "", "*.xlsx;;*.xls;;All Files(*)")
        if not filename:
            return
        ok = self.load_excel(filename)
        if not ok:
            return ok
        self.loaded = True
        return ok

    def load_excel(self, excel_file):
        ok = self.excel_agent.load(excel_file)
        if not ok:
            return ok
        self.setRowCount(self.excel_agent.num_rows)
        self.setColumnCount(self.excel_agent.num_cols)
        head_row = self.excel_agent.ws[1]
        head = [str(cell.value) for cell in head_row]
        self.setHorizontalHeaderLabels(head)
        for row in self.excel_agent.ws.iter_rows(min_row=2):
            for cell in row:
                cell_value = cell.value
                dtype = type(cell_value)
                i = cell.row - 2
                j = cell.column - 1
                item = QTableWidgetItem(str(cell_value))
                item.custom_dtype = dtype
                item = self.format_with_cell(cell, item)
                self.setItem(i, j, item)
                self.snapshot.set(item, (i, j), head[j])
        self.df_agent.load(excel_file)
        self.dataframe = pd.read_excel(excel_file)
        return ok

    def format_with_cell(self, cell, item):
        cell_font = cell.font
        font_name = cell_font.name
        font_size = cell_font.size
        item_font = QFont(font_name, int(font_size))
        item.setFont(item_font)

        font_color = cell_font.color.rgb
        if isinstance(font_color, str):
            color = QColor(*hex_to_rgb(font_color[2:]))
            item.setData(Qt.TextColorRole, color)

        # bg_color = cell.fill.fgColor.rgb
        # if isinstance(bg_color, str):
        #     color = QColor(*hex_to_rgb(bg_color[2:]))
        #     item.setBackground(color)
        return item

    def save(self):
        return self.modification

    def _update_inplace(self, item_infos):
        item_info = item_infos[0]
        text = item_info.text()
        index = item_info.index
        font = item_info.font
        font_color = item_info.font_color
        bg_color = item_info.bg_color
        row, column = index
        item = self.item(row, column)
        item.setText(text)
        item.setFont(font)
        item.setData(Qt.TextColorRole, font_color)
        item.setBackground(bg_color)

    def _insert_scalar(self, item_infos):
        item_info = item_infos[0]
        value = item_info.text
        row, col = item_info.index
        self.item(row, col).setText(value)

    def _delete_scalar(self, item_infos):
        item_info = item_infos[0]
        value = item_info.text
        row, col = item_info.index
        self.item(row, col).setText('')

    def restore(self, modifications):
        if modifications is None:
            return
        if len(modifications.item_infos) == 0:
            return
        mtype = modifications.mtype
        if mtype != ModificationType.UPDATE_INPLACE:
            return
        self._update_inplace(modifications.item_infos)
        self.modification = modifications
        self.notify()
        self.modification = None

    @withoutconnect
    def insert_result(self, res):
        stdout, stderror = res
        if stdout is None:
            return
        row_count = self.rowCount()
        col_count = self.columnCount()
        if isinstance(stdout, pd.DataFrame):
            new_shape = stdout.shape
            new_item_infos = []
            for i in range(new_shape[0]):
                for j in range(new_shape[1]):
                    value = stdout.iloc[i, j]
                    item = QTableWidgetItem(str(value))
                    index = (i, j)
                    column_name = stdout.columns[j]
                    dtype = type(value)
                    item.custom_dtype = dtype
                    new_item_infos.append(build_item_info(item, index, column_name))
            self.modification = Modification(ModificationType.NEW_TABLE, new_item_infos)
            self.modification.df = stdout
            self.notify()
            return True
        else:
            new_item = QTableWidgetItem(str(stdout))
            new_item.setText(str(stdout))
            new_item.custom_dtype = self.item(row_count - 2, 0).custom_dtype
            # TODO: set custom datatype
            old_item = self.item(row_count - 1, 0)
            old_item.custom_dtype = self.item(row_count - 2, 0).custom_dtype
            row = old_item.row()
            column = old_item.column()
            index = (row, column)
            column_name = self.get_column_name(column)
            old_modification = Modification(ModificationType.UPDATE_INPLACE,
                                            [build_item_info(old_item, index, column_name)])
            self.setItem(row_count - 1, 0, new_item)
            self.modification = Modification(ModificationType.UPDATE_INPLACE,
                                             [build_item_info(new_item, index, column_name)])
            self.notify()
            self.modification = old_modification
            self.save_checkpoint()
            self.snapshot.set(new_item, index, column_name)

    @withoutconnect
    def undo_modification(self):
        self.recoder.undo()

    def save_checkpoint(self):
        self.recoder.backup()

    def get_column_name(self, column):
        return self.horizontalHeaderItem(column).text()

    def handle_item_changed(self, item):
        if self.dataframe is None:
            return
        item_info = self.snapshot.get(item)
        row = item.row()
        column = item.column()
        index = (row, column)
        column_name = self.get_column_name(column)
        if item_info is None:
            mtype = ModificationType.INSERT_SCALAR
            item_info = build_item_info(item, index, column_name)
        else:
            mtype = ModificationType.UPDATE_INPLACE
        modification = Modification(mtype, item_info)
        self.modification = modification
        self.save_checkpoint()
        self.snapshot.set(item, index, column_name)

    def register_shortcut(self):
        self.shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Z), self)
        self.shortcut.activated.connect(self.undo_modification)

    def file_save(self):
        file_filter = "*.xlsx;;*.xls;;All Files(*)"
        path, _ = QFileDialog.getSaveFileName(self, "Save excel file", "", file_filter)

        if not path:
            return
        self.excel_agent.save(path, self.fig_dir)

    def attach(self, observer):
        self._observers.append(observer)

    def detach(self, observer):
        self._observers.remove(observer)

    def notify(self):
        for observer in self._observers:
            observer._update(self)

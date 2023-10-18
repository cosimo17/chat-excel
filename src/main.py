from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, \
    QTableWidgetItem, QHBoxLayout, QTextEdit, QShortcut, QMenuBar, \
    QMenu, QAction, QFileDialog, QScrollArea
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt, QTimer
import sys
import openpyxl
from richtext_display import CodeEditor
from memo import TableMemo, Modification
import pandas as pd
from copy import deepcopy
from utis import withoutconnect
from interpreter import PythonInterpreter
from chatgpt import ChatBot
from prompt_template import prompt


class Main(QWidget):
    def __init__(self):
        super(Main, self).__init__()
        self.setWindowTitle("chat-excel")
        self.loaded = False
        self.collapsed = False
        self.chat_widgets = None
        self.hbox = self.vbox = None
        self.table_widget = None
        self.chat_history = None
        self.user_input = None
        self.dataframe = None
        self.recoder = TableMemo(self)
        self.init_ui()
        self.register_shortcut()
        self.init_table()
        self.interpreter = PythonInterpreter()
        self.bot = ChatBot()

    def init_ui(self):
        hbox = QHBoxLayout()
        vbox = QVBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        self.hbox = hbox
        self.vbox = vbox
        chat_widget = QWidget()
        # container to display excel data
        self.table_widget = QTableWidget()
        self.table_widget.itemChanged.connect(self.handle_item_changed)
        hbox.addWidget(self.table_widget, 3)
        # readonly richtext editer to display the chat history
        self.chat_history = CodeEditor()
        self.chat_history.setReadOnly(True)
        self.chat_history.setLineWrapMode(QTextEdit.NoWrap)
        # add scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.chat_history)
        self.chat_history.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_history.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        vbox.addWidget(self.chat_history, 4)
        # text editer to handle user's input
        self.user_input = QTextEdit()
        vbox.addWidget(self.user_input, 1)
        chat_widget.setLayout(vbox)
        hbox.addWidget(chat_widget, 2)
        # menu setting
        menubar = QMenuBar()
        fileMenu = QMenu("&File", self)
        openAct = QAction('Open', self)
        openAct.triggered.connect(self.open_excel)
        fileMenu.addAction(openAct)
        saveAvt = QAction('Save', self)
        saveAvt.triggered.connect(self.file_save)
        fileMenu.addAction(saveAvt)
        menubar.addMenu(fileMenu)
        # Creating menus using a title
        editMenu = menubar.addMenu("&Edit")
        undoAct = QAction('Undo', self)
        undoAct.triggered.connect(self.undo_modification)
        editMenu.addAction(undoAct)
        helpMenu = menubar.addMenu("&Help")
        hbox.setMenuBar(menubar)

        self.setLayout(hbox)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.type_one_by_one)
        self.current_index = 0

    def register_shortcut(self):
        # hotkey
        # send chat message
        self.shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Q), self)
        self.shortcut.activated.connect(self.chat)

        # hide chat widget
        self.shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_A), self)
        self.shortcut.activated.connect(self.collapse_chat_widget)

        # undo modification
        self.shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Z), self)
        self.shortcut.activated.connect(self.undo_modification)

    @withoutconnect
    def init_table(self):
        self.table_widget.setRowCount(20)
        self.table_widget.setColumnCount(20)
        for row in range(20):
            for col in range(20):
                self.table_widget.setItem(row, col, QTableWidgetItem(''))

    @withoutconnect
    def open_excel(self):
        filename, filetype = QFileDialog.getOpenFileName(self, "select excel file", "", "*.xlsx;;*.xls;;All Files(*)")
        if not filename:
            return
        self.load_data_with_pandas(filename)
        self.loaded = True

    def load_data(self, excel_file):
        workbook = openpyxl.load_workbook(excel_file)
        sheet = workbook.active

        self.table_widget.setRowCount(sheet.max_row)
        self.table_widget.setColumnCount(sheet.max_column)

        list_values = list(sheet.values)
        self.table_widget.setHorizontalHeaderLabels(list_values[0])

        row_index = 0
        for value_tuple in list_values[1:]:
            col_index = 0
            for value in value_tuple:
                self.table_widget.setItem(row_index, col_index, QTableWidgetItem(str(value)))
                col_index += 1
            row_index += 1

    def load_data_with_pandas(self, excel_file):
        df = pd.read_excel(excel_file)
        shape = df.shape
        rows, cols = shape
        self.table_widget.setRowCount(rows+1)
        self.table_widget.setColumnCount(cols)
        self.table_widget.setHorizontalHeaderLabels(list(df.columns))
        for i in range(rows):
            for j in range(cols):
                value = df.iloc[i, j]
                self.table_widget.setItem(i, j, QTableWidgetItem(str(value)))
        self.dataframe = deepcopy(df)

    def save(self):
        return self.modification

    def restore(self, modification):
        if modification is None:
            return
        rows = modification.row_indexs
        cols = modification.col_indexs
        values = modification.values
        for i in range(len(modification)):
            row, col, value = rows[i], cols[i], values[i]
            self.table_widget.setItem(row, col, QTableWidgetItem(str(value)))
            d = self.dataframe.iloc[row, col]
            self.dataframe.iloc[row, col] = type(d)(value)

    @withoutconnect
    def undo_modification(self):
        self.recoder.undo()

    def save_checkpoint(self):
        self.recoder.backup()

    def handle_item_changed(self, item):
        if self.dataframe is None:
            return
        row = item.row()
        col = item.column()
        value = item.text()
        self.modification = Modification([row], [col], [self.dataframe.iloc[row, col]])
        d = self.dataframe.iloc[row, col]
        self.dataframe.iloc[row, col] = type(d)(value)
        self.save_checkpoint()

    def collapse_chat_widget(self):
        if not self.collapsed:
            widget = self.hbox.itemAt(1).widget()
            widget.setVisible(False)
            # backup chat widget
            self.chat_widget = widget
            self.collapsed = True
        else:
            self.chat_widget.setVisible(True)
            self.collapsed = False

    def type_one_by_one(self):
        if not self.answer:
            return
        if self.current_index < len(self.answer):
            next_char = self.answer[self.current_index]
            self.chat_history.insertPlainText(next_char)
            self.current_index += 1
        else:
            self.answer = ''
            self.timer.stop()

    def chat(self):
        self.table_widget.maximumWidth()
        if self.user_input.hasFocus():
            message = self.user_input.toPlainText().strip()
            task = message
            message = "Q:\n{}".format(message)
            if message:
                self.chat_history.append(message)
                self.user_input.clear()
                if self.dataframe is None:
                    self.answer = '\nA:\n' + '请先打开需要处理的excel!\n\n'
                else:
                    # get response from llm
                    formatted_prompt = prompt.format(self.dataframe.shape, self.dataframe.head(3), self.dataframe.dtypes, task)
                    response = self.bot.get_response(formatted_prompt)
                    self.answer = '\nA:\n' + response + '\n\n'
                # typing answer char by char
                self.current_index = 0
                self.timer.start(30)
        return

    def file_save(self):
        file_filter = "*.xlsx;;*.xls;;All Files(*)"
        path, _ = QFileDialog.getSaveFileName(self, "Save excel file", "", file_filter)

        if not path:
            return
        self.dataframe.to_excel(path)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main()
    window.showMaximized()
    app.exec_()

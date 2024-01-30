from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, \
    QHBoxLayout, QTextEdit, QShortcut, QMenuBar, \
    QMenu, QAction, QScrollArea, QLabel, QTabWidget, \
    QComboBox, QInputDialog, QMessageBox
from PyQt5.QtGui import QKeySequence, QIcon
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
import sys
from src.richtext_display import CodeEditor
from src.plotwin import PlotWidget
from src.memo import TableMemo
from src.utis import wrap_code, decodestdoutput, extract_func_info, resource_path
from src.interpreter import PythonInterpreter
from src.chatgpt import ChatBot
from src.prompt_template import prompt, chart_prompt, prompt_en, chart_prompt_en
from openai.error import APIError, AuthenticationError
from enum import Enum
from pathlib import Path
import os
from configparser import ConfigParser
from src.logger import logger
from src.tablewin import EnhancedTable, ResultTable
from functools import partial
import tempfile
import shutil

project_path = Path(__file__).parent.parent


class QChatBot(QThread):
    res_signal = pyqtSignal(tuple)

    def __init__(self, bot, prompts, default_answer, exception_answer):
        super(QChatBot, self).__init__()
        self.formatted_prompt = prompts
        self.bot = bot
        self.default_answer = default_answer
        self.exception_answer = exception_answer

    def run(self):
        if self.formatted_prompt == '':
            answer = self.default_answer
            token_count = 0
        else:
            try:
                answer, token_count = self.bot.get_response(self.formatted_prompt)
                answer = '\n#A:\n' + answer + '\n\n'
            except APIError:
                answer, token_count = self.exception_answer, 0
            except AuthenticationError:
                answer, token_count = self.exception_answer, 0
        self.res_signal.emit((answer, token_count))


class QInterpreter(QThread):
    res_signal = pyqtSignal(tuple)

    def __init__(self, code):
        super(QInterpreter, self).__init__()
        self.code = code
        self.interpreter = PythonInterpreter()

    def run(self):
        response = self.interpreter.execute(self.code)
        self.res_signal.emit(response)


class ChatWidget(QWidget):
    def __init__(self, main_win):
        super(ChatWidget, self).__init__()
        self.vbox = QVBoxLayout()

        # readonly richtext editer to display the chat history
        self.chat_history = CodeEditor()
        self.chat_history.setReadOnly(True)
        self.chat_history.setLineWrapMode(QTextEdit.NoWrap)
        # add scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.chat_history)
        self.chat_history.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_history.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.vbox.addWidget(self.chat_history, 4)

        self.switch_mode_box = QComboBox()
        self.switch_mode_box.addItem("Chat")
        self.switch_mode_box.addItem("Plot")
        self.switch_mode_box.currentIndexChanged.connect(main_win.switch_mode)
        self.mode_info = QLabel("mode: ")
        hbox2 = QHBoxLayout()
        # hbox2.addSpacing(20)
        hbox2.addWidget(self.mode_info)
        hbox2.addWidget(self.switch_mode_box)
        hbox2.addStretch(1)
        self.vbox.addLayout(hbox2)
        self.user_input = QTextEdit()
        self.vbox.addWidget(self.user_input, 1)

        self.token_logger = QLabel("Token:0   Cost:$0.0")
        self.vbox.addWidget(self.token_logger)
        self.setLayout(self.vbox)

    def set_token_usage(self, token):
        cost = token / 1000 * 0.002
        text = "Token: {} Cost: ${:.4f}".format(token, cost)
        self.token_logger.setText(text)


class Mode(Enum):
    CHAT_MODE = 1
    PLOT_MODE = 2


class MainWin(QWidget):
    def __init__(self):
        super(MainWin, self).__init__()
        self.setWindowTitle("chat-excel")
        self.language_configs = {}
        self.current_language = 'zh'
        self.collapsed = False
        self.chat_widgets = None
        self.hbox = self.vbox = None
        self.table_widget = None
        self.code = None
        self.chat_thread = None
        self.interpreter_thread = None
        self.stdout = None
        self.stderror = None
        self.mode = Mode.CHAT_MODE
        self.token_count = 0
        self.default_answer = None
        self.exception_answer = None
        self.fig_dir = tempfile.mkdtemp()
        self.recoder = TableMemo(self)
        self.init_ui()
        self.register_shortcut()
        self.bot = ChatBot()
        self.api_key = os.getenv('APIKEY', None)
        self.key_memo = "apikey.txt"
        if os.path.exists(self.key_memo):
            with open(self.key_memo, 'r') as f:
                self.api_key = f.read().rstrip()
                self.bot.set_api_key(self.api_key)

    def init_ui(self):
        icon_path = os.path.join("assets", "bot.jpg")
        icon_path = resource_path(icon_path)
        QApplication.setWindowIcon(QIcon(icon_path))
        hbox = QHBoxLayout()
        vbox = QVBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        self.hbox = hbox
        self.vbox = vbox
        # chat_widget = QWidget()
        # container to display excel data
        self.table_widget = EnhancedTable(self.fig_dir)
        self.sheet_tabs = QTabWidget()
        self.result_table = ResultTable(self)
        self.table_widget.attach(self.result_table)
        self.sheet_tabs.setTabPosition(QTabWidget.South)
        self.sheet_tabs.addTab(self.table_widget, 'Your Sheet')
        self.sheet_tabs.addTab(self.result_table, 'AI answer')
        hbox.addWidget(self.sheet_tabs, 3)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)

        self.chat_widget = ChatWidget(self)
        self.plot_widget = PlotWidget()
        self.tabs.addTab(self.chat_widget, "chat")
        self.tabs.addTab(self.plot_widget, 'plot')
        hbox.addWidget(self.tabs, 2)

        # menu setting
        menubar = QMenuBar()
        menubar.setStyleSheet("QMenuBar { background-color: lightgreen; }")
        fileMenu = QMenu("&文件", self)
        self.language_configs[fileMenu] = {'en': "&File", 'zh': "&文件"}

        openAct = QAction('打开', self)
        self.language_configs[openAct] = {'en': "&open", 'zh': "&打开"}
        openAct.triggered.connect(self.table_widget.open_excel)
        fileMenu.addAction(openAct)
        saveAct = QAction('保存', self)
        self.language_configs[saveAct] = {'en': "&save", 'zh': "&保存"}
        saveAct.triggered.connect(self.table_widget.file_save)
        fileMenu.addAction(saveAct)
        menubar.addMenu(fileMenu)
        # Creating menus using a title
        editMenu = menubar.addMenu("&编辑")
        self.language_configs[editMenu] = {'en': "&Edit", 'zh': "&编辑"}
        undoAct = QAction('撤销修改', self)
        self.language_configs[undoAct] = {'en': "&undo", 'zh': "&撤销修改"}
        undoAct.triggered.connect(self.table_widget.undo_modification)
        editMenu.addAction(undoAct)

        modelMenu = menubar.addMenu("&模型")
        self.language_configs[modelMenu] = {'en': "&Model", 'zh': "&模型"}
        openaiAct = QAction('chatgpt', self)
        modelMenu.addAction(openaiAct)

        lanMenu = menubar.addMenu("&语言(Language)")
        setzhAct = QAction('中文', self)
        setzhAct.triggered.connect(partial(self.reset_language, language='zh'))
        lanMenu.addAction(setzhAct)
        setenAct = QAction('English', self)
        setenAct.triggered.connect(partial(self.reset_language, language='en'))
        lanMenu.addAction(setenAct)

        helpMenu = menubar.addMenu("&帮助")
        self.language_configs[helpMenu] = {'en': "&Help", 'zh': "&帮助"}
        hbox.setMenuBar(menubar)

        self.setLayout(hbox)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.type_one_by_one)
        self.current_index = 0
        self.load_tips_info()

    def load_tips_info(self, language=None):
        lan = 'zh' if language is None else language
        if os.path.exists(resource_path(os.path.join('src', 'tips_info.ini'))):
            logger.debug("ini exist")
        parser = ConfigParser()
        parser.read(resource_path(os.path.join('src', 'tips_info.ini')), encoding='utf-8')
        self.default_answer = parser.get(lan, 'default_answer').replace('\\n', '\n')
        self.exception_answer = parser.get(lan, 'exception_answer').replace('\\n', '\n')
        self.unknown_answer = parser.get(lan, 'unknown_answer')
        self.execution_error = parser.get(lan, 'execution_error').replace('\\n', '\n')
        self.api_win_title = parser.get(lan, 'api_win_title').replace('\\n', '\n')
        self.input_tip = parser.get(lan, 'input_tip').replace('\\n', '\n')
        self.confirm_tip = parser.get(lan, 'confirm_tip').replace('\\n', '\n')

    def reset_language(self, language='zh'):
        if language not in ['zh', 'en']:
            return
        self.load_tips_info(language)
        self.current_language = language
        for item in self.language_configs.keys():
            if isinstance(item, QMenu):
                item.setTitle(self.language_configs[item][language])
            if isinstance(item, QAction):
                item.setText(self.language_configs[item][language])

    def register_shortcut(self):
        # hotkey
        # send chat message
        self.shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Q), self)
        self.shortcut.activated.connect(self.chat)

        # hide chat widget
        self.shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_A), self)
        self.shortcut.activated.connect(self.collapse_chat_widget)

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
        def is_python_source_code(s):
            return not (self.code == self.default_answer or
                        self.code == self.exception_answer or
                        "i don't know" in s.lower())

        if not self.answer:
            return
        if self.current_index < len(self.answer):
            next_char = self.answer[self.current_index]
            self.chat_widget.chat_history.insertPlainText(next_char)
            self.current_index += 1
        else:
            self.code = self.answer
            self.timer.stop()
            self.answer = None
            if is_python_source_code(self.code):
                # execute the code and display the result
                self.execute()
            self.chat_widget.switch_mode_box.setEnabled(True)

    def execute(self):
        if self.mode == Mode.CHAT_MODE:
            code = wrap_code(self.code, self.table_widget.dataframe)
            self.interpreter_thread = QInterpreter(code)
            self.interpreter_thread.res_signal.connect(self.receive_output)
            self.interpreter_thread.start()
        elif self.mode == Mode.PLOT_MODE:
            df = self.table_widget.dataframe
            func_names, func_args, func_kwargs = extract_func_info(self.code, df)
            self.plot_widget.new_axes()
            self.plot_widget.call_func(func_names, func_args, func_kwargs)
            self.plot_widget.add_figure()
            self.plot_widget.save_fig(self.fig_dir)
            self.tabs.setCurrentIndex(1)

    def receive_output(self, output):
        stdout, stderror = output
        try:
            stdout = decodestdoutput(stdout)
        except Exception:
            return
        self.stdout = stdout
        self.stderro = stderror
        if 'Traceback' in stderror:
            self.chat_widget.chat_history.append(self.execution_error)
            return
        # display the output and handle the error
        res = self.table_widget.insert_result(res=[stdout, stderror])
        if res:
            self.sheet_tabs.setCurrentIndex(1)

    def chat(self):
        if self.api_key is None:
            text, ok = QInputDialog.getText(self, self.api_win_title, self.input_tip)
            if ok:
                self.api_key = text
                self.bot.set_api_key(text)
                reply = QMessageBox.question(self, '', self.confirm_tip,
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.save_apikey()
            else:
                return
        self.table_widget.maximumWidth()
        if self.chat_widget.user_input.hasFocus():
            message = self.chat_widget.user_input.toPlainText().strip()
            task = message
            if message:
                message = "Q:\n{}".format(message)
                self.chat_widget.chat_history.append(message)
                self.chat_widget.user_input.clear()
                if self.table_widget.df_agent.df is not None:
                    formatted_prompt = self.format_prompt(task)
                else:
                    formatted_prompt = ''
                # get response from llm
                # using QThread to avoid GUI freeze
                self.chat_widget.switch_mode_box.setEnabled(False)
                self.chat_thread = QChatBot(self.bot, formatted_prompt, self.default_answer, self.exception_answer)
                self.chat_thread.res_signal.connect(self.receive_answer)
                self.chat_thread.start()

        return

    def format_prompt(self, task):
        template_prompts = {
            Mode.CHAT_MODE: {'en': prompt_en, 'zh': prompt},
            Mode.PLOT_MODE: {'en': chart_prompt_en, 'zh': chart_prompt}
        }
        template_prompt = template_prompts[self.mode][self.current_language]
        formatted_prompt = '' if self.table_widget.dataframe is None \
            else template_prompt.format(self.table_widget.df_agent.shape,
                                        self.table_widget.df_agent.head(3),
                                        self.table_widget.df_agent.dtypes, task)
        return formatted_prompt

    def receive_answer(self, res):
        answer, token_count = res
        self.answer = answer
        self.token_count += token_count
        self.chat_widget.set_token_usage(self.token_count)
        self.current_index = 0
        self.timer.start(30)

    def switch_mode(self, index):
        self.mode = Mode.PLOT_MODE if self.chat_widget.switch_mode_box.currentText() == "Plot" else Mode.CHAT_MODE

    def save_apikey(self):
        with open(self.key_memo, 'w') as f:
            f.write(self.api_key)

    def closeEvent(self, event):
        try:
            shutil.rmtree(self.fig_dir)
        except:
            pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWin()
    window.showMaximized()
    app.exec_()

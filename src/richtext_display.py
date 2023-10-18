import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QTextDocument, QColor
from PyQt5.QtCore import Qt, QRegExp


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(PythonHighlighter, self).__init__(parent)

        self.highlightingRules = []

        # 定义关键字及其对应的颜色
        kw_color = QColor(204, 120, 50)
        keywords = {
            "object": kw_color,
            "and": kw_color,
            "as": kw_color,
            "assert": kw_color,
            "break": kw_color,
            "class": kw_color,
            "continue": kw_color,
            "def": kw_color,
            "del": kw_color,
            "elif": kw_color,
            "else": kw_color,
            "except": kw_color,
            "False": kw_color,
            "finally": kw_color,
            "for": kw_color,
            "from": kw_color,
            "global": kw_color,
            "if": kw_color,
            "import": kw_color,
            "in": kw_color,
            "is": kw_color,
            "lambda": kw_color,
            "None": kw_color,
            "nonlocal": kw_color,
            "not": kw_color,
            "or": kw_color,
            "pass": kw_color,
            "raise": kw_color,
            "return": kw_color,
            "True": kw_color,
            "try": kw_color,
            "while": kw_color,
            "with": kw_color,
            "yield": kw_color
        }

        for word, color in keywords.items():
            keywordFormat = QTextCharFormat()
            keywordFormat.setForeground(color)
            keywordFormat.setFontWeight(QFont.Bold)
            pattern = QRegExp(r'\b' + word + r'\b')
            rule = {'pattern': pattern, 'format': keywordFormat}
            self.highlightingRules.append(rule)

        # 定义字符串格式
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(Qt.darkGreen)
        self.highlightingRules.append({'pattern': QRegExp(r'".*?"'), 'format': stringFormat})
        self.highlightingRules.append({'pattern': QRegExp(r"'.*?'"), 'format': stringFormat})

        # 定义注释格式
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(Qt.darkGray)
        self.highlightingRules.append({'pattern': QRegExp(r'#.*'), 'format': commentFormat})

    def highlightBlock(self, text):
        for rule in self.highlightingRules:
            expression = rule['pattern']
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, rule['format'])
                index = expression.indexIn(text, index + length)


class CodeEditor(QTextEdit):
    def __init__(self):
        super(CodeEditor, self).__init__()

        self.highlighter = PythonHighlighter(self.document())


class CodeHighlighterExample(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # 创建一个 CodeEditor 控件
        codeEditor = CodeEditor()

        # 设置主窗口的布局
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(codeEditor)
        self.setCentralWidget(central_widget)

        # 设置窗口属性
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('Code Highlighter Example')
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CodeHighlighterExample()
    sys.exit(app.exec_())

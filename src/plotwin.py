import os.path
import sys
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QSizePolicy,
    QLabel,
)
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class PlotWidget(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content.setLayout(content_layout)
        label = QLabel("No Plots Now")
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        content_layout.addWidget(label)

        sc = QScrollArea()
        sc.setFrameShape(QtWidgets.QFrame.NoFrame)
        sc.setWidgetResizable(True)
        sc.setWidget(content)

        self.main_layout.addWidget(sc)
        self.setLayout(self.main_layout)

        self.content_layout = content_layout
        self.content = content

        self.figsize = (6, 3)
        self.current_ax = None
        self.current_static_canvas = None
        self.static_canvas = []
        self.figs = []
        self.tool_bars = []

    def new_axes(self):
        if self.ax_created():
            return
        new_fig = Figure(figsize=self.figsize)
        self.figs.append(new_fig)
        static_canvas = FigureCanvas(new_fig)
        ax = static_canvas.figure.subplots()
        self.current_ax = ax
        self.current_static_canvas = static_canvas
        self.current_static_canvas.setSizePolicy(QSizePolicy.Fixed,
                                                 QSizePolicy.Fixed)

    def ax_created(self):
        return self.current_ax is not None and self.current_static_canvas is not None

    def add_figure(self):
        if self.ax_created():
            tool_bar = NavigationToolbar(self.current_static_canvas, self)

            self.tool_bars.append(tool_bar)
            self.content_layout.addWidget(tool_bar)
            self.content_layout.addWidget(self.current_static_canvas)
            self.content_layout.addStretch(1)
            self.static_canvas.append(self.current_static_canvas)
            self.current_static_canvas = None
            self.current_ax = None

    def call_func(self, names, func_args, func_kwargs):
        if self.ax_created():
            for i in range(len(names)):
                try:
                    func = getattr(self.current_ax, names[i])
                except AttributeError:
                    continue
                args = func_args[i]
                kwargs = func_kwargs[i]
                func(*args, **kwargs)

    def save_fig(self, fig_dir):
        if len(self.figs) == 0:
            return
        i = len(self.figs)
        fig = self.figs[-1]
        savename = 'Plot{:02d}.png'.format(i)
        savename = os.path.join(fig_dir, savename)
        fig.savefig(savename)

from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)

class Ui_GraphsWindow(object):
    def setupUi(self, MainWindow, figures: list):
        MainWindow.setObjectName("GraphsWindow")
        MainWindow.resize(800, 600)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setAlignment(QtCore.Qt.AlignTop)

        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollWidget = QtWidgets.QWidget()
        self.scrollLayout = QtWidgets.QVBoxLayout(self.scrollWidget)

        # Вставляем каждый Figure как FigureCanvas + Toolbar
        for fig in figures:
            canvas = FigureCanvas(fig)
            canvas.setMinimumHeight(250)

            container = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)

            toolbar = NavigationToolbar(canvas, container)
            layout.addWidget(toolbar)
            layout.addWidget(canvas)

            self.scrollLayout.addWidget(container)

        self.scrollArea.setWidget(self.scrollWidget)
        self.verticalLayout.addWidget(self.scrollArea)
        MainWindow.setCentralWidget(self.centralwidget)

from PyQt5 import QtWidgets, QtCore, QtGui
import sys

from Data.ControllerParams import ControllerParams

# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from UI.Simulation import Ui_Simulation
from Data.Calculations import *

class UI_LoadingWindow(object):
    def setupController(self, Controller):
        self.Controller = Controller

        # layers = [
        #     ('layer', 0.0, None, None),
        #     ('item', 1.711111111111111, None, Syrio(name='Сырьё 3', percentage=40.0, density=1.7, color=None)),
        #     ('layer', 2.19, None, None),
        #     ('item', 2.666666666666667, None, Syrio(name='Сырьё 8', percentage=15.0, density=2.0, color=None)),
        #     ('layer', 4.86, None, None),
        #     ('item', 6.2444444444444445, None, Syrio(name='Сырьё 5', percentage=25.0, density=1.3, color=None)),
        #     ('layer', 7.17, None, None),
        #     ('item', 8.555555555555557, None, Syrio(name='Сырьё 1', percentage=20.0, density=1.2, color=None)),
        #     ('layer', 8.88, None, None),
        #     ('item', 9.440000000000001, None, Syrio(name='Сырьё 6', percentage=35.0, density=1.6, color=None)),
        #     ('layer', 10.0, None, None)
        # ]
        # heat_schedule = [
        #     (1, 500),
        #     (18, 442.5950355646992),
        #     (18, 363),
        #     (45, 250),
        #     (70, 383),
        #     (70, 515),
        #     (89, 381),
        #     (104, 381),
        #     (126, 506),
        #     (150, 500)
        # ]
        # #self.Controller = ControllerParams()
        # # Инициализация параметров
        # self.Controller.height = 1.0  # Высота реактора
        # self.Controller.radius = 1.0  # Радиус реактора
        #
        # self.Controller.items_and_layers=layers
        #
        # self.Controller.thermal_diffusivity = 0.01  # Температуропроводность
        # self.Controller.time_delta = 0.01  #
        # self.Controller.time_steps = 100  # Кол-во шагов моделирования
        # self.Controller.heat_function = heat_schedule  # Функция нагрева
        # self.Controller.heat_source = None  # Точка подвода тепла (r, z, φ)
        # self.Controller.grid_size = (10, 10, 10)  # Размер сетки (r, z, φ)
        #
        # print(self.Controller.items_and_layers)
        # print("------------")

    def setupUi(self, LoadingForm):
        self.window = LoadingForm
        LoadingForm.setObjectName("LoadingForm")
        LoadingForm.resize(500, 450)
        LoadingForm.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        LoadingForm.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Основной layout
        self.verticalLayout = QtWidgets.QVBoxLayout(LoadingForm)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)

        # Картинка
        self.image_label = QtWidgets.QLabel(LoadingForm)
        current_dir = os.path.dirname(__file__)  # Папка, где находится Loading.py
        image_path = os.path.join(current_dir, "../images/warmRadar.png")
        pixmap = QtGui.QPixmap(image_path).scaled(500, 400, QtCore.Qt.KeepAspectRatio)
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.verticalLayout.addWidget(self.image_label)

        # Кастомный прогресс-бар
        self.progress_bar = CustomProgressBar(LoadingForm)
        self.progress_bar.setFixedSize(500, 30)
        self.verticalLayout.addWidget(self.progress_bar, alignment=QtCore.Qt.AlignCenter)
        simulation = Simulation(self.Controller)
        simulation.calculate()
        # # Настраиваем таймер
        self.timer = QtCore.QTimer(LoadingForm)
        self.timer.timeout.connect(self.update_progress)
        self.progress = 0
        self.timer.start(10)  # Интервал 0.1 секунда

    def update_progress(self):
        self.progress += 1
        self.progress_bar.setValue(self.progress)
        if self.progress >= 100:
            self.timer.stop()
            self.goSimulation()

    def goSimulation(self):
        self.window.close()
        self.simulationWindow = QtWidgets.QMainWindow()
        self.simulationUi = Ui_Simulation()
        self.simulationUi.setupController(self.Controller)
        self.simulationUi.setupUi(self.simulationWindow)
        self.simulationWindow.show()


class CustomProgressBar(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.setMinimumSize(300, 30)

    def setValue(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        rect = self.rect()

        # Фон прогресс-бара
        painter.setBrush(QtGui.QColor("#e0e0e0"))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRect(rect)

        # Заполненная часть прогресс-бара
        fill_width = rect.width() * self.value / 100
        gradient = QtGui.QLinearGradient(0, 0, rect.width(), 0)
        gradient.setColorAt(0.0, QtGui.QColor("#9A32CD"))  # Светло-фиолетовый (Amethyst)
        gradient.setColorAt(0.33, QtGui.QColor("#4682B4"))  # Светлый синий (Steel Blue)
        gradient.setColorAt(0.66, QtGui.QColor("#32CD32"))  # Светло-зелёный (Lime Green)
        gradient.setColorAt(1.0, QtGui.QColor("#FFD700"))  # Светло-жёлтый (Golden Yellow)

        painter.setBrush(QtGui.QBrush(gradient))
        painter.drawRect(0, 0, int(fill_width), rect.height())

        # Текст прогресса
        painter.setPen(QtGui.QColor("black"))
        painter.setFont(QtGui.QFont("Arial", 12))
        text = f"{self.value}%"
        painter.drawText(rect, QtCore.Qt.AlignCenter, text)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    LoadingForm = QtWidgets.QWidget()
    ui = UI_LoadingWindow()
    ui.setupUi(LoadingForm)
    LoadingForm.show()
    sys.exit(app.exec_())

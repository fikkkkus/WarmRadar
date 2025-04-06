from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import os

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from UI.TGAVisializer import Ui_GraphsWindow
from Data.TGA import TGA

class Ui_DependencySelectorWithFile(object):
    def setupUi(self, MainWindow):
        self.MainWindow = MainWindow
        MainWindow.setObjectName("DependencySelector")
        MainWindow.resize(700, 600)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setAlignment(QtCore.Qt.AlignTop)

        label = QtWidgets.QLabel("Выберите зависимости:")
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 12px;")
        self.verticalLayout.addWidget(label)

        # Зависимости (6 штук, осмысленные)
        self.dependencies = [
            ("Temp./°C", "Time/min", "Время от Температуры"),
            ("Temp./°C", "DSC/(uV/mg)", "Тепловой поток от Температуры"),
            ("Temp./°C", "Mass/%", "Масса от Температуры"),
            ("Time/min", "DSC/(uV/mg)", "Тепловой поток от Времени"),
            ("Time/min", "Mass/%", "Масса от Времени"),
            ("DSC/(uV/mg)", "Mass/%", "Масса от Теплового потока"),
        ]

        self.checkboxes = []
        for x, y, title in self.dependencies:
            full_text = f"{title}: x = {x}, y = {y}"
            cb = QtWidgets.QCheckBox(full_text)
            cb.setStyleSheet("font-size: 16px; margin: 6px;")
            self.verticalLayout.addWidget(cb)
            self.checkboxes.append((cb, x, y))

        # Кнопка выбора файла
        self.fileButton = QtWidgets.QPushButton("Выбрать файл")
        self.fileButton.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                font-size: 14px;
                padding: 8px 16px;
                border-radius: 6px;
                margin-top: 15px;
            }
        """)
        self.fileButton.clicked.connect(self.choose_file)
        self.verticalLayout.addWidget(self.fileButton)

        # Отображение пути
        self.filePathField = QtWidgets.QLineEdit()
        self.filePathField.setReadOnly(True)
        self.filePathField.setPlaceholderText("Файл не выбран")
        self.filePathField.setStyleSheet("font-size: 14px; padding: 6px; margin-bottom: 10px;")
        self.verticalLayout.addWidget(self.filePathField)

        # Кнопка продолжить
        self.continueButton = QtWidgets.QPushButton("Продолжить")
        self.continueButton.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                font-size: 18px;
                padding: 10px 20px;
                border-radius: 8px;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #004a99;
            }
        """)
        self.continueButton.clicked.connect(self.generate_charts_and_open)
        self.verticalLayout.addWidget(self.continueButton)

        MainWindow.setCentralWidget(self.centralwidget)

    def choose_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Выберите файл", os.getcwd(), "TXT (*.txt);;Все файлы (*)"
        )
        if file_path:
            self.filePathField.setText(file_path)

    def generate_charts_and_open(self):
        selected = []
        for checkbox, x, y in self.checkboxes:
            if checkbox.isChecked():
                selected.append((x, y))

        file_path = self.filePathField.text()
        if not file_path:
            QtWidgets.QMessageBox.warning(None, "Нет файла", "Сначала выберите файл.")
            return

        if not selected:
            QtWidgets.QMessageBox.warning(None, "Нет выбора", "Выберите хотя бы одну зависимость.")
            return

        self.continueButton.setText("Генерируем...")
        QtWidgets.QApplication.processEvents()

        # 👉 Генерация графиков (Figure объекты)
        figures = self.generate_charts(file_path, selected)

        # 👉 Передаём их напрямую в окно для отображения
        self.open_graphs_window(file_path, figures)

        self.continueButton.setText("Продолжить")

    def generate_charts(self, file_path: str, selected: list) -> list:
        figures = []

        for x, y in selected:
            plot = TGA.plot_graph(file_path, x, y)
            fig = plot.gcf()
            figures.append(fig)

            plot.close(fig)

        return figures

    def open_graphs_window(self, file_path, charts):
        self.graphWindow = QtWidgets.QMainWindow()
        self.graphUI = Ui_GraphsWindow()
        self.graphUI.setupUi(self.graphWindow, charts)
        self.graphWindow.setWindowTitle(f"Графики по: {os.path.basename(file_path)}")
        self.graphWindow.show()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_DependencySelectorWithFile()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

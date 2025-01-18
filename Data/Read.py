import json
import os
import numpy as np
import pyvista as pv
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
from pyvistaqt import QtInteractor

from Data.DataHadler import DataHandler
from Data.ReactorSimulation import ReactorSimulation


class MainWindow(QMainWindow):
    def __init__(self, data_handler):
        super().__init__()
        self.setWindowTitle("Temperature Visualization")
        self.setGeometry(100, 100, 850, 750)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Макет
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # PyVista интерактор
        self.plotter = QtInteractor(central_widget)
        layout.addWidget(self.plotter)

        # Инициализация симуляции
        self.simulation = ReactorSimulation(data_handler)

        # Добавляем меши в сцену
        self.plotter.add_mesh(self.simulation.merged_polydata, scalars="c_values", cmap="coolwarm", point_size=10,
                              render_points_as_spheres=True, name="c_m")

        # Таймер для обновления
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_temperature)
        self.timer.start(100)

    def update_temperature(self):
        if not self.simulation.update_temperature():
            self.timer.stop()
            print("End of simulation.")
            return

        # Обновляем визуализацию
        self.plotter.update_scalars(self.simulation.merged_polydata["c_values"], render=True)


if __name__ == "__main__":
    # Пути к папкам и файлам
    OUTPUT_FOLDER_JSON = "calculated_models/model_1"
    OUTPUT_FOLDER = "calculated_models/model_1/output_data"
    PARAMETERS_FILE = os.path.join(OUTPUT_FOLDER_JSON, "model_parameters.json")

    # Создаем объект DataHandler
    data_handler = DataHandler(output_folder=OUTPUT_FOLDER, parameters_file=PARAMETERS_FILE)

    app = QApplication([])
    window = MainWindow(data_handler)
    window.show()
    app.exec_()

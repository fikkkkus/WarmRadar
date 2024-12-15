import sys
import json  # Для удобного хранения параметров в JSON формате
from dataclasses import dataclass

import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
from qtpy import QtCore

from funcs import update_central_temperature
import os

@dataclass
class Syrio:
    name: str
    percentage: float
    density: float
    color: QtCore.Qt.GlobalColor

current_dir = os.path.dirname(__file__)
OUTPUT_FOLDER_JSON = os.path.join(current_dir, "../Data/model_1")
OUTPUT_FOLDER = os.path.join(current_dir, "../Data/model_1/output_data")
#PARAMETERS_FILE = os.path.join(OUTPUT_FOLDER_JSON, "model_parameters.json")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)  # Создаёт папку, если её нет

def save_model_parameters(filename, parameters):
    """Сохраняет параметры модели в файл."""
    with open(filename, "w") as file:
        json.dump(parameters, file, indent=4)
    print(f"Model parameters saved to {filename}")

def save_temperature_to_file(step, temperature_data, file_prefix="temperature_step"):
    """Сохраняет температуру на текущем шаге в файл."""
    filename = os.path.join(OUTPUT_FOLDER, f"{file_prefix}_{step}.npy")
    np.save(filename, temperature_data)
    #print(f"Saved step {step} to {filename}")

def interpolate_temperature(schedule, current_step):
    """Интерполирует температуру на текущем шаге на основе расписания."""
    for i in range(len(schedule) - 1):
        step_start, temp_start = schedule[i]
        step_end, temp_end = schedule[i + 1]
        if step_start <= current_step <= step_end:
            # Линейная интерполяция
            return temp_start + (temp_end - temp_start) * (current_step - step_start) / (step_end - step_start)
    return schedule[-1][1]  # Если шаг больше последнего указанного, вернуть последнюю температуру

def calculate_a_distribution(layers, Z, Nz):
    """
    Вычисляет распределение теплопроводности a(z) вдоль высоты цилиндра.

    :param layers: Список слоев и сырья в формате [('layer', ...), ('item', ...)].
    :param Z: Высота цилиндра.
    :param Nz: Количество узлов по оси Z.
    :return: Массив a(z) длиной Nz.
    """
    a_distribution = np.zeros(Nz)
    dz = Z / (Nz - 1)

    for i in range(len(layers)):
        if layers[i][0] == 'item':
            current_item = layers[i][3]  # Syrio объект
            density = current_item.density

            # Находим границы слоя
            z_start = layers[i - 1][1] if i > 0 and layers[i - 1][0] == 'layer' else 0.0
            z_end = layers[i + 1][1] if i + 1 < len(layers) and layers[i + 1][0] == 'layer' else Z

            # Определяем индексы для z_start и z_end
            start_index = int(z_start / dz)
            end_index = int(z_end / dz)

            # Рассчитываем теплопроводность (пример: a пропорционален плотности)
            a_value = 0.01 * density  # Здесь коэффициент пропорциональности

            # Заполняем массив a для данного слоя
            a_distribution[start_index:end_index + 1] = a_value

    print(a_distribution)
    return a_distribution


class Simulation:
    def __init__(self, Controller):
        # Параметры цилиндра
        self.R, self.Z, self.PHI = Controller.radius, Controller.height, 2 * np.pi
        self.Nr, self.Nz, self.Nphi = Controller.grid_size[0], Controller.grid_size[1], Controller.grid_size[2]
        self.dr, self.dz, self.dphi = self.R / (self.Nr - 1), self.Z / (self.Nz - 1), self.PHI / self.Nphi

        # Флаг и координаты точки подвода тепла
        self.heat_point_coordinates = Controller.heat_source
        self.heat_point_enabled = self.heat_point_coordinates is not None
        self.heat_point_coordinates_json = tuple(x.item() for x in self.heat_point_coordinates) if self.heat_point_enabled else None

        # Расписание температуры
        self.heat_schedule = Controller.heat_function

        # Структура слоев сырья
        self.layers = Controller.items_and_layers
        self.a_distribution = calculate_a_distribution(self.layers, self.Z, self.Nz)

        # Переменные для расчетов
        self.T = np.zeros((self.Nr - 1, self.Nphi, self.Nz))
        self.T_center = np.zeros(self.Nz)
        self.dt = Controller.time_delta
        self.a = 0.01
        self.epsilon = 1e-6
        self.current_step = 1
        self.max_steps = Controller.time_steps

        # Интерполяция начальной температуры
        interpolated_temperature = interpolate_temperature(self.heat_schedule, self.current_step)
        if self.heat_point_enabled:
            self.T[self.heat_point_coordinates] = interpolated_temperature
        else:
            self.T[-1, :, :] = interpolated_temperature

        # Сохранение параметров модели
        model_parameters = {
            "Cylinder": {"Radius": self.R, "Height": self.Z, "Phi": self.PHI},
            "Grid": {"Nr": self.Nr, "Nz": self.Nz, "Nphi": self.Nphi},
            "Step_Size": {"dr": self.dr, "dz": self.dz, "dphi": self.dphi},
            "Simulation": {"Max_Steps": self.max_steps, "dt": self.dt, "a": self.a},
            "Heat_Point": {
                "Enabled": self.heat_point_enabled,
                "Coordinates": self.heat_point_coordinates_json,
                "Schedule": self.heat_schedule
            },
        }
        print("Параметры сохранены")
        save_model_parameters(os.path.join(OUTPUT_FOLDER_JSON, "model_parameters.json"), model_parameters)


    def calculate(self):
        while self.current_step <= self.max_steps:
            self.update_temperature()
        print("Достигнуто максимальное количество шагов.")
    def update_temperature(self):
        # Создаем копии текущих температур
        T_new = np.copy(self.T)
        T_center_new = np.copy(self.T_center)

        # Обновляем центральную температуру
        for k in range(1, self.Nz - 1):
            T_center_new[k] = update_central_temperature(self.T_center, self.T, k, self.epsilon)

        # Основной расчет температуры
        for i in range(1, self.Nr - 2):
            for j in range(self.Nphi):
                for k in range(1, self.Nz - 1):
                    r_i = i * self.dr
                    T_new[i, j, k] = self.T[i, j, k] + self.a_distribution[k] * self.dt * (
                            (self.T[i + 1, j, k] - 2 * self.T[i, j, k] + self.T[i - 1, j, k]) / self.dr ** 2 +
                            (self.T[i + 1, j, k] - self.T[i - 1, j, k]) / (r_i * self.dr) +
                            (self.T[i, (j + 1) % self.Nphi, k] - 2 * self.T[i, j, k] +
                             self.T[i, (j - 1) % self.Nphi, k]) / (self.dphi ** 2 * (i * self.dr) ** 2) +
                            (self.T[i, j, k + 1] - 2 * self.T[i, j, k] + self.T[i, j, k - 1]) / self.dz ** 2
                    )

        # Расчет температуры для первого радиального слоя
        for j in range(self.Nphi):
            for k in range(1, self.Nz - 1):
                r_i = self.dr
                T_new[0, j, k] = self.T[0, j, k] + self.a_distribution[k] * self.dt * (
                        (self.T[1, j, k] - 2 * self.T[0, j, k] + self.T_center[k]) / self.dr ** 2 +
                        (self.T[1, j, k] - self.T_center[k]) / (r_i * self.dr) +
                        (self.T[0, (j + 1) % self.Nphi, k] - 2 * self.T[0, j, k] +
                         self.T[0, (j - 1) % self.Nphi, k]) / (self.dphi ** 2 * (1.5 * self.dr) ** 2) +
                        (self.T[0, j, k + 1] - 2 * self.T[0, j, k] + self.T[0, j, k - 1]) / self.dz ** 2
                )

        # Применение граничных условий
        T_new[:, :, 0] = T_new[:, :, 1]
        T_new[:, :, -1] = T_new[:, :, -2]

        # Применение точки подвода тепла с интерполяцией температуры
        interpolated_temperature = interpolate_temperature(self.heat_schedule, self.current_step)
        if self.heat_point_enabled:
            T_new[self.heat_point_coordinates] = interpolated_temperature
        else:
            T_new[-1, :, :] = interpolated_temperature

        # Обновляем значения self.T и self.T_center
        self.T = T_new
        self.T_center = T_center_new

        # Сохранение температуры
        save_temperature_to_file(step=self.current_step, temperature_data=self.T)
        self.current_step += 1
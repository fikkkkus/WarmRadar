import sys
import random
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
from scipy.interpolate import griddata

from funcs import update_central_temperature, get_cylinder_surface_points, get_valid_cylinder_surface_points, \
    slice_plane_with_tolerance
from scipy.spatial import Delaunay

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Visualization with Changing Colors")
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

        # Параметры цилиндра
        R, Z, PHI = 1, 2, 2 * np.pi
        Nr, Nz, Nphi = 30, 20, 40
        dr, dz, dphi = R / (Nr - 1), Z / (Nz - 1), PHI / Nphi

        r = np.linspace(dr, R, Nr - 1)
        z = np.linspace(0, Z, Nz)
        phi = np.linspace(0, PHI, Nphi, endpoint=False)

        # Сетка
        R_grid, PHI_grid, Z_grid = np.meshgrid(r, phi, z, indexing="ij")
        X = R_grid * np.cos(PHI_grid)
        Y = R_grid * np.sin(PHI_grid)
        points = np.column_stack((X.ravel(), Y.ravel(), Z_grid.ravel()))
        self.grid = pv.PolyData(points)

        # Инициализация данных
        self.grid["c_values"] = np.zeros((Nr - 1, Nphi, Nz)).ravel()
        # Создаем индексы для всех точек
        indices = np.arange(len(self.grid.points))
        self.grid["indices"] = indices
        # Добавляем индексы как атрибут в grid

        # Переменные для расчетов
        self.T = np.zeros((Nr - 1, Nphi, Nz))
        self.T[-1, :, :] = 600
        self.T_center = np.zeros(Nz)
        self.dt = 0.01
        self.a = 0.01
        self.dr, self.dz, self.dphi = dr, dz, dphi
        self.epsilon = 1e-6
        self.Nr, self.Nphi, self.Nz = Nr, Nphi, Nz

        # Создание цилиндра для отображения поверхности
        self.cylinder = pv.Cylinder(radius=R, height=Z, resolution=50, center=(0, 0, Z / 2), direction=(0, 0, 1))

        # Произвольный наклонный срез
        normal = [0, 0, 1]  # Нормаль, произвольная комбинация
        origin = [0, 0, Z / 2]  # Точка на плоскости
        tolerance = 0.07  # Погрешность для среза
        slice_grid_plane = slice_plane_with_tolerance(self.grid, normal, origin, tolerance)
        # Получаем точки на боковой поверхности цилиндра и основаниях
        cylinder_surface_points_grid = get_cylinder_surface_points(self.grid, R, Z)
        # Применяем срез и фильтруем точки, которые лежат в пределах среза
        valid_cylinder_surface_points = get_valid_cylinder_surface_points(cylinder_surface_points_grid, normal, origin)

        self.merged_polydata = valid_cylinder_surface_points.merge(slice_grid_plane)
        self.sliced_cylinder = self.cylinder.clip(normal=normal, origin=origin)

        # Цилиндр с заполненной дырой
        filled_cylinder = self.sliced_cylinder.fill_holes(1000)

        self.plotter.add_mesh(slice_grid_plane, color="red", opacity=0.8)  # Убираем эту строку

        num_points = slice_grid_plane.n_points  # Количество точек в slice_grid_plane

        # Создаём линейный градиент от 0 до 100
        c_values_gradient = np.linspace(0, 100, num_points)  # Линейные значения от 0 до 100

        # Добавляем эти значения как скалярное поле "c_values"
        slice_grid_plane["c_values"] = c_values_gradient

        # Направление нормали
        normal = np.array(normal)

        normal = normal / np.linalg.norm(normal)  # Нормируем вектор нормали

        # Фиксированное расстояние от камеры до origin
        fixed_distance = 4  # Например, 5 единиц

        # Позиция камеры, находящейся на расстоянии fixed_distance от origin вдоль нормали
        camera_position = np.array(origin) + fixed_distance * normal

        up_vector = np.array([0, 1, 0]) if np.allclose(normal, [0, 0, 1]) else [0, 0, 1]

        # Установка камеры
        self.plotter.camera_position = [
            camera_position.tolist(),  # Позиция камеры
            origin,  # Фокус камеры (куда она смотрит)
            up_vector
        ]

        # Настройка угла обзора (если требуется фиксировать видимый масштаб)
        self.plotter.camera.view_angle = 30  # Например, 30 градусов

        # Добавляем цилиндр в сцену
        self.plotter.add_mesh(filled_cylinder, color="gray", opacity=0.9)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
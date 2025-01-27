import os

import numpy as np
import pyvista as pv
from pyvista.plotting.opts import ElementType


class ReactorSimulation:
    def __init__(self, data_handler):
        self.data_handler = data_handler
        # Загружаем параметры модели
        self.parameters = self.data_handler.load_parameters()

        # Извлекаем параметры
        cylinder_params = self.parameters["Cylinder"]
        grid_params = self.parameters["Grid"]
        step_params = self.parameters["Step_Size"]

        R, Z, PHI = cylinder_params["Radius"], cylinder_params["Height"], cylinder_params["Phi"]
        Nr, Nz, Nphi = grid_params["Nr"], grid_params["Nz"], grid_params["Nphi"]
        dr, dz, dphi = step_params["dr"], step_params["dz"], step_params["dphi"]

        # Загружаем файлы с температурой
        self.temperature_files = self.data_handler.load_temperature_files()

        # Инициализация переменных для симуляции
        self.R, self.Z, self.PHI = R, Z, PHI
        self.Nr, self.Nz, self.Nphi = Nr, Nz, Nphi
        self.dr, self.dz, self.dphi = dr, dz, dphi
        self.temperature_data = np.zeros((Nr - 1, Nphi, Nz))
        self.current_step = 0
        self.max_steps = len(self.temperature_files)

        # Создаем сетку
        r = np.linspace(dr, R, Nr - 1)
        z = np.linspace(0, Z, Nz)
        phi = np.linspace(0, PHI, Nphi, endpoint=False)
        R_grid, PHI_grid, Z_grid = np.meshgrid(r, phi, z, indexing="ij")

        X = R_grid * np.cos(PHI_grid)
        Y = R_grid * np.sin(PHI_grid)
        points = np.column_stack((X.ravel(), Y.ravel(), Z_grid.ravel()))
        self.grid = pv.PolyData(points)

        # Добавляем атрибуты
        self.grid["c_values"] = np.zeros_like(self.grid.points[:, 0])
        indices = np.arange(len(self.grid.points))
        self.grid["indices"] = indices
        self.grid["R"] = R_grid.ravel()
        self.grid["Phi"] = PHI_grid.ravel()
        self.grid["Z"] = Z_grid.ravel()

        # Создание цилиндра для отображения поверхности
        self.cylinder = pv.Cylinder(radius=R, height=Z, resolution=100, center=(0, 0, Z / 2), direction=(0, 0, 1))

        # Получаем точки на боковой поверхности цилиндра и основаниях
        self.cylinder_surface_points_grid = self.get_cylinder_surface_points(self.grid, R, Z)
        # Применяем срез и фильтруем точки, которые лежат в пределах среза

        self.cylinder = self.cylinder.clean()
        self.cylinder = self.cylinder.triangulate()
        self.cylinder = self.cylinder.subdivide(5, subfilter="linear")

        self.interpolated = self.cylinder.interpolate(self.cylinder_surface_points_grid, radius=0.1)
        self.interpolated.set_active_scalars("c_values")

    def get_slice_and_surface_points(self,normal, origin,tolerance = 0.07):
        slice_grid_plane = self.slice_plane_with_tolerance(self.grid, normal, origin, tolerance)
        # Получаем точки на боковой поверхности цилиндра и основаниях
        self.cylinder_surface_points_grid = self.get_cylinder_surface_points(self.grid, self.R, self.Z)
        # Применяем срез и фильтруем точки, которые лежат в пределах среза
        valid_cylinder_surface_points = self.get_valid_cylinder_surface_points(self.cylinder_surface_points_grid, normal,origin)
        self.merged_polydata = valid_cylinder_surface_points.merge(slice_grid_plane)
        return self.merged_polydata

    def get_slice_cylinder(self,normal, origin):
        # Создание цилиндра для отображения поверхности
        cylinder = pv.Cylinder(radius=self.R, height=self.Z, resolution=50, center=(0, 0, self.Z / 2), direction=(0, 0, 1))
        cylinder = cylinder.clip(normal=normal, origin=origin)
        cylinder = cylinder.fill_holes(1000)
        cylinder = cylinder.clean()
        cylinder = cylinder.triangulate()
        cylinder = cylinder.subdivide(3, subfilter="linear")
        return cylinder


    def get_slice(self, normal, origin):
        tolerance = 0.07  # Погрешность для среза
        print(f"Creating slice with normal: {normal}, origin: {origin}, tolerance: {tolerance}")

        slice_grid_plane = self.slice_plane_with_tolerance(self.grid, normal, origin, tolerance)
        print(f"Slice grid plane created. Number of points: {slice_grid_plane.n_points}")

        # Получаем точки на боковой поверхности цилиндра и основаниях
        cylinder_surface_points_grid = self.get_cylinder_surface_points(self.grid, self.R, self.Z)
        print(f"Cylinder surface points grid created. Number of points: {cylinder_surface_points_grid.n_points}")

        # Применяем срез и фильтруем точки, которые лежат в пределах среза
        valid_cylinder_surface_points = self.get_valid_cylinder_surface_points(cylinder_surface_points_grid, normal,
                                                                               origin)
        print(f"Filtered valid cylinder surface points. Number of points: {valid_cylinder_surface_points.n_points}")

        # Интерполяция температуры с точек среза на поверхность среза
        sliced_cylinder = self.cylinder.clip(normal=normal, origin=origin)
        print("Cylinder clipped with the slice.")

        sliced_cylinder = sliced_cylinder.fill_holes(1000)
        print("Holes filled in the sliced cylinder.")

        cleaned_cylinder = sliced_cylinder.clean()
        print("Cylinder cleaned.")

        triangulated_cylinder = cleaned_cylinder.triangulate()
        print("Cylinder triangulated.")

        subdivided_cylinder = triangulated_cylinder.subdivide(3, subfilter="linear")
        print("Cylinder subdivided.")

        # Объединяем полигональные данные
        merged_polydata = valid_cylinder_surface_points.merge(slice_grid_plane)
        print("Merged polydata with the slice grid plane.")

        # Интерполируем значения температуры
        interpolated = subdivided_cylinder.interpolate(merged_polydata, radius=0.1)
        print("Interpolation of temperature values completed.")

        interpolated.set_active_scalars("c_values")
        print("Set active scalars to 'c_values'.")

        return interpolated

    def get_new_grid(self):
        return self.grid

    def update_temperature(self, step,OUTPUT_DATA_FOLDER):


        # Загружаем данные температуры для текущего шага
        path_to_step_file = f"temperature_step_{step}.npy"
        temperature_data = np.load(os.path.join(OUTPUT_DATA_FOLDER, path_to_step_file))
        # Обновляем значения температуры на сетке
        self.grid["c_values"] = temperature_data.ravel()
        self.cylinder_surface_points_grid["c_values"] = self.grid["c_values"][
            self.cylinder_surface_points_grid["indices"]]
        self.interpolated.point_data['c_values'] = \
        self.cylinder.interpolate(self.cylinder_surface_points_grid, radius=0.1)['c_values']
        self.interpolated.set_active_scalars("c_values")

    # Функция для вычисления температуры в центральной точке
    def update_central_temperature(self, T_center, T, k, epsilon):
        # Соседи центральной оси (на первом радиальном слое)
        neighbors = T[0, :, k]

        # Вычисление весов w_m
        grad_diff = np.abs(neighbors - T_center[k]) + epsilon
        std_term = np.std(neighbors) + epsilon
        weights = 1 / (grad_diff * std_term)

        # Нормализация весов
        weights /= np.sum(weights)

        # Обновление температуры в центральной точке
        T_center_new = np.sum(weights * neighbors)
        return T_center_new

    # Функция для получения точек на боковой поверхности цилиндра
    def get_cylinder_surface_points(self, grid, radius, height):
        """Функция для получения точек на боковой поверхности цилиндра, а также на основаниях"""
        # Отбираем точки, которые лежат на боковой поверхности цилиндра (по радиусу)
        mask = np.isclose(grid.points[:, 0] ** 2 + grid.points[:, 1] ** 2, radius ** 2, atol=0.05)

        # Отбираем точки, которые лежат в пределах высоты цилиндра
        mask &= (grid.points[:, 2] >= 0) & (grid.points[:, 2] <= height)

        # Отбираем точки на верхнем и нижнем основаниях цилиндра
        bottom_mask = np.isclose(grid.points[:, 2], 0, atol=0.05)
        top_mask = np.isclose(grid.points[:, 2], height, atol=0.05)

        # Комбинируем маски для боковой поверхности и оснований
        surface_mask = mask | bottom_mask | top_mask

        # Применяем маску для извлечения точек, которые лежат на поверхности
        surface_points = grid.points[surface_mask]

        # Создаем объект PolyData с выбранными точками
        slice_grid = pv.PolyData(surface_points)

        # Добавляем атрибут температуры для этих точек
        slice_grid["c_values"] = grid["c_values"][surface_mask]
        slice_grid["indices"] = grid["indices"][surface_mask]
        slice_grid["R"] = grid["R"][surface_mask]
        slice_grid["Phi"] = grid["Phi"][surface_mask]
        slice_grid["Z"] = grid["Z"][surface_mask]
        return slice_grid

    def get_valid_cylinder_surface_points(self, grid, normal, origin):
        # Нормализуем нормаль
        normal = np.array(normal)
        normal = normal / np.linalg.norm(normal)

        origin = np.array(origin)

        plane_points = grid.points

        # Вектор от точки на плоскости до текущей точки
        # Скалярное произведение нормали и вектора
        dot_product = np.dot(plane_points - origin, normal)
        # Добавляем точку, если она лежит за плоскостью (dot_product > 0)
        valid_points = grid.points[dot_product <= 0]

        valid_points_grid = pv.PolyData(valid_points)
        valid_points_grid["indices"] = grid["indices"][dot_product <= 0]
        valid_points_grid["c_values"] = grid["c_values"][dot_product <= 0]

        return valid_points_grid

    # Функция для наклонного среза с погрешностью
    def slice_plane_with_tolerance(self, grid, normal, origin, tolerance=0.05):
        """Функция для получения среза по наклонённой плоскости с погрешностью"""
        plane_points = grid.points
        distances = np.dot(plane_points - origin, normal)  # Скаларное произведение

        # Фильтруем точки, которые находятся в пределах погрешности
        slice_points = grid.points[np.abs(distances) < tolerance]

        slice_grid = pv.PolyData(slice_points)
        slice_grid["c_values"] = grid["c_values"][np.abs(distances) < tolerance]
        slice_grid["indices"] = grid["indices"][np.abs(distances) < tolerance]
        return slice_grid

    def get_reduced_cylinder_surface_points(self, grid, step_r, step_phi, step_z):
        """
        Уменьшение количества точек на поверхности цилиндра с исключением точек
        по радиусу, углу и высоте, сохраняя минимальные и максимальные значения.

        Параметры:
        - grid: исходная сетка точек с атрибутами R, Phi, Z.
        - step_r: шаг исключения точек по радиусу.
        - step_phi: шаг исключения точек по углу.
        - step_z: шаг исключения точек по высоте.
        """
        # Получаем цилиндрические координаты из атрибутов
        r = grid["R"]
        phi = grid["Phi"]
        z = grid["Z"]

        # Уникальные значения радиуса, угла и высоты
        unique_r = np.unique(r)
        unique_phi = np.unique(phi)
        unique_z = np.unique(z)

        # Удаляем первые 4 минимальных радиуса и оставляем каждую N-ю точку
        reduced_r = unique_r[4::step_r]
        if unique_r[-1] not in reduced_r:
            reduced_r = np.append(reduced_r, unique_r[-1])

        # Убираем больше точек по углу для первого радиуса после минимальных
        reduced_phi = unique_phi[::step_phi]
        # if unique_phi[-1] not in reduced_phi:
        #     reduced_phi = np.append(reduced_phi, unique_phi[-1])

        reduced_z = unique_z[::step_z]
        if unique_z[-1] not in reduced_z:
            reduced_z = np.append(reduced_z, unique_z[-1])

        # Создаём фильтры по радиусу, углу и высоте
        r_filter = np.isin(r, reduced_r)
        phi_filter = np.isin(phi, reduced_phi)
        z_filter = np.isin(z, reduced_z)

        # Применяем фильтры для первых 4 минимальных радиусов
        for i in range(4):
            r_min = unique_r[i]
            r_filter &= ~(r == r_min)

        # Применяем комбинированный фильтр
        final_mask = r_filter & phi_filter & z_filter
        # Создаём объект PolyData с уменьшенной выборкой точек
        reduced_points = grid.points[final_mask]
        slice_grid = pv.PolyData(reduced_points)

        # Добавляем атрибуты температуры и индексов
        slice_grid["c_values"] = grid["c_values"][final_mask]
        slice_grid["indices"] = grid["indices"][final_mask]

        return slice_grid

    def plotter_to_qimage(self, plotter):
        """
        Функция, принимающая PyVista plotter и возвращающая QImage на основе скриншота.

        :param plotter: Объект PyVista plotter
        :return: Объект QImage
        """
        # Получение скриншота как объекта numpy array
        screenshot_array = plotter.screenshot(return_img=True)

        # Если скриншот в диапазоне от 0 до 1, умножаем на 255, чтобы привести к 8-битному диапазону
        screenshot_array = (screenshot_array * 255).astype(
            np.uint8) if screenshot_array.max() <= 1 else screenshot_array

        # Извлекаем размеры изображения
        height, width, channels = screenshot_array.shape

        # Количество байт на строку
        bytes_per_line = channels * width

        # Убедимся, что массив данных является непрерывным (для QImage)
        screenshot_array = np.ascontiguousarray(screenshot_array[:, :, :3])  # Берем только RGB, без альфа-канала

        # Преобразуем numpy массив в QImage
        qimage = [screenshot_array.data, width, height, bytes_per_line]

        return qimage

    import numpy as np

    def rotate_slice_to_camera(self, plotter, points_for_slice):
        """
        Поворачивает камеру так, чтобы срез был виден лицом к пользователю.
        Учитывает центр цилиндра для более точного расположения камеры.

        points_for_slice: list из 3 точек (np.ndarray или список)
        center_cylinder: координаты центра цилиндра [x, y, z]
        """

        # Центр цилиндра (предположим, что центр цилиндра известен)
        center_cylinder = [0, 0, self.Z / 2]

        # Убедимся, что точки заданы правильно
        points = np.array(points_for_slice)
        if points.shape != (3, 3):
            raise ValueError("points_for_slice должен содержать ровно три точки в формате (3, 3).")

        # Геометрический центр среза (усреднение координат точек среза)
        mean_points = np.mean(points, axis=0)

        # Вычисление вектора сдвига от центра среза к центру цилиндра
        shift_vector = np.array(center_cylinder) - mean_points

        # Сдвигаем все точки среза в центр цилиндра
        shifted_points = points + shift_vector

        # Векторы, определяющие плоскость среза
        v1 = shifted_points[1] - shifted_points[0]
        v2 = shifted_points[2] - shifted_points[0]

        # Нормаль к плоскости
        normal = np.cross(v1, v2)
        normal = normal / np.linalg.norm(normal)

        # Геометрический центр среза после сдвига
        center_slice = np.mean(shifted_points, axis=0)

        # Камера на фиксированном расстоянии вдоль нормали
        fixed_distance = 10
        camera_position = center_slice + fixed_distance * normal

        # Вектор "вверх" (по умолчанию ось Y или Z, если нормаль к плоскости близка к оси Z)
        up_vector = np.array([0, 1, 0]) if np.allclose(normal, [0, 0, 1], atol=1e-3) else [0, 0, 1]

        # Устанавливаем положение камеры
        plotter.camera_position = [
            camera_position.tolist(),  # Позиция камеры
            center_slice.tolist(),  # Точка, на которую камера смотрит
            up_vector  # Вектор "вверх"
        ]

        # Опционально: настройка угла обзора
        #plotter.camera.view_angle = 30  # Угол обзора, например, 30 градусов


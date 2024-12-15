import numpy as np
import pyvista as pv
# Функция для вычисления температуры в центральной точке
def update_central_temperature(T_center, T, k, epsilon):
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
def get_cylinder_surface_points(grid, radius, height):
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

    return slice_grid

def get_valid_cylinder_surface_points(grid, normal, origin):
    # Нормализуем нормаль
    normal = np.array(normal)
    normal = normal / np.linalg.norm(normal)

    origin = np.array(origin)



    plane_points = grid.points

    # Вектор от точки на плоскости до текущей точки
    # Скалярное произведение нормали и вектора
    dot_product = np.dot(plane_points - origin,normal )
    # Добавляем точку, если она лежит за плоскостью (dot_product > 0)
    valid_points=grid.points[dot_product <= 0]


    valid_points_grid = pv.PolyData(valid_points)
    valid_points_grid["indices"] = grid["indices"][dot_product<=0]
    valid_points_grid["c_values"] = grid["c_values"][dot_product<=0]

    return valid_points_grid

# Функция для наклонного среза с погрешностью
def slice_plane_with_tolerance(grid, normal, origin, tolerance=0.05):
    """Функция для получения среза по наклонённой плоскости с погрешностью"""
    plane_points = grid.points
    distances = np.dot(plane_points - origin, normal)  # Скаларное произведение

    # Фильтруем точки, которые находятся в пределах погрешности
    slice_points = grid.points[np.abs(distances) < tolerance]


    slice_grid = pv.PolyData(slice_points)
    slice_grid["c_values"] = grid["c_values"][np.abs(distances) < tolerance]
    slice_grid["indices"] = grid["indices"][np.abs(distances) < tolerance]
    return slice_grid

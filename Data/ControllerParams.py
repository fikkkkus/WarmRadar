
class ControllerParams:
    def __init__(self):
        # Инициализация параметров
        self.height = 0.0  # Высота реактора
        self.radius = 0.0   # Радиус реактора
        self.items_and_layers = None  # Пример слоев сырья
        self.thermal_diffusivity = 0.0 # Температуропроводность
        self.time_delta = 0.0  # Время моделирования (сек)
        self.time_steps = 0  # Кол-во шагов моделирования
        self.heat_function = None  # Функция нагрева
        self.heat_source = None  # Точка подвода тепла (r, z, φ)
        self.grid_size = (0.0, 0.0, 0.0)  # Размер сетки (r, z, φ)
